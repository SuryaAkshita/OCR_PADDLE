"""
PDF to Image conversion and parsing
"""
from pdf2image import convert_from_path
from pathlib import Path
from typing import List, Tuple
import PyPDF2

from config.settings import PDF_TO_IMAGE_DPI, PDF_TO_IMAGE_FORMAT, TEMP_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFParser:
    """Convert PDF documents to images for OCR processing"""
    
    def __init__(self, dpi: int = None, output_format: str = None):
        """
        Initialize PDF parser
        
        Args:
            dpi: Resolution for image conversion (default from config)
            output_format: Image format (PNG or JPEG)
        """
        self.dpi = dpi or PDF_TO_IMAGE_DPI
        self.output_format = output_format or PDF_TO_IMAGE_FORMAT
    
    def convert_to_images(self, pdf_path: str, output_dir: str = None) -> List[str]:
        """
        Convert PDF to images (one per page)
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images (default: temp directory)
            
        Returns:
            List of image file paths
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            output_dir = Path(output_dir) if output_dir else TEMP_DIR
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Converting PDF to images: {pdf_path.name}")
            logger.info(f"DPI: {self.dpi}, Format: {self.output_format}")
            
            # Convert PDF to images
            images = convert_from_path(
                str(pdf_path),
                dpi=self.dpi,
                fmt=self.output_format.lower()
            )
            
            logger.info(f"PDF has {len(images)} page(s)")
            
            # Save images
            image_paths = []
            base_name = pdf_path.stem
            
            for i, image in enumerate(images, start=1):
                image_filename = f"{base_name}_page_{i:03d}.{self.output_format.lower()}"
                image_path = output_dir / image_filename
                
                image.save(str(image_path), self.output_format)
                image_paths.append(str(image_path))
                logger.debug(f"Saved page {i} to {image_filename}")
            
            logger.info(f"Successfully converted {len(image_paths)} pages to images")
            return image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get PDF metadata and information
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF information
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                info = {
                    'num_pages': len(pdf_reader.pages),
                    'is_encrypted': pdf_reader.is_encrypted,
                    'metadata': {}
                }
                
                # Extract metadata if available
                if pdf_reader.metadata:
                    metadata = pdf_reader.metadata
                    info['metadata'] = {
                        'author': metadata.get('/Author', 'N/A'),
                        'creator': metadata.get('/Creator', 'N/A'),
                        'producer': metadata.get('/Producer', 'N/A'),
                        'subject': metadata.get('/Subject', 'N/A'),
                        'title': metadata.get('/Title', 'N/A'),
                        'creation_date': metadata.get('/CreationDate', 'N/A'),
                    }
                
                logger.info(f"PDF Info - Pages: {info['num_pages']}, "
                           f"Encrypted: {info['is_encrypted']}")
                
                return info
                
        except Exception as e:
            logger.error(f"Error reading PDF info: {e}")
            return {'error': str(e)}
    
    def extract_text_if_possible(self, pdf_path: str) -> Tuple[bool, str]:
        """
        Try to extract text directly from PDF (if it's a text-based PDF)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (success: bool, text: str)
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                all_text = []
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    if text and text.strip():
                        all_text.append(f"--- Page {page_num} ---\n{text}")
                
                full_text = '\n\n'.join(all_text)
                
                if full_text.strip():
                    logger.info("Successfully extracted text directly from PDF")
                    return True, full_text
                else:
                    logger.info("PDF appears to be image-based, OCR required")
                    return False, ""
                    
        except Exception as e:
            logger.warning(f"Could not extract text from PDF: {e}")
            return False, ""