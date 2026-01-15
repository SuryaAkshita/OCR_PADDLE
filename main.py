"""
Main OCR Document Processor
Entry point for the application
"""
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from config.settings import (
    INPUT_DIR, OUTPUT_DIR, OUTPUT_JSON_DIR, 
    OUTPUT_TXT_DIR, TEMP_DIR
)
from src.parsers.pdf_parser import PDFParser
from src.parsers.form_parser import FormParser
from src.ocr.engine import OCREngine
from src.ocr.preprocessor import ImagePreprocessor
from src.ocr.postprocessor import TextPostprocessor
from src.utils.logger import get_logger
from src.utils.file_handler import FileHandler

logger = get_logger(__name__)


class DocumentOCRProcessor:
    """Main OCR processing pipeline"""
    
    def __init__(self):
        """Initialize processor components"""
        logger.info("Initializing OCR Document Processor")
        
        self.pdf_parser = PDFParser()
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = OCREngine()
        self.postprocessor = TextPostprocessor()
        self.form_parser = FormParser()
        self.file_handler = FileHandler()
    
    def process_document(self, input_path: str, preprocess: bool = True, 
                        cleanup_temp: bool = True) -> dict:
        """
        Process a document (PDF or image) with OCR
        
        Args:
            input_path: Path to input file (PDF or image)
            preprocess: Apply preprocessing to images (default: True)
            cleanup_temp: Clean up temporary files after processing (default: True)
            
        Returns:
            Dictionary with processing results
        """
        try:
            start_time = datetime.now()
            input_path = Path(input_path)
            
            logger.info("="*70)
            logger.info(f"Processing: {input_path.name}")
            logger.info("="*70)
            
            # Get file info
            file_info = self.file_handler.get_file_info(input_path)
            logger.info(f"File size: {file_info.get('size_mb', 0)} MB")
            
            # Step 1: Convert PDF to images if needed
            if input_path.suffix.lower() == '.pdf':
                logger.info("Step 1: Converting PDF to images...")
                
                # Try to extract text directly first
                has_text, direct_text = self.pdf_parser.extract_text_if_possible(str(input_path))
                
                if has_text:
                    logger.info("PDF contains extractable text - using direct extraction")
                    image_paths = []
                    all_text = direct_text
                    all_detailed_results = []
                else:
                    logger.info("PDF is image-based - proceeding with OCR")
                    image_paths = self.pdf_parser.convert_to_images(str(input_path))
                    all_text = None
            else:
                # Single image file
                image_paths = [str(input_path)]
                all_text = None
            
            # Step 2: Preprocess images if needed
            if all_text is None and preprocess and image_paths:
                logger.info("Step 2: Preprocessing images...")
                preprocessed_paths = []
                
                for img_path in tqdm(image_paths, desc="Preprocessing"):
                    preprocessed_path = self.preprocessor.preprocess(img_path)
                    preprocessed_paths.append(preprocessed_path)
                
                image_paths = preprocessed_paths
            
            # Step 3: Perform OCR
            if all_text is None:
                logger.info("Step 3: Performing OCR...")
                all_text_parts = []
                all_detailed_results = []
                
                for i, img_path in enumerate(tqdm(image_paths, desc="OCR Processing"), 1):
                    logger.info(f"Processing page {i}/{len(image_paths)}")
                    
                    text, detailed = self.ocr_engine.extract_text(img_path)
                    
                    if text:
                        all_text_parts.append(f"\n--- Page {i} ---\n{text}")
                        all_detailed_results.extend([
                            {**item, 'page': i} for item in detailed
                        ])
                
                all_text = '\n'.join(all_text_parts)
            
            # Step 4: Postprocess text
            logger.info("Step 4: Postprocessing text...")
            cleaned_text = self.postprocessor.process(all_text)
            
            # Step 5: Parse form data into structured format
            logger.info("Step 5: Parsing form data...")
            num_pages = len(image_paths) if image_paths else 1
            structured_form = self.form_parser.parse_document(cleaned_text, num_pages)
            
            # Extract structured fields
            extracted_fields = self.postprocessor.extract_fields(
                cleaned_text, 
                all_detailed_results if all_text else []
            )
            
            # Calculate confidence metrics
            confidence_metrics = self.postprocessor.calculate_confidence_score(
                all_detailed_results if all_text else []
            )
            
            # Step 6: Save results
            logger.info("Step 6: Saving results...")
            output_paths = self._save_results(
                input_path.stem,
                cleaned_text,
                all_detailed_results if all_text else [],
                extracted_fields,
                confidence_metrics,
                file_info,
                structured_form
            )
            
            # Cleanup
            if cleanup_temp:
                self.file_handler.cleanup_temp_files(TEMP_DIR)
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            logger.info("="*70)
            logger.info(f"Processing completed in {processing_time:.2f} seconds")
            logger.info(f"Output saved to: {OUTPUT_DIR}")
            logger.info("="*70)
            
            return {
                'success': True,
                'input_file': str(input_path),
                'output_paths': output_paths,
                'processing_time_seconds': processing_time,
                'num_pages': len(image_paths) if image_paths else 1,
                'extracted_fields': extracted_fields,
                'structured_form': structured_form,
                'confidence_metrics': confidence_metrics,
                'text_length': len(cleaned_text)
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'input_file': str(input_path)
            }
    
    def _save_results(self, base_name: str, text: str, detailed_results: list,
                     extracted_fields: dict, confidence_metrics: dict,
                     file_info: dict, structured_form: dict = None) -> dict:
        """Save processing results to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save plain text
        text_path = OUTPUT_TXT_DIR / f"{base_name}_{timestamp}.txt"
        self.file_handler.save_text(text, str(text_path))
        
        # Save structured JSON (form data)
        if structured_form:
            form_json_path = OUTPUT_JSON_DIR / f"{base_name}_{timestamp}_form.json"
            self.file_handler.save_json(structured_form, str(form_json_path))
        
        # Save general structured JSON
        json_path = OUTPUT_JSON_DIR / f"{base_name}_{timestamp}.json"
        result_data = {
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'input_file_info': file_info,
                'confidence_metrics': confidence_metrics
            },
            'extracted_fields': extracted_fields,
            'full_text': text,
            'text_length': len(text)
        }
        self.file_handler.save_json(result_data, str(json_path))
        
        # Save detailed results (with bounding boxes)
        if detailed_results:
            detailed_path = OUTPUT_JSON_DIR / f"{base_name}_{timestamp}_detailed.json"
            detailed_data = {
                'metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'total_detections': len(detailed_results),
                },
                'detections': detailed_results
            }
            self.file_handler.save_json(detailed_data, str(detailed_path))
        
        return {
            'text': str(text_path),
            'json': str(json_path),
            'form_json': str(form_json_path) if structured_form else None,
            'detailed': str(detailed_path) if detailed_results else None
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='OCR Document Processor using PaddleOCR'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Path to input PDF or image file'
    )
    parser.add_argument(
        '--no-preprocess',
        action='store_true',
        help='Skip image preprocessing'
    )
    parser.add_argument(
        '--keep-temp',
        action='store_true',
        help='Keep temporary files'
    )
    
    args = parser.parse_args()
    
    # Get input file
    if args.input:
        input_file = Path(args.input)
    else:
        # Look for files in input directory
        input_files = list(INPUT_DIR.glob('*.pdf')) + \
                     list(INPUT_DIR.glob('*.png')) + \
                     list(INPUT_DIR.glob('*.jpg')) + \
                     list(INPUT_DIR.glob('*.jpeg'))
        
        if not input_files:
            logger.error(f"No PDF or image files found in {INPUT_DIR}")
            logger.info("Please place your files in the data/input/ directory")
            logger.info("Or use: python main.py --input path/to/your/file.pdf")
            return
        
        input_file = input_files[0]
        logger.info(f"Processing first file found: {input_file.name}")
    
    if not input_file.exists():
        logger.error(f"File not found: {input_file}")
        return
    
    # Process document
    processor = DocumentOCRProcessor()
    result = processor.process_document(
        str(input_file),
        preprocess=not args.no_preprocess,
        cleanup_temp=not args.keep_temp
    )
    
    # Print summary
    if result['success']:
        print("\n" + "="*70)
        print("PROCESSING SUMMARY")
        print("="*70)
        print(f"Input File: {result['input_file']}")
        print(f"Pages Processed: {result['num_pages']}")
        print(f"Processing Time: {result['processing_time_seconds']:.2f}s")
        print(f"Text Extracted: {result['text_length']} characters")
        print(f"\nConfidence Metrics:")
        for key, value in result['confidence_metrics'].items():
            print(f"  {key}: {value}")
        print(f"\nExtracted Fields: {len(result['extracted_fields'])}")
        for key, value in result['extracted_fields'].items():
            print(f"  {key}: {value}")
        print(f"\nOutput Files:")
        for key, path in result['output_paths'].items():
            if path:
                print(f"  {key}: {path}")
        print("="*70)
    else:
        print(f"\nERROR: {result['error']}")


if __name__ == '__main__':
    main()