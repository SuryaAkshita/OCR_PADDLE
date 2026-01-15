"""
Image preprocessing for better OCR results
"""
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from pathlib import Path
from typing import Union

from config.settings import PREPROCESSING
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ImagePreprocessor:
    """Preprocess images for optimal OCR performance"""
    
    def __init__(self, config: dict = None):
        """
        Initialize preprocessor
        
        Args:
            config: Custom preprocessing configuration
        """
        self.config = config or PREPROCESSING
    
    def preprocess(self, image_path: Union[str, Path], output_path: Union[str, Path] = None) -> str:
        """
        Apply preprocessing pipeline to image
        
        Args:
            image_path: Path to input image
            output_path: Path to save processed image (optional)
            
        Returns:
            Path to processed image
        """
        try:
            logger.info(f"Preprocessing image: {Path(image_path).name}")
            
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Failed to read image: {image_path}")
            
            # Convert to PIL for some operations
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            
            # Resize if needed
            if self.config.get('resize', False):
                pil_img = self._resize_image(pil_img)
            
            # Enhance contrast
            if self.config.get('enhance_contrast', False):
                pil_img = self._enhance_contrast(pil_img)
            
            # Convert back to OpenCV format
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            # Denoise
            if self.config.get('denoise', False):
                img = self._denoise(img)
            
            # Binarize (optional, for very poor quality)
            if self.config.get('binarize', False):
                img = self._binarize(img)
            
            # Save processed image
            if output_path is None:
                output_path = Path(image_path).parent / f"preprocessed_{Path(image_path).name}"
            
            cv2.imwrite(str(output_path), img)
            logger.info(f"Preprocessed image saved to: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error during preprocessing: {e}")
            raise
    
    def _resize_image(self, img: Image.Image) -> Image.Image:
        """Resize image to optimal dimensions"""
        max_width = self.config.get('max_width', 2000)
        max_height = self.config.get('max_height', 3000)
        
        width, height = img.size
        
        # Calculate scaling factor
        width_scale = max_width / width if width > max_width else 1
        height_scale = max_height / height if height > max_height else 1
        scale = min(width_scale, height_scale)
        
        if scale < 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        return img
    
    def _enhance_contrast(self, img: Image.Image, factor: float = 1.5) -> Image.Image:
        """Enhance image contrast"""
        enhancer = ImageEnhance.Contrast(img)
        enhanced = enhancer.enhance(factor)
        logger.debug("Enhanced image contrast")
        return enhanced
    
    def _denoise(self, img: np.ndarray) -> np.ndarray:
        """Remove noise from image"""
        denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        logger.debug("Applied denoising")
        return denoised
    
    def _binarize(self, img: np.ndarray) -> np.ndarray:
        """Convert image to binary (black and white)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Convert back to 3-channel for consistency
        binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        logger.debug("Applied binarization")
        return binary_bgr
    
    def auto_rotate(self, img: np.ndarray) -> np.ndarray:
        """
        Auto-rotate image to correct orientation
        (Useful for scanned documents)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
            
            if lines is not None:
                # Calculate average angle
                angles = []
                for rho, theta in lines[:, 0]:
                    angle = np.degrees(theta) - 90
                    angles.append(angle)
                
                median_angle = np.median(angles)
                
                # Rotate if needed
                if abs(median_angle) > 0.5:
                    h, w = img.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    rotated = cv2.warpAffine(img, M, (w, h), 
                                            flags=cv2.INTER_CUBIC,
                                            borderMode=cv2.BORDER_REPLICATE)
                    logger.debug(f"Auto-rotated image by {median_angle:.2f} degrees")
                    return rotated
            
            return img
            
        except Exception as e:
            logger.warning(f"Auto-rotation failed: {e}")
            return img