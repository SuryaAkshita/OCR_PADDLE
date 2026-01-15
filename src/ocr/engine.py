"""
OCR Engine using PaddleOCR
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # Fix OpenMP duplicate library issue

from paddleocr import PaddleOCR
import numpy as np
from typing import List, Dict, Tuple
import cv2
from pathlib import Path

from config.settings import PADDLEOCR_CONFIG, POSTPROCESSING
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OCREngine:
    """PaddleOCR engine for text extraction"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize OCR engine
        
        Args:
            config: Custom configuration (optional)
        """
        self.config = config or PADDLEOCR_CONFIG
        logger.info("Initializing PaddleOCR engine...")
        
        try:
            self.ocr = PaddleOCR(**self.config)
            logger.info("PaddleOCR engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise
    
    def extract_text(self, image_path: str) -> Tuple[str, List[Dict]]:
        """
        Extract text from image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (full_text, detailed_results)
        """
        try:
            logger.info(f"Processing image: {Path(image_path).name}")
            
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Failed to read image: {image_path}")
            
            # Perform OCR
            result = self.ocr.ocr(str(image_path), cls=True)
            
            if not result or not result[0]:
                logger.warning(f"No text detected in {image_path}")
                return "", []
            
            # Extract text and details
            full_text = []
            detailed_results = []
            
            for line in result[0]:
                if len(line) >= 2:
                    bbox = line[0]  # Bounding box coordinates
                    text_info = line[1]  # (text, confidence)
                    
                    text = text_info[0]
                    confidence = text_info[1]
                    
                    # Filter by confidence threshold
                    if confidence >= POSTPROCESSING['min_confidence']:
                        full_text.append(text)
                        
                        detailed_results.append({
                            'text': text,
                            'confidence': float(confidence),
                            'bbox': [[int(coord) for coord in point] for point in bbox]
                        })
            
            # Join text with newlines
            full_text_str = '\n'.join(full_text)
            
            logger.info(f"Extracted {len(detailed_results)} text lines with avg confidence: "
                       f"{np.mean([r['confidence'] for r in detailed_results]):.2f}")
            
            return full_text_str, detailed_results
            
        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")
            raise
    
    def extract_text_batch(self, image_paths: List[str]) -> List[Tuple[str, List[Dict]]]:
        """
        Extract text from multiple images
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of (full_text, detailed_results) tuples
        """
        results = []
        for img_path in image_paths:
            try:
                text, details = self.extract_text(img_path)
                results.append((text, details))
            except Exception as e:
                logger.error(f"Failed to process {img_path}: {e}")
                results.append(("", []))
        
        return results
    
    def extract_with_layout(self, image_path: str) -> Dict:
        """
        Extract text with layout information (preserving structure)
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with structured layout information
        """
        try:
            full_text, detailed_results = self.extract_text(image_path)
            
            # Sort by vertical position (y-coordinate)
            sorted_results = sorted(detailed_results, 
                                  key=lambda x: (x['bbox'][0][1], x['bbox'][0][0]))
            
            # Group into lines based on y-coordinate proximity
            lines = []
            current_line = []
            current_y = None
            y_threshold = 20  # Pixels threshold for same line
            
            for item in sorted_results:
                y_pos = item['bbox'][0][1]
                
                if current_y is None or abs(y_pos - current_y) <= y_threshold:
                    current_line.append(item)
                    current_y = y_pos if current_y is None else current_y
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = [item]
                    current_y = y_pos
            
            if current_line:
                lines.append(current_line)
            
            # Sort items within each line by x-coordinate
            for line in lines:
                line.sort(key=lambda x: x['bbox'][0][0])
            
            # Build structured output
            structured_text = []
            for line in lines:
                line_text = ' '.join([item['text'] for item in line])
                structured_text.append(line_text)
            
            return {
                'full_text': '\n'.join(structured_text),
                'lines': lines,
                'num_lines': len(lines)
            }
            
        except Exception as e:
            logger.error(f"Error extracting layout: {e}")
            raise