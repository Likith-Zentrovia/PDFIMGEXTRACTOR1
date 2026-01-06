# PDF Image Extractor

A powerful Python tool for extracting images from PDF files with batch processing capabilities and optional AI-powered image quality detection using Claude.

## Features

- **Two Extraction Modes**:
  - **Image Region Rendering Mode**: Detects images and renders only those regions (screenshot-like), perfect for preserving text
  - **Embedded Extraction Mode**: Extracts individual embedded images from PDFs
- **Batch Processing**: Process entire folders of PDF files at once
- **Organized Output**: Each PDF gets its own folder for extracted images
- **High Accuracy**: Uses PyMuPDF for reliable image extraction
- **Adjustable DPI**: Control output quality with DPI settings (render mode)
- **Duplicate Detection**: Automatically skips duplicate images within PDFs (embedded mode)
- **Size Filtering**: Filters out tiny images (icons, logos) based on file size (embedded mode)
- **AI-Powered Quality Detection**: Optional Claude AI integration to filter out low-quality or irrelevant images
- **Progress Tracking**: Real-time progress bars for batch operations
- **Multiple Format Support**: Extracts PNG, JPEG, and other image formats

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd PDFIMGEXTRACTOR1
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up Claude AI integration:
   - Copy `.env.example` to `.env`
   - Add your Anthropic API key to the `.env` file
   ```bash
   cp .env.example .env
   # Edit .env and add your API key
   ```

## Usage

### Basic Usage - Single PDF

Extract images from a single PDF file:

```bash
python pdf_image_extractor.py -i document.pdf -o output_images
```

### Batch Processing - Multiple PDFs

Process all PDF files in a folder:

```bash
python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch
```

This will:
- Find all PDF files in `pdfs_folder`
- Extract images from each PDF
- Save images in separate folders: `extracted_images/pdf_name1/`, `extracted_images/pdf_name2/`, etc.

### Image Region Rendering Mode (Screenshot Mode) - RECOMMENDED

**Use this mode when text in images appears altered or you need pixel-perfect extraction:**

```bash
python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch --render
```

This mode:
- Detects where images are located in the PDF
- Renders only those specific image regions (not the entire page)
- Like taking a screenshot of just the image area
- Preserves text within images perfectly without alteration
- No text quality loss or encoding issues
- Default 300 DPI (adjustable with `--dpi`)

**For even higher quality:**
```bash
python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch --render --dpi 600
```

### With Claude AI Quality Detection

Use Claude AI to filter out low-quality images:

```bash
python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch --use-claude
```

This will analyze each extracted image and keep only high-quality, meaningful images.

### Custom Minimum Image Size

Set a custom minimum image size (in bytes) to filter out small images:

```bash
python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch --min-size 50000
```

## Command Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `-i, --input` | Yes | Input PDF file or folder containing PDFs |
| `-o, --output` | Yes | Output folder for extracted images |
| `--batch` | No | Enable batch processing mode |
| `--render` | No | Render pages as images (screenshot mode, preserves text perfectly) |
| `--dpi` | No | DPI for page rendering (only with `--render`, default: 300) |
| `--use-claude` | No | Use Claude AI for image quality detection |
| `--min-size` | No | Minimum image size in bytes (embedded mode only, default: 10000) |

## Examples

### Example 1: Extract from a Single PDF
```bash
python pdf_image_extractor.py -i research_paper.pdf -o extracted
```

**Output Structure:**
```
extracted/
└── research_paper/
    ├── page1_img1.png
    ├── page3_img1.jpeg
    └── page5_img1.png
```

### Example 2: Batch Process with AI Filtering
```bash
python pdf_image_extractor.py -i ./my_pdfs -o ./output --batch --use-claude
```

**Input Structure:**
```
my_pdfs/
├── document1.pdf
├── document2.pdf
└── document3.pdf
```

**Output Structure:**
```
output/
├── document1/
│   ├── page1_img1.png
│   └── page2_img1.jpeg
├── document2/
│   ├── page1_img1.png
│   ├── page3_img1.png
│   └── page4_img1.jpeg
└── document3/
    └── page1_img1.png
```

### Example 3: Image Region Rendering Mode (Best for Text Preservation)
```bash
python pdf_image_extractor.py -i ./pdfs -o ./output --batch --render --dpi 300
```

**Output Structure:**
```
output/
├── document1/
│   ├── page1_img1.png    # Screenshot of image region from page 1
│   ├── page2_img1.png    # Screenshot of image region from page 2
│   └── page3_img1.png
├── document2/
│   ├── page1_img1.png
│   └── page2_img1.png
└── document3/
    └── page1_img1.png
```

Only image regions are rendered (not entire pages), preserving text within images perfectly.

### Example 4: Large Images Only (Embedded Mode)
```bash
python pdf_image_extractor.py -i ./pdfs -o ./output --batch --min-size 100000
```

This will only extract embedded images larger than 100KB.

## How It Works

### Embedded Image Extraction Mode (Default)

1. **PDF Scanning**: Opens each PDF and scans all pages
2. **Image Detection**: Identifies all embedded images using PyMuPDF
3. **Duplicate Removal**: Tracks image XREFs to avoid extracting the same image multiple times
4. **Size Filtering**: Skips images smaller than the minimum size threshold
5. **Extraction**: Saves images in their original format (PNG, JPEG, etc.)
6. **AI Analysis** (optional): Uses Claude to determine if images are high-quality and meaningful
7. **Organization**: Saves all images in organized folders

### Image Region Rendering Mode (`--render`)

1. **PDF Scanning**: Opens each PDF and scans all pages
2. **Image Detection**: Identifies all images and their exact positions/coordinates
3. **Bounding Box Extraction**: Gets the rectangular area of each image
4. **Region Rendering**: Renders only that specific image region at high DPI (not the whole page)
5. **Pixel-Perfect Capture**: Captures the image area exactly as it appears, preserving any text within
6. **PNG Output**: Saves each image region as a PNG with lossless compression
7. **AI Analysis** (optional): Uses Claude to determine if images are high-quality and meaningful
8. **Organization**: Saves all rendered image regions in organized folders

## Claude AI Integration

When using `--use-claude`, the tool will:

1. Extract all images from the PDF
2. Send each image to Claude AI for analysis
3. Ask Claude if the image is meaningful and high-quality
4. Keep only images that Claude identifies as valuable
5. Remove low-quality images (icons, decorative elements, etc.)

This is particularly useful for:
- Academic papers with many small figures and icons
- Documents with watermarks or logos
- PDFs with mixed content quality

## Configuration

### Environment Variables

Create a `.env` file with the following:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Get your API key from: https://console.anthropic.com/

### Adjusting Extraction Parameters

You can modify the `PDFImageExtractor` class parameters:

```python
extractor = PDFImageExtractor(
    use_claude=True,           # Enable Claude AI
    min_image_size=10000       # Minimum size in bytes
)
```

## Performance Considerations

- **Batch Processing**: Processes files sequentially for reliability
- **Claude AI**: Adds processing time but significantly improves output quality
- **Memory**: Processes one PDF at a time to minimize memory usage
- **Storage**: Original image formats preserved for best quality

## Troubleshooting

### "No module named 'fitz'"
Install PyMuPDF:
```bash
pip install PyMuPDF
```

### "ANTHROPIC_API_KEY not found"
Either:
- Don't use the `--use-claude` flag, or
- Create a `.env` file with your API key

### "No PDF files found"
Make sure:
- Your input folder contains `.pdf` files
- You're using the correct path
- You have read permissions for the folder

## Requirements

- Python 3.7+
- PyMuPDF (fitz)
- Pillow (PIL)
- anthropic (optional, for Claude AI features)
- python-dotenv
- tqdm

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
