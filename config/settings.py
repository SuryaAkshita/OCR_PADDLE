"""
Configuration settings for OCR Document Processor
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
TEMP_DIR = DATA_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Output subdirectories
OUTPUT_JSON_DIR = OUTPUT_DIR / "json"
OUTPUT_TXT_DIR = OUTPUT_DIR / "txt"
OUTPUT_IMAGES_DIR = OUTPUT_DIR / "images"

# Create directories if they don't exist
for directory in [INPUT_DIR, OUTPUT_DIR, TEMP_DIR, LOGS_DIR, 
                  OUTPUT_JSON_DIR, OUTPUT_TXT_DIR, OUTPUT_IMAGES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# PaddleOCR settings
PADDLEOCR_CONFIG = {
    'use_angle_cls': True,          # Enable angle classification
    'lang': 'en',                   # Language
    'device': 'cpu',                # 'cpu' or 'gpu' (use GPU if available)
    'det_db_thresh': 0.3,           # Detection threshold (lower = more sensitive)
    'det_db_box_thresh': 0.5,       # Box threshold
}

# PDF to Image conversion settings
PDF_TO_IMAGE_DPI = 300              # Higher DPI = better quality but larger files
PDF_TO_IMAGE_FORMAT = 'PNG'         # PNG or JPEG

# Image preprocessing settings
PREPROCESSING = {
    'resize': True,
    'max_width': 2000,
    'max_height': 3000,
    'enhance_contrast': True,
    'denoise': True,
    'binarize': False,              # Set to True for very poor quality scans
}

# Text postprocessing settings
POSTPROCESSING = {
    'remove_extra_whitespace': True,
    'fix_common_ocr_errors': True,
    'min_confidence': 0.5,          # Minimum confidence score (0-1)
}

# Logging settings
LOG_LEVEL = "INFO"                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "ocr_processor.log"

# Processing settings
BATCH_SIZE = 5                      # Number of pages to process at once
MAX_WORKERS = 4                     # Parallel processing workers