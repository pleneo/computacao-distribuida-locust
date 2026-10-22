#!/usr/bin/env python3
"""
Gera os artefatos de teste exigidos pelos 3 cenários do Trabalho 3:
1. Post com imagem de aproximadamente 1MB (assets/img_1mb.bmp e assets/post1_1mb.html)
2. Post com texto de aproximadamente 400KB (assets/texto_400kb.html)
3. Post com imagem de aproximadamente 300KB (assets/img_300kb.bmp e assets/post3_300kb.html)

As imagens também são embutidas em base64 no HTML dos posts 1 e 3 para garantir que o
Locust (que não interpreta tags <img> externas como um navegador) transfira exatamente ~1MB
e ~300KB ao fazer GET em /?p=1 e /?p=3.
"""

import base64
import os
import struct

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def build_bmp_bytes(width: int, height: int, color_rgb=(66, 135, 245)) -> bytes:
    """Constrói os bytes de uma imagem BMP 24-bit válida (~width * height * 3 bytes)."""
    row_padding = (4 - (width * 3) % 4) % 4
    row_size = width * 3 + row_padding
    pixel_data_size = row_size * height
    file_size = 54 + pixel_data_size

    bmp_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
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
    return bmp_header + dib_header + (row_bytes * height)


def create_bmp_image(filepath: str, width: int, height: int, color_rgb=(66, 135, 245)):
    bmp_data = build_bmp_bytes(width, height, color_rgb)
    with open(filepath, "wb") as f:
        f.write(bmp_data)
    actual_kb = os.path.getsize(filepath) / 1024
    print(f"[OK] Imagem gerada: {filepath} ({actual_kb:.1f} KB)")


def create_image_post_html(filepath: str, target_total_kb: int, title: str, color_rgb=(66, 135, 245)):
    """
    Gera um post HTML contendo uma imagem BMP embutida cujo payload total de resposta HTTP
    seja de aproximadamente target_total_kb KB.
    Como Base64 expande os bytes em 4/3, geramos um BMP de ~(target_total_kb * 3/4) KB.
    """
    raw_target_bytes = int(target_total_kb * 1024 * 0.74)
    side = int((raw_target_bytes / 3) ** 0.5)
    bmp_data = build_bmp_bytes(side, side, color_rgb)
    b64_str = base64.b64encode(bmp_data).decode("ascii")

    html = (
        f"<h2>{title}</h2>\n"
        f"<p>Post de teste de carga com imagem embutida (~{target_total_kb} KB).</p>\n"
        f'<p><img src="data:image/bmp;base64,{b64_str}" alt="{title}" style="max-width:100%;height:auto;" /></p>\n'
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    actual_kb = os.path.getsize(filepath) / 1024
    print(f"[OK] Post HTML com imagem gerado: {filepath} ({actual_kb:.1f} KB)")


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

    # 1. Cenário 1: Imagem de ~1MB
    create_bmp_image(os.path.join(ASSETS_DIR, "img_1mb.bmp"), width=590, height=590, color_rgb=(52, 152, 219))
    create_image_post_html(
        os.path.join(ASSETS_DIR, "post1_1mb.html"),
        target_total_kb=1000,
        title="Cenário 1: Blog Post com Imagem de ~1MB",
        color_rgb=(52, 152, 219),
    )

    # 2. Cenário 2: Texto de ~400KB
    create_text_file(os.path.join(ASSETS_DIR, "texto_400kb.html"), target_kb=400)

    # 3. Cenário 3: Imagem de ~300KB
    create_bmp_image(os.path.join(ASSETS_DIR, "img_300kb.bmp"), width=320, height=320, color_rgb=(46, 204, 113))
    create_image_post_html(
        os.path.join(ASSETS_DIR, "post3_300kb.html"),
        target_total_kb=300,
        title="Cenário 3: Blog Post com Imagem de ~300KB",
        color_rgb=(46, 204, 113),
    )


if __name__ == "__main__":
    main()
