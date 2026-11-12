"""Generates a branded quote-card PNG from a post's text, so every LinkedIn
post can carry an image without any hand-picked artwork or paid image API.

Style: one consistent dark gradient background with soft blurred accent
shapes, a dark elevated card (drop shadow, a lighter shade of the same
background tone -- not white) holding the insight, and a plain "Follow Saad
Ali" signature line in a shaded tint of the background color, so every card
reads as the same consistent personal-brand series. Pillow only -- no 3D
renderer / paid image API involved.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CANVAS_SIZE = (1080, 1080)
MARGIN = 64
CARD_RADIUS = 36

FOLLOW_TEXT = "Follow Saad Ali"

# Single fixed theme -- every card uses the same background so the series
# looks consistent instead of jumping between colors post to post.
THEME = {"top": "#0B1220", "bottom": "#15335C", "accent": "#5EA8FF"}

FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
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


def _lighten(rgb: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    """Blends rgb toward white by `amount` (0-1) -- used to derive on-brand
    shades (card color, signature text) from the theme instead of plain
    white/black."""
    return tuple(int(c + (255 - c) * amount) for c in rgb)


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
    accent_rgb = _hex_to_rgb(THEME["accent"])
    bottom_rgb = _hex_to_rgb(THEME["bottom"])
    card_color = _lighten(bottom_rgb, 0.16)  # elevated panel, same tone family -- not white
    text_color = _lighten(bottom_rgb, 0.92)  # near-white but still tinted, for contrast on the dark card
    follow_color = _lighten(bottom_rgb, 0.5)  # shaded tint of the background color itself

    background = _vertical_gradient(CANVAS_SIZE, THEME["top"], THEME["bottom"]).convert("RGBA")

    # Soft blurred accent shapes for visual depth.
    decor = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    decor_draw = ImageDraw.Draw(decor)
    decor_draw.ellipse([-220, -260, 480, 420], fill=THEME["accent"] + "45")
    decor_draw.ellipse([760, 780, 1340, 1360], fill="#FFFFFF1F")
    decor = decor.filter(ImageFilter.GaussianBlur(90))
    background = Image.alpha_composite(background, decor)

    card_box = (MARGIN, 140, CANVAS_SIZE[0] - MARGIN, 860)

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

    # The card itself, opaque and crisp on top of the shadow -- a lighter
    # shade of the same background tone, not white.
    card_layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    ImageDraw.Draw(card_layer).rounded_rectangle(card_box, radius=CARD_RADIUS, fill=card_color)
    background = Image.alpha_composite(background, card_layer)

    image = background.convert("RGB")
    draw = ImageDraw.Draw(image)

    # Large decorative quote mark in the corner of the card.
    quote_font = _load_font(FONT_BOLD_CANDIDATES, 160)
    draw.text((card_box[0] + 34, card_box[1] - 44), "\u201c", font=quote_font, fill=accent_rgb)

    # Body text, centered vertically inside the card.
    inner_margin = 76
    max_width = (card_box[2] - card_box[0]) - 2 * inner_margin
    body_font = _load_font(FONT_BOLD_CANDIDATES, 44)
    lines = _wrap_text(draw, text, body_font, max_width)
    line_height = body_font.getbbox("Ag")[3] + 22
    total_height = line_height * len(lines)
    card_height = card_box[3] - card_box[1]
    start_y = card_box[1] + max(100, (card_height - total_height) // 2)
    start_x = card_box[0] + inner_margin

    for i, line in enumerate(lines):
        draw.text((start_x, start_y + i * line_height), line, font=body_font, fill=text_color)

    # Small accent bar under the text.
    bar_y = card_box[3] - 46
    draw.rounded_rectangle((start_x, bar_y, start_x + 70, bar_y + 6), radius=3, fill=accent_rgb)

    # Signature line below the card -- just "Follow Saad Ali", tinted as a
    # shade of the background color itself (no icon, no contrasting color).
    follow_font = _load_font(FONT_BOLD_CANDIDATES, 38)
    draw.text((MARGIN, 912), FOLLOW_TEXT, font=follow_font, fill=follow_color)

    image.save(output_path, "PNG")


if __name__ == "__main__":
    generate_post_image(
        "Example post text to preview the generated LinkedIn image card.",
        "preview.png",
    )
