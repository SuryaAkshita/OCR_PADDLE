"""
Text postprocessing and cleanup
"""
import re
from typing import List, Dict
from config.settings import POSTPROCESSING
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TextPostprocessor:
    """Clean and enhance OCR extracted text"""
    
    def __init__(self, config: dict = None):
        """
        Initialize postprocessor
        
        Args:
            config: Custom postprocessing configuration
        """
        self.config = config or POSTPROCESSING
        
        # Common OCR errors mapping
        self.error_corrections = {
            r'\b0\b': 'O',  # Zero to letter O in context
            r'\bl\b': 'I',  # lowercase L to I in context
            r'rn': 'm',     # Common OCR error
            r'\|': 'I',     # Pipe to I
            r'~': '-',      # Tilde to dash
        }
    
    def process(self, text: str) -> str:
        """
        Apply postprocessing pipeline to text
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        try:
            if not text:
                return text
            
            # Remove extra whitespace
            if self.config.get('remove_extra_whitespace', True):
                text = self._remove_extra_whitespace(text)
            
            # Fix common OCR errors
            if self.config.get('fix_common_ocr_errors', True):
                text = self._fix_common_errors(text)
            
            # Additional cleanup
            text = self._clean_special_characters(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Error during postprocessing: {e}")
            return text
    
    def _remove_extra_whitespace(self, text: str) -> str:
        """Remove extra spaces and normalize whitespace"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _fix_common_errors(self, text: str) -> str:
        """Fix common OCR recognition errors"""
        for pattern, replacement in self.error_corrections.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _clean_special_characters(self, text: str) -> str:
        """Clean up problematic special characters"""
        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Fix common punctuation spacing
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        return text
    
    def extract_fields(self, text: str, detailed_results: List[Dict]) -> Dict:
        """
        Extract structured fields from form text
        (Specific to WorldTrips insurance claim form)
        
        Args:
            text: Full OCR text
            detailed_results: Detailed OCR results with bounding boxes
            
        Returns:
            Dictionary of extracted fields
        """
        fields = {}
        
        try:
            # Extract policy/certificate number
            policy_match = re.search(r'(?:Policy|Certificate)\s*Number[:\s]*([A-Z0-9]+)', text, re.IGNORECASE)
            if policy_match:
                fields['policy_number'] = policy_match.group(1)
            
            # Extract name
            name_match = re.search(r"Claimant's Full Name[:\s]*([A-Za-z\s]+)", text, re.IGNORECASE)
            if name_match:
                fields['claimant_name'] = name_match.group(1).strip()
            
            # Extract date of birth
            dob_match = re.search(r'Date of Birth[:\s]*(\d{2}/\d{2}/\d{2,4})', text, re.IGNORECASE)
            if dob_match:
                fields['date_of_birth'] = dob_match.group(1)
            
            # Extract email
            email_match = re.search(r'Email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text, re.IGNORECASE)
            if email_match:
                fields['email'] = email_match.group(1)
            
            # Extract address
            address_match = re.search(r'(?:Current Mailing Address|Address)[:\s]*([A-Za-z0-9\s,.-]+)', text, re.IGNORECASE)
            if address_match:
                fields['address'] = address_match.group(1).strip()
            
            # Extract city
            city_match = re.search(r'City[:\s]*([A-Za-z\s]+)', text, re.IGNORECASE)
            if city_match:
                fields['city'] = city_match.group(1).strip()
            
            # Extract state
            state_match = re.search(r'State[:\s]*([A-Z]{2})', text)
            if state_match:
                fields['state'] = state_match.group(1)
            
            # Extract postal code
            postal_match = re.search(r'Postal Code[:\s]*(\d{5}(?:-\d{4})?)', text, re.IGNORECASE)
            if postal_match:
                fields['postal_code'] = postal_match.group(1)
            
            # Extract phone numbers
            phone_matches = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
            if phone_matches:
                fields['phone_numbers'] = phone_matches
            
            logger.info(f"Extracted {len(fields)} structured fields")
            
        except Exception as e:
            logger.error(f"Error extracting fields: {e}")
        
        return fields
    
    def calculate_confidence_score(self, detailed_results: List[Dict]) -> Dict:
        """
        Calculate overall confidence metrics
        
        Args:
            detailed_results: Detailed OCR results
            
        Returns:
            Dictionary with confidence metrics
        """
        if not detailed_results:
            return {
                'average_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'total_detections': 0
            }
        
        confidences = [r['confidence'] for r in detailed_results]
        
        return {
            'average_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'total_detections': len(detailed_results),
            'low_confidence_count': sum(1 for c in confidences if c < 0.7)
        }