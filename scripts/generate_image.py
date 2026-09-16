"""Generates a branded quote-card PNG from a post's text, so every LinkedIn
post can carry an image without any hand-picked artwork or paid image API.
"""

import hashlib

from PIL import Image, ImageDraw, ImageFont

CANVAS_SIZE = (1080, 1080)
MARGIN = 90

# Rotate through a few high-contrast color pairs so posts don't all look
# identical; picked deterministically from the post text so re-runs (e.g.
# workflow retries) render the same card.
PALETTE = [
    ("#0A66C2", "#FFFFFF"),  # LinkedIn blue
    ("#1D2226", "#FFFFFF"),  # near-black
    ("#004182", "#FFFFFF"),  # deep blue
    ("#2E2E2E", "#F5C518"),  # charcoal + amber accent
]

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _pick_colors(text: str) -> tuple[str, str]:
    index = int(hashlib.sha256(text.encode()).hexdigest(), 16) % len(PALETTE)
    return PALETTE[index]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_post_image(text: str, output_path: str) -> None:
    bg_color, fg_color = _pick_colors(text)
    image = Image.new("RGB", CANVAS_SIZE, bg_color)
    draw = ImageDraw.Draw(image)

    max_width = CANVAS_SIZE[0] - 2 * MARGIN

    label_font = _load_font(38)
    body_font = _load_font(52)

    draw.text((MARGIN, MARGIN), "FRONTEND DEV TIP", font=label_font, fill=fg_color)
    draw.line((MARGIN, MARGIN + 60, MARGIN + 140, MARGIN + 60), fill=fg_color, width=4)

    body_lines = _wrap_text(draw, text, body_font, max_width)
    line_height = body_font.getbbox("Ag")[3] + 22
    total_height = line_height * len(body_lines)
    start_y = max(MARGIN + 140, (CANVAS_SIZE[1] - total_height) // 2)

    for i, line in enumerate(body_lines):
        draw.text((MARGIN, start_y + i * line_height), line, font=body_font, fill=fg_color)

    image.save(output_path, "PNG")


if __name__ == "__main__":
    generate_post_image(
        "Example post text to preview the generated LinkedIn image card.",
        "preview.png",
    )
