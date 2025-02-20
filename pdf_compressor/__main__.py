#!/usr/bin/env python3
"""
Command-line interface for the PDF Compressor.
"""

import argparse
import sys
from . import compress_pdf, CompressionError

def main():
    parser = argparse.ArgumentParser(
        description="Compress PDF files while maintaining quality for important pages."
    )
    parser.add_argument(
        "input_file",
        help="Path to the input PDF file"
    )
    parser.add_argument(
        "output_file",
        help="Path to save the compressed PDF"
    )
    parser.add_argument(
        "-t", "--target-size",
        type=float,
        default=4.5,
        help="Target file size in MB (default: 4.5)"
    )
    parser.add_argument(
        "-p", "--important-pages",
        type=int,
        default=5,
        help="Number of pages to maintain higher quality (default: 5)"
    )
    parser.add_argument(
        "--first-quality",
        type=int,
        default=85,
        help="JPEG quality for important pages (1-100, default: 85)"
    )
    parser.add_argument(
        "--remaining-quality",
        type=int,
        default=25,
        help="JPEG quality for remaining pages (1-100, default: 25)"
    )
    parser.add_argument(
        "--first-dpi",
        type=int,
        default=200,
        help="DPI for important pages (default: 200)"
    )
    parser.add_argument(
        "--remaining-dpi",
        type=int,
        default=35,
        help="DPI for remaining pages (default: 35)"
    )

    args = parser.parse_args()

    try:
        success, final_size = compress_pdf(
            args.input_file,
            args.output_file,
            target_size_mb=args.target_size,
            important_pages=args.important_pages,
            first_page_quality=args.first_quality,
            remaining_quality=args.remaining_quality,
            first_page_dpi=args.first_dpi,
            remaining_dpi=args.remaining_dpi
        )

        if not success:
            print(f"\nWarning: Could not reach target size of {args.target_size}MB")
            print(f"Final size: {final_size:.2f}MB")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except CompressionError as e:
        print(f"Compression Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
