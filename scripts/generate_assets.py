#!/usr/bin/env python3
"""
Gera os artefatos de teste exigidos pelos 3 cenários do Trabalho 3:
1. Imagem de aproximadamente 1MB (assets/img_1mb.bmp)
2. Texto de aproximadamente 400KB (assets/texto_400kb.html)
3. Imagem de aproximadamente 300KB (assets/img_300kb.bmp)

Não requer bibliotecas externas (usa apenas a biblioteca padrão do Python).
"""

import os
import struct

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def create_bmp_image(filepath: str, width: int, height: int, color_rgb=(66, 135, 245)):
    """Gera uma imagem BMP 24-bit válida com tamanho determinístico (~width * height * 3 bytes)."""
    row_padding = (4 - (width * 3) % 4) % 4
    row_size = width * 3 + row_padding
    pixel_data_size = row_size * height
    file_size = 54 + pixel_data_size

    # Cabeçalho BMP (14 bytes) + DIB Header BITMAPINFOHEADER (40 bytes)
    bmp_header = struct.pack(
        "<2sIHHI",
        b"BM",
        file_size,
        0,
        0,
        54,
    )
    dib_header = struct.pack(
        "<IiiHHIIiiII",
        40,
        width,
        height,
        1,
        24,
        0,
        pixel_data_size,
        2835,
        2835,
        0,
        0,
    )

    r, g, b = color_rgb
    pixel_bgr = bytes([b, g, r])
    row_bytes = pixel_bgr * width + (b"\x00" * row_padding)

    with open(filepath, "wb") as f:
        f.write(bmp_header)
        f.write(dib_header)
        for _ in range(height):
            f.write(row_bytes)

    actual_kb = os.path.getsize(filepath) / 1024
    print(f"[OK] Imagem gerada: {filepath} ({actual_kb:.1f} KB)")


def create_text_file(filepath: str, target_kb: int = 400):
    """Gera um conteúdo HTML de blog post com aproximadamente target_kb KB."""
    target_bytes = target_kb * 1024
    paragraph = (
        "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
        "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
        "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure "
        "dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. "
        "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
        "mollit anim id est laborum. Computação Distribuída - Teste de Carga com Locust e "
        "múltiplas instâncias do WordPress balanceadas via Nginx.</p>\n"
    )
    repeats = (target_bytes // len(paragraph.encode("utf-8"))) + 1
    content = "<h2>Cenário 2: Blog Post com Texto de ~400KB</h2>\n" + (paragraph * repeats)
    content_bytes = content.encode("utf-8")[:target_bytes]

    with open(filepath, "wb") as f:
        f.write(content_bytes)

    actual_kb = os.path.getsize(filepath) / 1024
    print(f"[OK] Texto gerado:  {filepath} ({actual_kb:.1f} KB)")


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    # 1. Imagem de ~1MB (590 x 590 x 3 bytes ≈ 1.020 KB ≈ 1 MB)
    create_bmp_image(os.path.join(ASSETS_DIR, "img_1mb.bmp"), width=590, height=590, color_rgb=(52, 152, 219))

    # 2. Texto de ~400KB
    create_text_file(os.path.join(ASSETS_DIR, "texto_400kb.html"), target_kb=400)

    # 3. Imagem de ~300KB (320 x 320 x 3 bytes ≈ 300 KB)
    create_bmp_image(os.path.join(ASSETS_DIR, "img_300kb.bmp"), width=320, height=320, color_rgb=(46, 204, 113))


if __name__ == "__main__":
    main()
