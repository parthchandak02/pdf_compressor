"""
PDF Compressor - A tool for extreme PDF compression while maintaining readability.

This module provides functionality to compress PDF files while maintaining
high quality for important pages (e.g., first few pages) and applying more
aggressive compression to the rest.
"""

import os
import subprocess
import tempfile
from typing import List, Optional, Tuple
from PyPDF2 import PdfReader, PdfWriter
import img2pdf
from PIL import Image

class CompressionError(Exception):
    """Custom exception for compression-related errors."""
    pass

def check_dependencies() -> bool:
    """
    Check if required system dependencies (ImageMagick) are installed.

    Returns:
        bool: True if all dependencies are found, False otherwise
    """
    try:
        subprocess.run(['magick', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def compress_image(image_path: str, quality: int = 60, optimize: bool = True) -> None:
    """
    Compress a JPEG image with the specified quality settings.

    Args:
        image_path: Path to the image file
        quality: JPEG quality (1-100)
        optimize: Whether to apply additional JPEG optimization
    """
    try:
        img = Image.open(image_path)
        img.save(image_path, 'JPEG', quality=quality, optimize=optimize)
    except Exception as e:
        raise CompressionError(f"Failed to compress image {image_path}: {str(e)}")

def convert_pdf_to_images(
    input_path: str,
    output_dir: str,
    start_page: int = 0,
    end_page: Optional[int] = None,
    dpi: int = 72,
    quality: int = 60
) -> List[str]:
    """
    Convert PDF pages to images using ImageMagick.

    Args:
        input_path: Path to input PDF file
        output_dir: Directory to save the converted images
        start_page: First page to convert (0-based)
        end_page: Last page to convert (None means all pages)
        dpi: Resolution in dots per inch
        quality: JPEG quality (1-100)

    Returns:
        List[str]: List of paths to the converted images
    """
    reader = PdfReader(input_path)
    if end_page is None:
        end_page = len(reader.pages)

    images = []
    for i in range(start_page, end_page):
        output_image = os.path.join(output_dir, f'page_{i}.jpg')

        cmd = [
            'magick',
            '-density', str(dpi),
            '-quality', str(quality),
            '-compress', 'JPEG',
            f'{input_path}[{i}]',
            '-background', 'white',
            '-alpha', 'remove',
            '-alpha', 'off',
            output_image
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            if os.path.exists(output_image):
                compress_image(output_image, quality=quality)
                images.append(output_image)
        except subprocess.SubprocessError as e:
            raise CompressionError(f"Failed to convert page {i}: {str(e)}")

    return images

def compress_pdf(
    input_path: str,
    output_path: str,
    target_size_mb: float = 4.5,
    important_pages: int = 5,
    first_page_quality: int = 85,
    remaining_quality: int = 25,
    first_page_dpi: int = 200,
    remaining_dpi: int = 35
) -> Tuple[bool, float]:
    """
    Compress a PDF file while maintaining quality for important pages.

    Args:
        input_path: Path to input PDF file
        output_path: Path to save the compressed PDF
        target_size_mb: Target file size in megabytes
        important_pages: Number of pages to maintain higher quality
        first_page_quality: JPEG quality for important pages (1-100)
        remaining_quality: JPEG quality for remaining pages (1-100)
        first_page_dpi: DPI for important pages
        remaining_dpi: DPI for remaining pages

    Returns:
        Tuple[bool, float]: (Success status, Final file size in MB)
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not check_dependencies():
        raise CompressionError("ImageMagick is not installed. Please install it first.")

    print("Starting compression process...")

    with tempfile.TemporaryDirectory() as temp_dir:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        # Convert and compress important pages
        print(f"\nProcessing first {important_pages} pages with higher quality...")
        first_pages = convert_pdf_to_images(
            input_path, temp_dir,
            start_page=0,
            end_page=min(important_pages, total_pages),
            dpi=first_page_dpi,
            quality=first_page_quality
        )

        # Convert and compress remaining pages
        print("Processing remaining pages with extreme compression...")
        remaining_pages = convert_pdf_to_images(
            input_path, temp_dir,
            start_page=important_pages,
            end_page=total_pages,
            dpi=remaining_dpi,
            quality=remaining_quality
        )

        # Combine all images into PDF
        print("\nConverting compressed images back to PDF...")
        all_images = first_pages + remaining_pages

        if not all_images:
            raise CompressionError("No images were created during conversion")

        with open(output_path, 'wb') as f:
            f.write(img2pdf.convert(all_images))

        # Check final size
        final_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\nFinal PDF size: {final_size:.2f}MB")

        if final_size <= target_size_mb:
            print(f"Successfully compressed PDF to {final_size:.2f}MB")
            return True, final_size

        # Try one final time with most extreme settings
        print("\nAttempting final compression with most aggressive settings...")
        extreme_images = []

        for img_path in all_images:
            output = os.path.join(temp_dir, f'extreme_{os.path.basename(img_path)}')
            compress_image(img_path, quality=15, optimize=True)
            extreme_images.append(img_path)

        with open(output_path, 'wb') as f:
            f.write(img2pdf.convert(extreme_images))

        final_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Final PDF size after extreme compression: {final_size:.2f}MB")
        return final_size <= target_size_mb, final_size
