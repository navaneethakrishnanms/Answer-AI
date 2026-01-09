"""
Central logging configuration for AI Exam Evaluator pipeline
Provides structured logging with job_id tracking for production observability
"""

import logging
import sys
from datetime import datetime
from typing import Optional

class PipelineLoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter that automatically includes job_id in all log messages
    """
    def process(self, msg, kwargs):
        job_id = self.extra.get('job_id', 'N/A')
        stage = self.extra.get('stage', 'SYSTEM')
        return f"Job {job_id} | {stage} | {msg}", kwargs


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for better visibility in terminal
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_pipeline_logger():
    """
    Configure the central pipeline logger
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger('pipeline')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler for CMD/terminal output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Detailed format with timestamp
    formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_job_logger(job_id: str, stage: str = "SYSTEM") -> PipelineLoggerAdapter:
    """
    Get a logger adapter with job_id and stage context
    
    Args:
        job_id: Unique job identifier
        stage: Pipeline stage (UPLOAD, OCR, PREPROCESSING, MAPPING, EVALUATION, FINAL)
    
    Returns:
        PipelineLoggerAdapter: Logger with job context
    """
    base_logger = logging.getLogger('pipeline')
    return PipelineLoggerAdapter(base_logger, {'job_id': job_id, 'stage': stage})


# Initialize the pipeline logger on module import
pipeline_logger = setup_pipeline_logger()


def log_stage_start(job_id: str, stage: str, detail: str = ""):
    """
    Log the start of a pipeline stage
    
    Args:
        job_id: Job identifier
        stage: Stage name
        detail: Additional details
    """
    logger = get_job_logger(job_id, stage)
    msg = f"Started"
    if detail:
        msg += f" - {detail}"
    logger.info(msg)


def log_stage_complete(job_id: str, stage: str, detail: str = ""):
    """
    Log the completion of a pipeline stage
    
    Args:
        job_id: Job identifier
        stage: Stage name
        detail: Additional details
    """
    logger = get_job_logger(job_id, stage)
    msg = f"✓ Completed"
    if detail:
        msg += f" - {detail}"
    logger.info(msg)


def log_stage_error(job_id: str, stage: str, error: str):
    """
    Log a stage error
    
    Args:
        job_id: Job identifier
        stage: Stage name
        error: Error message
    """
    logger = get_job_logger(job_id, stage)
    logger.error(f"✗ Failed - {error}")


def log_progress(job_id: str, stage: str, message: str):
    """
    Log progress within a stage
    
    Args:
        job_id: Job identifier
        stage: Stage name
        message: Progress message
    """
    logger = get_job_logger(job_id, stage)
    logger.info(message)
