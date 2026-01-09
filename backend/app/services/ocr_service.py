"""OCR Service using OCR.Space API with handwriting support"""

import requests
import io
import logging
import os
import sys
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
from typing import Tuple, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import Config
from app.logger import log_stage_start, log_stage_complete, log_progress, log_stage_error

logger = logging.getLogger(__name__)

class OCRService:
    """Service for extracting text from PDFs using OCR.Space API"""
    
    def __init__(self):
        self.api_key = Config.get_ocr_api_key()
        self.base_url = Config.get('ocr.base_url')
        self.timeout = Config.get('ocr.timeout', 30)
        self.engine = Config.get('ocr.engine', 2)
        self.language = Config.get('ocr.language', 'eng')
        self.max_size_kb = Config.get('ocr.max_image_size_kb', 900)
        self.max_workers = Config.get('ocr.max_workers', 3)
        
        if not self.api_key:
            raise ValueError("OCR_API_KEY not found in environment variables")
        
        logger.info(f"OCR Service initialized with engine {self.engine}")
        logger.info("Using PyMuPDF for PDF to image conversion (no poppler required)")
    
    def compress_image(self, image: Image.Image, max_size_kb: int = None) -> bytes:
        """
        Compress image to stay under max_size_kb
        
        Args:
            image: PIL Image object
            max_size_kb: Maximum size in KB (default from config)
        
        Returns:
            Compressed image bytes
        """
        if max_size_kb is None:
            max_size_kb = self.max_size_kb
        
        quality = 95
        while quality > 20:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
            img_byte_arr.seek(0)
            size_kb = len(img_byte_arr.getvalue()) / 1024
            
            if size_kb <= max_size_kb:
                logger.debug(f"Image compressed to {size_kb:.2f}KB at quality {quality}")
                return img_byte_arr.getvalue()
            
            quality -= 10
        
        # If still too large, resize the image
        img_byte_arr = io.BytesIO()
        width, height = image.size
        new_size = (int(width * 0.7), int(height * 0.7))
        image = image.resize(new_size, Image.LANCZOS)
        image.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
        img_byte_arr.seek(0)
        
        final_size = len(img_byte_arr.getvalue()) / 1024
        logger.debug(f"Image resized and compressed to {final_size:.2f}KB")
        
        return img_byte_arr.getvalue()
    
    def ocr_image(self, image_bytes: bytes, page_num: int) -> Tuple[int, Optional[str], Optional[str]]:
        """
        Perform OCR on a single image using OCR.Space API
        
        Args:
            image_bytes: Image data in bytes
            page_num: Page number for tracking
        
        Returns:
            Tuple of (page_num, extracted_text, error_message)
        """
        payload = {
            "apikey": self.api_key.strip(),
            "language": self.language,
            "isOverlayRequired": False,
            "OCREngine": self.engine,
            "isTable": True
        }
        
        try:
            logger.debug(f"Processing page {page_num} with OCR.Space API")
            
            response = requests.post(
                self.base_url,
                files={"file": ("image.jpg", image_bytes, "image/jpeg")},
                data=payload,
                timeout=self.timeout
            )
            
            result = response.json()
            
            if result.get("IsErroredOnProcessing"):
                error_msg = result.get("ErrorMessage", ["Unknown error"])
                error_str = error_msg[0] if isinstance(error_msg, list) else str(error_msg)
                logger.error(f"OCR error on page {page_num}: {error_str}")
                return (page_num, None, error_str)
            
            if "ParsedResults" in result and len(result["ParsedResults"]) > 0:
                text = result["ParsedResults"][0].get("ParsedText", "")
                logger.info(f"Successfully extracted {len(text)} characters from page {page_num}")
                return (page_num, text, None)
            
            logger.warning(f"No text found on page {page_num}")
            return (page_num, "", None)
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while processing page {page_num}")
            return (page_num, None, "Request timeout")
        except Exception as e:
            logger.error(f"Error processing page {page_num}: {str(e)}")
            return (page_num, None, str(e))
    
    async def extract_text_from_pdf(self, pdf_path: str, job_id: str = "N/A", doc_name: str = "document") -> Tuple[str, List[str]]:
        """
        Extract text from PDF by converting to images and processing page by page
        
        Args:
            pdf_path: Path to the PDF file
            job_id: Job identifier for logging
            doc_name: Document name for logging (question_paper, answer_key, student_answers)
        
        Returns:
            Tuple of (extracted_text, list_of_errors)
        """
        log_progress(job_id, "OCR", f"Starting OCR for {doc_name}")
        logger.info(f"Starting PDF text extraction: {pdf_path}")
        
        try:
            # Open PDF with PyMuPDF
            dpi = Config.get('pdf_processing.dpi', 200)
            logger.info(f"Converting PDF to images (DPI: {dpi}) using PyMuPDF")
            
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)
            
            log_progress(job_id, "OCR", f"{doc_name}: {total_pages} pages to process")
            logger.info(f"PDF has {total_pages} pages")
            
            # Convert pages to images and compress
            compressed_images = []
            zoom = dpi / 72.0  # PyMuPDF zoom factor (72 DPI is default)
            matrix = fitz.Matrix(zoom, zoom)
            
            for page_num in range(total_pages):
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=matrix)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Compress
                image_bytes = self.compress_image(img)
                compressed_images.append((page_num + 1, image_bytes))
            
            pdf_document.close()
            logger.info(f"Compressed {len(compressed_images)} pages")
            
            # Process pages in parallel
            extracted_text = ""
            errors = []
            results = [None] * total_pages
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all pages for processing
                future_to_page = {
                    executor.submit(self.ocr_image, img_bytes, page_num): page_num
                    for page_num, img_bytes in compressed_images
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_page):
                    page_num, page_text, error = future.result()
                    results[page_num - 1] = (page_text, error)
                    
                    if error:
                        errors.append(f"Page {page_num}: {error}")
            
            # Compile results in page order
            for idx, (page_text, error) in enumerate(results):
                if page_text is not None and page_text.strip():
                    extracted_text += f"{'='*60}\n"
                    extracted_text += f"PAGE {idx + 1}\n"
                    extracted_text += f"{'='*60}\n\n"
                    extracted_text += page_text.strip() + "\n\n"
            
            if not extracted_text or extracted_text.strip() == "":
                logger.warning("No text extracted from PDF")
                log_stage_error(job_id, "OCR", f"{doc_name}: No text found")
                return "", errors if errors else ["No text found in the PDF"]
            
            log_progress(job_id, "OCR", f"{doc_name}: ✓ Extracted {len(extracted_text)} characters")
            logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
            return extracted_text.strip(), errors
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            log_stage_error(job_id, "OCR", f"{doc_name}: {str(e)}")
            return "", [f"PDF extraction failed: {str(e)}"]
    
    def extract_text_from_pdf_sync(self, pdf_path: str) -> Tuple[str, List[str]]:
        """
        Synchronous version of extract_text_from_pdf
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Tuple of (extracted_text, list_of_errors)
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.extract_text_from_pdf(pdf_path))
