# PDF OCR Paddle - Form Extraction Output

## Overview

The PDF OCR Paddle application now successfully:
1. ✅ Converts PDF documents to structured text
2. ✅ Extracts form fields and organizes them by page and section
3. ✅ Generates structured JSON output with organized form data
4. ✅ Handles multi-page documents (up to 13 pages in test)
5. ✅ Extracts document metadata (DocuSign IDs, totalpages, etc.)

## Output Structure

The application now generates **structured form JSON** with the following format:

```json
{
  "document": {
    "file_name": "main_test_file.pdf",
    "document_type": "WorldTrips Claimant Statement and Authorization",
    "total_pages": 10,
    "docu_sign_envelope_id": "5208D50D-6221-461D-B926-C9BA6DF98167",
    "extracted_at": "2026-01-15T17:31:04.826157"
  },
  "pages": [
    {
      "page": 1,
      "section": "PART A: CLAIMANT INFORMATION",
      "raw_text": "...",
      "form_fields": {
        "1a_claimant_full_name": "Ilyas Malik",
        "2a_gender": "Male",
        "3a_date_of_birth_mm_dd_yy": "07/03/2008",
        "4a_current_mailing_address": "69 Sylvester Avenue",
        "5a_city": "Winchester",
        "6a_state": "MA",
        "7a_postal_code": "01890",
        "8a_country": "USA",
        "9a_primary_telephone": "120392469",
        "11a_email_address": "razmalik@gmail.com",
        "12a_policy_or_certificate_number": "245549351",
        "14a_home_country": "USA",
        "15a_countries_visited": "England, Turkey"
      }
    },
    {
      "page": 2,
      "section": "PART A (Continued) + PART B: TRAVEL ASSISTANCE AND OTHER CLAIMS",
      "form_fields": { ... },
      "part_b": { ... }
    },
    {
      "page": 3,
      "section": "PART C: MEDICAL INFORMATION",
      "form_fields": {
        "1c_symptoms_description": "Fever, headaches, GI issues, Dizziness",
        ...
      }
    },
    {
      "page": 4,
      "section": "PART D: MEDICAL RECORD AUTHORIZATION",
      "signatures": {
        "claimant_signature_date_mm_dd_yy": "09/05/2023",
        "insured_signature_date_mm_dd_yy": "09/05/2023",
        "printed_name": "Ilyas Malik"
      }
    },
    {
      "page": 5,
      "section": "SUPPLEMENT A — NON-U.S. CLAIM ITEMIZATION FORM",
      "tables": {
        "supplement_a_items": [
          {
            "date_of_service_mm_dd_yy": "07/09/2023",
            "provider": "ACIBADEM Hospital",
            "diagnosis": "virus",
            "description_of_services": "Examination and tests",
            "currency": "TL (Turkish Lira)",
            "country": "Turkey",
            "amount_charged": "4590.599"
          }
        ]
      }
    },
    {
      "page": 7,
      "section": "SUPPLEMENT C — PAYMENT AUTHORIZATION AGREEMENT FORM",
      "form_fields": {
        "beneficiary_name": "Raheel Malik",
        "beneficiary_email": "razmalik@gmail.com",
        "beneficiary_address": "69 Sylvester Avenue",
        "beneficiary_city": "Winchester",
        "beneficiary_state": "MA",
        "beneficiary_postal_code": "01890",
        "beneficiary_country": "USA",
        "payment_type": "Check"
      },
      "third_party_payment_form": { ... }
    }
  ]
}
```

## Output Files

The application generates multiple output files in `data/output/`:

### 1. **Form JSON** (`*_form.json`)
- **Purpose**: Structured form data organized by page and section
- **Best For**: Machine-readable form parsing, data extraction, automation
- **Contains**: 
  - Document metadata
  - Page-by-page breakdowns
  - Extracted form fields with proper naming
  - Table data (supplement items)
  - Signature dates and information

### 2. **General JSON** (`*.json`)
- **Purpose**: Overall processing metadata and extracted fields
- **Contains**:
  - Processing metadata (timestamps, confidence scores)
  - General extracted fields (policy number, phone numbers, etc.)
  - Full text length
  - File information

### 3. **Plain Text** (`*.txt`)
- **Purpose**: Raw extracted text organized by page
- **Best For**: Human review, debugging OCR quality
- **Contains**: Page-by-page raw text output

### 4. **Detailed JSON** (`*_detailed.json`)
- **Purpose**: Low-level OCR detections with bounding boxes
- **Contains**: Individual text detections from the PDF with coordinates

## Sample Extracted Data (Page 1: PART A)

From the test file, the following data was successfully extracted:

```json
{
  "1a_claimant_full_name": "Ilyas Malik",
  "2a_gender": "Male",
  "3a_date_of_birth_mm_dd_yy": "07/03/2008",
  "4a_current_mailing_address": "69 Sylvester Avenue",
  "5a_city": "Winchester",
  "6a_state": "MA",
  "7a_postal_code": "01890",
  "8a_country": "USA",
  "9a_primary_telephone": "120392469",
  "11a_email_address": "razmalik@gmail.com",
  "12a_policy_or_certificate_number": "245549351",
  "14a_home_country": "USA",
  "15a_countries_visited": "England, Turkey"
}
```

## How to Use

### Running the OCR Processor

```bash
# Process first PDF found in data/input/
python main.py

# Process specific file
python main.py --input path/to/your/file.pdf

# Skip preprocessing (faster, may have lower quality)
python main.py --no-preprocess

# Keep temporary files for debugging
python main.py --keep-temp
```

### Processing Results

After running, check the output:

```bash
# Form JSON (recommended for programmatic use)
data/output/json/main_test_file_*_form.json

# Plain text (for human review)
data/output/txt/main_test_file_*.txt

# General processing metadata
data/output/json/main_test_file_*.json
```

## Form Field Naming Convention

All form fields follow a naming pattern:

- **PART A** (Claimant Info): `{field_number}_claimant_{description}`
  - Example: `1a_claimant_full_name`, `2a_gender`

- **PART B** (Travel Claims): `{field_number}b_{description}`
  - Example: `1b_applying_for`, `2b_incident_details`

- **PART C** (Medical Info): `{field_number}c_{description}`
  - Example: `1c_onset_of_illness_or_date_time_of_injury`

- **PART D** (Signatures): `signatures` dict
  - Contains: `claimant_signature_date_mm_dd_yy`, `printed_name`, etc.

- **SUPPLEMENT A-D**: Respective form fields and tables

## Data Extraction Quality

The extraction quality depends on:

1. **PDF Type**:
   - ✅ Text-based PDFs: Excellent extraction
   - ⚠️ Scanned/Image PDFs: Good extraction (OCR-dependent)

2. **Form Layout**:
   - ✅ Structured forms with clear labels: Excellent
   - ⚠️ Complex layouts: May need manual adjustment

3. **Preprocessing**:
   - ✅ Default preprocessing handles most cases
   - ⚠️ Poor quality scans may need `--no-preprocess` toggle

## Advanced Usage

### Custom Processing Configuration

Edit `config/settings.py` to customize:

```python
# PADDLEOCR_CONFIG
PADDLEOCR_CONFIG = {
    'use_angle_cls': True,      # Detect rotated text
    'lang': 'en',                # Language (supports multiple)
    'device': 'cpu',             # 'cpu' or 'gpu'
    'det_db_thresh': 0.3,       # Detection sensitivity
    'det_db_box_thresh': 0.5,   # Box threshold
}

# Image preprocessing
PREPROCESSING = {
    'resize': True,
    'max_width': 2000,
    'enhance_contrast': True,
    'denoise': True,
}
```

### Using the Form Parser Programmatically

```python
from src.parsers.form_parser import FormParser

# Create parser
parser = FormParser()

# Parse document text
result = parser.parse_document(full_text, num_pages=10)

# Access structured data
print(result['document']['docu_sign_envelope_id'])
print(result['pages'][0]['form_fields']['1a_claimant_full_name'])
```

## Dependencies

- **PaddleOCR**: OCR engine
- **pdf2image**: PDF to image conversion
- **Pillow**: Image processing
- **OpenCV**: Computer vision
- **pandas**: Data processing (optional)

## Next Steps for Improvement

1. **Better Layout Analysis**: Implement grid-based form detection
2. **Checkbox Detection**: Auto-detect checked vs unchecked boxes
3. **Table Parsing**: Improved table structure recognition
4. **Confidence Scores**: Add confidence metrics per field
5. **Batch Processing**: Process multiple files efficiently
6. **Web API**: REST endpoint for form processing

## Troubleshooting

### Poor Text Extraction
- Check if PDF is text-based or image-based
- Try with `--no-preprocess` flag
- Verify PDF quality

### Missing Fields
- Some fields may be optional in the form
- Check raw text output (`*.txt`) for OCR quality
- Adjust regex patterns in `form_parser.py` if needed

### Performance Issues
- Use `--no-preprocess` for faster processing
- Use GPU: set `device: 'gpu'` in config (requires CUDA)
- Process smaller PDFs first

## Example Output Location

After running `python main.py` on test file:

```
data/output/
├── json/
│   ├── main_test_file_20260115_173247.json         # General metadata
│   ├── main_test_file_20260115_173247_form.json    # Form structure
│   └── main_test_file_20260115_173247_detailed.json # OCR details
└── txt/
    └── main_test_file_20260115_173247.txt          # Raw text
```

---

**Last Updated**: January 15, 2026  
**Version**: 1.0  
**Status**: ✅ Functional - Form parsing working, ready for production use
