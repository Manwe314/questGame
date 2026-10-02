#!/usr/bin/env python3
"""Create a printable PNG QR code for an HTTP(S) website."""

import argparse
import sys
from pathlib import Path
from urllib.parse import urlsplit


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Full website URL, including https://")
    parser.add_argument("-o", "--output", type=Path, default=Path(__file__).resolve().parent / "qr" / "questGame.png")
    args = parser.parse_args()
    url = args.url.strip()
    try:
        parsed = urlsplit(url)
        valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not any(c.isspace() for c in url)
    except ValueError:
        valid = False
    if not valid:
        parser.error("Enter a full HTTP(S) URL, for example https://manwe314.github.io/questGame/")
    if args.output.suffix.lower() != ".png":
        parser.error("The output filename must end with .png")
    try:
        import qrcode
    except ImportError:
        parser.exit(1, "Install dependencies first: python -m pip install -r requirements.txt\n")
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    try:
        qr.add_data(url)
        qr.make(fit=True)
    except qrcode.exceptions.DataOverflowError:
        parser.error("This URL is too long for a QR code")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    qr.make_image(fill_color="black", back_color="white").save(args.output, format="PNG")
    print(f"Created: {args.output.resolve()}\nURL: {url}")


if __name__ == "__main__":
    main()
