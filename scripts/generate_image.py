"""Generates a branded quote-card PNG from a post's text, so every LinkedIn
post can carry an image without any hand-picked artwork or paid image API.

Style: a gradient background with soft blurred accent shapes, and a white
"elevated" card (drop shadow) holding the text -- gives a modern, layered
look using only Pillow (no 3D renderer / paid image API involved).
"""

import hashlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CANVAS_SIZE = (1080, 1080)
MARGIN = 64
CARD_RADIUS = 36
CARD_COLOR = (255, 255, 255)
TEXT_COLOR = (29, 34, 38)

# Rotate through a few gradient themes, picked deterministically from the
# post text so re-runs (e.g. workflow retries) render the same card.
THEMES = [
    {"top": "#0A2540", "bottom": "#0A66C2", "accent": "#4DA3FF"},
    {"top": "#2B0B3F", "bottom": "#7B2FBE", "accent": "#D896FF"},
    {"top": "#1B1B1B", "bottom": "#3A3A3A", "accent": "#F5C518"},
    {"top": "#00332E", "bottom": "#00796B", "accent": "#4DE8CF"},
]

FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONT_REGULAR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _pick_theme(text: str) -> dict:
    index = int(hashlib.sha256(text.encode()).hexdigest(), 16) % len(THEMES)
    return THEMES[index]


def _vertical_gradient(size: tuple[int, int], top_hex: str, bottom_hex: str) -> Image.Image:
    width, height = size
    top = _hex_to_rgb(top_hex)
    bottom = _hex_to_rgb(bottom_hex)
    column = Image.new("RGB", (1, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        column.putpixel((0, y), tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3)))
    return column.resize((width, height))


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
    theme = _pick_theme(text)

    background = _vertical_gradient(CANVAS_SIZE, theme["top"], theme["bottom"]).convert("RGBA")

    # Soft blurred accent shapes for visual depth.
    decor = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    decor_draw = ImageDraw.Draw(decor)
    decor_draw.ellipse([-220, -260, 480, 420], fill=theme["accent"] + "50")
    decor_draw.ellipse([720, 760, 1320, 1360], fill="#FFFFFF26")
    decor = decor.filter(ImageFilter.GaussianBlur(90))
    background = Image.alpha_composite(background, decor)

    card_box = (MARGIN, 168, CANVAS_SIZE[0] - MARGIN, CANVAS_SIZE[1] - 140)

    # Drop shadow behind the card, for an elevated/layered look.
    shadow = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_offset = 22
    shadow_draw.rounded_rectangle(
        (card_box[0], card_box[1] + shadow_offset, card_box[2], card_box[3] + shadow_offset),
        radius=CARD_RADIUS,
        fill=(0, 0, 0, 130),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    background = Image.alpha_composite(background, shadow)

    # The card itself, opaque and crisp on top of the shadow.
    card_layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    ImageDraw.Draw(card_layer).rounded_rectangle(card_box, radius=CARD_RADIUS, fill=CARD_COLOR)
    background = Image.alpha_composite(background, card_layer)

    image = background.convert("RGB")
    draw = ImageDraw.Draw(image)

    # Label above the card.
    label_font = _load_font(FONT_BOLD_CANDIDATES, 34)
    label = "FRONTEND DEV TIP"
    label_width = draw.textlength(label, font=label_font)
    draw.text(((CANVAS_SIZE[0] - label_width) / 2, 72), label, font=label_font, fill="#FFFFFF")
    underline_width = 90
    draw.rounded_rectangle(
        (
            (CANVAS_SIZE[0] - underline_width) / 2,
            124,
            (CANVAS_SIZE[0] + underline_width) / 2,
            130,
        ),
        radius=3,
        fill=theme["accent"],
    )

    # Large decorative quote mark in the corner of the card.
    quote_font = _load_font(FONT_BOLD_CANDIDATES, 180)
    accent_rgb = _hex_to_rgb(theme["accent"])
    draw.text((card_box[0] + 34, card_box[1] - 60), "“", font=quote_font, fill=accent_rgb + (60,))

    # Body text, centered vertically inside the card.
    inner_margin = 76
    max_width = (card_box[2] - card_box[0]) - 2 * inner_margin
    body_font = _load_font(FONT_BOLD_CANDIDATES, 46)
    lines = _wrap_text(draw, text, body_font, max_width)
    line_height = body_font.getbbox("Ag")[3] + 20
    total_height = line_height * len(lines)
    card_height = card_box[3] - card_box[1]
    start_y = card_box[1] + max(90, (card_height - total_height) // 2)
    start_x = card_box[0] + inner_margin

    for i, line in enumerate(lines):
        draw.text((start_x, start_y + i * line_height), line, font=body_font, fill=TEXT_COLOR)

    # Small accent bar under the text, echoing the top underline.
    bar_y = card_box[3] - 46
    draw.rounded_rectangle((start_x, bar_y, start_x + 70, bar_y + 6), radius=3, fill=theme["accent"])

    image.save(output_path, "PNG")


if __name__ == "__main__":
    generate_post_image(
        "Example post text to preview the generated LinkedIn image card.",
        "preview.png",
    )
