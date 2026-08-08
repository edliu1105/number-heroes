# -*- coding: utf-8 -*-
"""Generate QR code PNG for the deployed URL (for iPad camera scanning)."""
import sys, os
import qrcode

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def main(url):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=14, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1c2b46", back_color="white")
    out = os.path.join(ROOT, "review", "qr-shuzi-xiaoyingxiong.png")
    img.save(out)
    print("QR saved:", out, "->", url)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "https://example.com")
