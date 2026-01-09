"""
Comprehensive tests for OCR Service
Tests with advanced DSA optimizations
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from tests.test_framework import test, test_runner, memoize_test, time_test

# Import service to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ocr_service import OCRService


class TestOCRService:
    """Test suite for OCR Service with DSA optimizations"""
    
    @pytest.fixture
    def ocr_service(self):
        """Create OCR service instance"""
        with patch('app.services.ocr_service.Config') as mock_config:
            mock_config.get_ocr_api_key.return_value = "test_key"
            mock_config.get.side_effect = lambda key, default=None: {
                'ocr.base_url': 'https://api.ocr.space/parse/image',
                'ocr.timeout': 30,
                'ocr.engine': 2,
                'ocr.language': 'eng',
                'ocr.max_image_size_kb': 900,
                'ocr.max_workers': 3,
                'pdf_processing.dpi': 200,
                'pdf_processing.format': 'jpeg'
            }.get(key, default)
            
            return OCRService()
    
    @time_test
    def test_ocr_initialization(self, ocr_service):
        """Test OCR service initialization"""
        assert ocr_service is not None
        assert ocr_service.api_key == "test_key"
        assert ocr_service.max_workers == 3
        assert ocr_service.engine == 2
    
    @time_test
    def test_image_compression(self, ocr_service):
        """Test image compression with various sizes"""
        from PIL import Image
        import io
        
        # Create test image
        img = Image.new('RGB', (800, 600), color='red')
        
        # Compress
        compressed = ocr_service.compress_image(img, max_size_kb=100)
        
        # Verify size
        size_kb = len(compressed) / 1024
        assert size_kb <= 100, f"Image size {size_kb}KB exceeds limit"
        assert size_kb > 0, "Compressed image is empty"
    
    @time_test
    @patch('requests.post')
    def test_ocr_api_call_success(self, mock_post, ocr_service):
        """Test successful OCR API call"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "IsErroredOnProcessing": False,
            "ParsedResults": [{
                "ParsedText": "Sample extracted text"
            }]
        }
        mock_post.return_value = mock_response
        
        # Test
        page_num, text, error = ocr_service.ocr_image(b"fake_image_data", 1)
        
        assert page_num == 1
        assert text == "Sample extracted text"
        assert error is None
    
    @time_test
    @patch('requests.post')
    def test_ocr_api_call_error(self, mock_post, ocr_service):
        """Test OCR API error handling"""
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "IsErroredOnProcessing": True,
            "ErrorMessage": ["API Error"]
        }
        mock_post.return_value = mock_response
        
        # Test
        page_num, text, error = ocr_service.ocr_image(b"fake_image_data", 1)
        
        assert page_num == 1
        assert text is None
        assert error == "API Error"
    
    @time_test
    @patch('requests.post')
    def test_ocr_timeout_handling(self, mock_post, ocr_service):
        """Test OCR timeout handling"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        page_num, text, error = ocr_service.ocr_image(b"fake_image_data", 1)
        
        assert page_num == 1
        assert text is None
        assert "timeout" in error.lower()
    
    @time_test
    def test_compression_quality_degradation(self, ocr_service):
        """Test that compression reduces quality appropriately"""
        from PIL import Image
        
        # Create large image
        img = Image.new('RGB', (2000, 2000), color='blue')
        
        # Compress with tight limit
        compressed = ocr_service.compress_image(img, max_size_kb=50)
        
        # Verify it's within limits
        size_kb = len(compressed) / 1024
        assert size_kb <= 50
    
    @pytest.mark.asyncio
    @time_test
    @patch('pdf2image.convert_from_path')
    @patch.object(OCRService, 'ocr_image')
    async def test_pdf_extraction_success(self, mock_ocr, mock_convert, ocr_service, temp_dir):
        """Test successful PDF text extraction"""
        from PIL import Image
        
        # Mock PDF conversion
        mock_convert.return_value = [
            Image.new('RGB', (100, 100), color='white'),
            Image.new('RGB', (100, 100), color='white')
        ]
        
        # Mock OCR results
        mock_ocr.side_effect = [
            (1, "Page 1 text", None),
            (2, "Page 2 text", None)
        ]
        
        # Create dummy PDF
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")
        
        # Test
        text, errors = await ocr_service.extract_text_from_pdf(str(pdf_path))
        
        assert "Page 1 text" in text
        assert "Page 2 text" in text
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    @time_test
    @patch('pdf2image.convert_from_path')
    async def test_pdf_extraction_with_errors(self, mock_convert, ocr_service, temp_dir):
        """Test PDF extraction with OCR errors"""
        from PIL import Image
        
        # Mock PDF conversion to fail
        mock_convert.side_effect = Exception("PDF conversion failed")
        
        # Create dummy PDF
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")
        
        # Test
        text, errors = await ocr_service.extract_text_from_pdf(str(pdf_path))
        
        assert text == ""
        assert len(errors) > 0
        assert "PDF extraction failed" in errors[0]


# Register tests with advanced framework
@test("ocr_initialization", priority=10, category="ocr")
def test_ocr_init():
    """Test OCR initialization through framework"""
    print("  Testing OCR initialization...")
    with patch('app.services.ocr_service.Config') as mock_config:
        mock_config.get_ocr_api_key.return_value = "test_key"
        mock_config.get.return_value = 30
        service = OCRService()
        assert service.api_key == "test_key"
    return True


@test("ocr_compression", priority=9, dependencies=["ocr_initialization"], category="ocr")
def test_ocr_compression():
    """Test image compression through framework"""
    print("  Testing image compression...")
    from PIL import Image
    
    with patch('app.services.ocr_service.Config') as mock_config:
        mock_config.get_ocr_api_key.return_value = "test_key"
        mock_config.get.return_value = 900
        service = OCRService()
        
        img = Image.new('RGB', (500, 500), color='red')
        compressed = service.compress_image(img, max_size_kb=100)
        
        size_kb = len(compressed) / 1024
        assert size_kb <= 100
    
    return True


if __name__ == "__main__":
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
