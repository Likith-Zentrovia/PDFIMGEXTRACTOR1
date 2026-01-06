#!/usr/bin/env python3
"""
PDF Image Extractor with Batch Processing
Extracts images from PDF files with high accuracy and organizes them in separate folders.
"""

import os
import sys
import argparse
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
import io
from tqdm import tqdm
from typing import List, Tuple, Optional
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PDFImageExtractor:
    """Extracts images from PDF files with batch processing support."""

    def __init__(self, use_claude: bool = False, min_image_size: int = 10000,
                 render_mode: bool = False, dpi: int = 300):
        """
        Initialize the PDF image extractor.

        Args:
            use_claude: Whether to use Claude AI for image quality detection
            min_image_size: Minimum image size in bytes to consider (filters tiny images)
            render_mode: If True, renders pages as images (screenshot-like). If False, extracts embedded images.
            dpi: DPI for page rendering (only used when render_mode=True, default: 300)
        """
        self.use_claude = use_claude
        self.min_image_size = min_image_size
        self.render_mode = render_mode
        self.dpi = dpi
        self.claude_client = None

        if use_claude:
            try:
                import anthropic
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if not api_key:
                    print("Warning: ANTHROPIC_API_KEY not found in environment. Claude AI features disabled.")
                    self.use_claude = False
                else:
                    self.claude_client = anthropic.Anthropic(api_key=api_key)
                    print("Claude AI integration enabled for image quality detection.")
            except ImportError:
                print("Warning: anthropic package not installed. Claude AI features disabled.")
                self.use_claude = False

    def extract_images_from_pdf(self, pdf_path: str, output_folder: str) -> List[str]:
        """
        Extract all images from a single PDF file.

        Args:
            pdf_path: Path to the PDF file
            output_folder: Folder to save extracted images

        Returns:
            List of saved image file paths
        """
        # Choose extraction method based on render_mode
        if self.render_mode:
            return self._render_pages_as_images(pdf_path, output_folder)
        else:
            return self._extract_embedded_images(pdf_path, output_folder)

    def _render_pages_as_images(self, pdf_path: str, output_folder: str) -> List[str]:
        """
        Detect images in PDF and render only those image regions (screenshot mode).
        This preserves text within images perfectly without alteration.

        Args:
            pdf_path: Path to the PDF file
            output_folder: Folder to save rendered image regions

        Returns:
            List of saved image file paths
        """
        saved_images = []

        try:
            # Open the PDF
            pdf_document = fitz.open(pdf_path)

            # Create output folder if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)

            # Calculate zoom factor for desired DPI (default 72 DPI in PDF)
            zoom = self.dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            # Track unique images using hash to avoid duplicates
            seen_images = set()

            # Iterate through each page
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]

                # Get list of images on the page
                image_list = page.get_images(full=True)

                # Process each image
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]  # Image XREF number

                    # Skip if we've seen this image before (duplicate)
                    if xref in seen_images:
                        continue
                    seen_images.add(xref)

                    try:
                        # Get all instances of this image on the page
                        img_rects = page.get_image_rects(xref)

                        if not img_rects:
                            continue

                        # Use the first rectangle (main instance)
                        rect = img_rects[0]

                        # Skip very small images (likely logos, icons, etc.)
                        # Calculate area in points
                        area = (rect.width * rect.height)
                        if area < (self.min_image_size / 100):  # Rough heuristic
                            continue

                        # Add some padding around the image (optional, 2 points on each side)
                        padded_rect = rect + (-2, -2, 2, 2)

                        # Make sure the rectangle is within page bounds
                        padded_rect = padded_rect.intersect(page.rect)

                        # Render only this region of the page at high DPI
                        pix = page.get_pixmap(matrix=mat, clip=padded_rect, alpha=False)

                        # Skip if rendered image is too small
                        if pix.width < 50 or pix.height < 50:
                            continue

                        # Create a unique filename
                        image_filename = f"page{page_num + 1}_img{img_index + 1}.png"
                        image_path = os.path.join(output_folder, image_filename)

                        # Save the rendered image region
                        pix.save(image_path)
                        saved_images.append(image_path)

                    except Exception as e:
                        print(f"  Warning: Could not render image {img_index + 1} from page {page_num + 1}: {str(e)}")
                        continue

            pdf_document.close()

            # Optionally use Claude AI to analyze image quality
            if self.use_claude and saved_images:
                saved_images = self._filter_images_with_claude(saved_images)

            return saved_images

        except Exception as e:
            print(f"Error rendering PDF {pdf_path}: {str(e)}")
            return []

    def _extract_embedded_images(self, pdf_path: str, output_folder: str) -> List[str]:
        """
        Extract embedded images from PDF (original extraction method).

        Args:
            pdf_path: Path to the PDF file
            output_folder: Folder to save extracted images

        Returns:
            List of saved image file paths
        """
        saved_images = []

        try:
            # Open the PDF
            pdf_document = fitz.open(pdf_path)

            # Create output folder if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)

            # Track unique images using hash to avoid duplicates
            seen_images = set()

            # Iterate through each page
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]

                # Get list of images on the page
                image_list = page.get_images(full=True)

                # Extract each image
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]  # Image XREF number

                    # Skip if we've seen this image before (duplicate)
                    if xref in seen_images:
                        continue
                    seen_images.add(xref)

                    # Extract the image
                    try:
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # Skip very small images (likely logos, icons, etc.)
                        if len(image_bytes) < self.min_image_size:
                            continue

                        # Create a unique filename
                        image_filename = f"page{page_num + 1}_img{img_index + 1}.{image_ext}"
                        image_path = os.path.join(output_folder, image_filename)

                        # Save the image
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)

                        saved_images.append(image_path)

                    except Exception as e:
                        print(f"  Warning: Could not extract image {img_index + 1} from page {page_num + 1}: {str(e)}")
                        continue

            pdf_document.close()

            # Optionally use Claude AI to analyze image quality
            if self.use_claude and saved_images:
                saved_images = self._filter_images_with_claude(saved_images)

            return saved_images

        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            return []

    def _filter_images_with_claude(self, image_paths: List[str]) -> List[str]:
        """
        Use Claude AI to analyze and filter images based on quality and relevance.

        Args:
            image_paths: List of image file paths

        Returns:
            Filtered list of high-quality image paths
        """
        if not self.claude_client:
            return image_paths

        filtered_images = []

        print("  Analyzing images with Claude AI...")
        for img_path in tqdm(image_paths, desc="  AI Analysis", leave=False):
            try:
                # Read and encode image
                with open(img_path, "rb") as img_file:
                    image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")

                # Determine image type
                ext = Path(img_path).suffix.lower()
                media_type_map = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                media_type = media_type_map.get(ext, 'image/jpeg')

                # Ask Claude to analyze the image
                message = self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=200,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": image_data,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": "Is this a meaningful, high-quality image (not a small icon, logo, or decorative element)? Answer with just 'YES' or 'NO'."
                                }
                            ],
                        }
                    ],
                )

                response = message.content[0].text.strip().upper()

                if 'YES' in response:
                    filtered_images.append(img_path)
                else:
                    # Delete low-quality images
                    os.remove(img_path)

            except Exception as e:
                print(f"    Warning: Claude AI analysis failed for {img_path}: {str(e)}")
                # Keep the image if analysis fails
                filtered_images.append(img_path)

        return filtered_images

    def batch_process(self, input_folder: str, output_base_folder: str) -> dict:
        """
        Process multiple PDF files in batch.

        Args:
            input_folder: Folder containing PDF files
            output_base_folder: Base folder for output (subfolders created per PDF)

        Returns:
            Dictionary with processing statistics
        """
        # Find all PDF files
        pdf_files = list(Path(input_folder).glob("*.pdf"))
        pdf_files.extend(Path(input_folder).glob("*.PDF"))

        if not pdf_files:
            print(f"No PDF files found in {input_folder}")
            return {"total_pdfs": 0, "total_images": 0, "failed_pdfs": 0}

        print(f"Found {len(pdf_files)} PDF files to process.\n")

        stats = {
            "total_pdfs": len(pdf_files),
            "total_images": 0,
            "failed_pdfs": 0,
            "processed_files": []
        }

        # Process each PDF
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                # Create output folder for this PDF
                pdf_name = pdf_path.stem
                output_folder = os.path.join(output_base_folder, pdf_name)

                print(f"\nProcessing: {pdf_path.name}")

                # Extract images
                saved_images = self.extract_images_from_pdf(str(pdf_path), output_folder)

                stats["total_images"] += len(saved_images)
                stats["processed_files"].append({
                    "pdf": pdf_path.name,
                    "images": len(saved_images),
                    "output_folder": output_folder
                })

                print(f"  Extracted {len(saved_images)} images to: {output_folder}")

            except Exception as e:
                print(f"  Error processing {pdf_path.name}: {str(e)}")
                stats["failed_pdfs"] += 1

        return stats


def main():
    """Main entry point for the PDF image extractor."""
    parser = argparse.ArgumentParser(
        description="Extract images from PDF files with batch processing support.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract embedded images from PDFs
  python pdf_image_extractor.py -i document.pdf -o output_images

  # Batch process all PDFs in a folder
  python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch

  # Render image regions only (screenshot mode - preserves text perfectly)
  python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch --render

  # Render image regions with high DPI for better quality
  python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch --render --dpi 600

  # Use Claude AI for image quality detection
  python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch --use-claude

  # Set minimum image size (only for embedded mode, not render mode)
  python pdf_image_extractor.py -i pdfs_folder -o extracted_images --batch --min-size 50000
        """
    )

    parser.add_argument('-i', '--input', required=True,
                        help='Input PDF file or folder containing PDFs')
    parser.add_argument('-o', '--output', required=True,
                        help='Output folder for extracted images')
    parser.add_argument('--batch', action='store_true',
                        help='Enable batch processing mode (process folder of PDFs)')
    parser.add_argument('--render', action='store_true',
                        help='Render only image regions (screenshot mode). Detects images and captures just those areas, preserving text perfectly.')
    parser.add_argument('--dpi', type=int, default=300,
                        help='DPI for page rendering (only used with --render, default: 300)')
    parser.add_argument('--use-claude', action='store_true',
                        help='Use Claude AI for image quality detection')
    parser.add_argument('--min-size', type=int, default=10000,
                        help='Minimum image size in bytes (only applies to embedded extraction, default: 10000)')

    args = parser.parse_args()

    # Initialize extractor
    extractor = PDFImageExtractor(
        use_claude=args.use_claude,
        min_image_size=args.min_size,
        render_mode=args.render,
        dpi=args.dpi
    )

    # Display mode information
    if args.render:
        print(f"Mode: Image Region Rendering (Screenshot mode) at {args.dpi} DPI")
        print("Detects images and renders only those regions, preserving text perfectly.\n")
    else:
        print(f"Mode: Embedded Image Extraction (min size: {args.min_size} bytes)\n")

    # Process based on mode
    if args.batch:
        # Batch processing mode
        if not os.path.isdir(args.input):
            print(f"Error: Input path '{args.input}' is not a directory.")
            sys.exit(1)

        stats = extractor.batch_process(args.input, args.output)

        # Print summary
        print("\n" + "="*60)
        print("EXTRACTION COMPLETE")
        print("="*60)
        print(f"Total PDFs processed: {stats['total_pdfs']}")
        print(f"Total images extracted: {stats['total_images']}")
        print(f"Failed PDFs: {stats['failed_pdfs']}")
        print("\nDetails:")
        for file_info in stats['processed_files']:
            print(f"  {file_info['pdf']}: {file_info['images']} images -> {file_info['output_folder']}")

    else:
        # Single file mode
        if not os.path.isfile(args.input):
            print(f"Error: Input file '{args.input}' does not exist.")
            sys.exit(1)

        pdf_name = Path(args.input).stem
        output_folder = os.path.join(args.output, pdf_name)

        print(f"Processing: {args.input}")
        saved_images = extractor.extract_images_from_pdf(args.input, output_folder)

        print(f"\nExtracted {len(saved_images)} images to: {output_folder}")


if __name__ == "__main__":
    main()
