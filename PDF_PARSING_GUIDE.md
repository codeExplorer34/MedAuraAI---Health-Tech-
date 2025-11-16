# PDF Parsing Guide

## How It Works

The PDF parsing feature uses a two-stage approach:

### 1. Text Extraction
- Uses `pdfplumber` library to extract text from PDF files
- Supports multi-page PDFs
- Handles standard text-based PDFs

### 2. AI-Powered Data Extraction
- Uses Google Gemini Pro to intelligently parse the extracted text
- Extracts structured medical data:
  - Patient demographics (ID, name, age, gender)
  - Chief complaint
  - Medical history (family, personal)
  - Lifestyle factors
  - Medications
  - Lab results (blood tests, stool studies, colonoscopy)
  - Vital signs
  - Physical examination findings

### 3. Fallback Parsing
- If AI parsing fails, falls back to rule-based text parsing
- Uses pattern matching to find common medical report sections

## Supported PDF Types

✅ **Works Best:**
- Text-based PDFs (created from Word, Google Docs, etc.)
- PDFs with structured medical report format
- Multi-page reports

⚠️ **Limited Support:**
- Scanned PDFs (image-based) - May need OCR preprocessing
- Handwritten reports - Not supported
- PDFs with complex layouts - May miss some fields

## Usage

1. **Upload PDF** in the Case Intake Wizard
2. **Wait for processing** (usually 5-15 seconds)
3. **Review extracted data** - Form fields auto-populate
4. **Edit as needed** - You can always modify extracted data
5. **Submit case** - Proceeds to AI agent analysis

## Error Handling

- **File too large**: Maximum 10MB
- **Invalid PDF**: Must be a valid PDF file
- **No text found**: PDF may be scanned/corrupted
- **Extraction failed**: Falls back to manual entry

## Tips for Best Results

1. **Use structured reports** - Reports with clear sections work best
2. **Check extracted data** - Always review and correct if needed
3. **Manual entry** - Still available if PDF parsing doesn't work
4. **File size** - Keep PDFs under 10MB for faster processing

## Technical Details

- **Backend**: FastAPI endpoint `/api/cases/parse-report`
- **AI Model**: Google Gemini Pro (via LangChain)
- **Libraries**: `pdfplumber` for text extraction
- **Processing Time**: 5-15 seconds depending on PDF complexity

