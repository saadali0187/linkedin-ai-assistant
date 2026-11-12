"""Generates a branded quote-card PNG from a post's text, so every LinkedIn
post can carry an image without any hand-picked artwork or paid image API.

Style: a deep gradient background with soft blurred accent shapes, a small
"kicker" pill labeling the topic, a white elevated card (drop shadow) holding
the insight, and a signature row (initials badge + name + role) so every card
reads as a consistent, personal-brand series rather than a one-off quote
image. Pillow only -- no 3D renderer / paid image API involved.
"""

import hashlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CANVAS_SIZE = (1080, 1080)
MARGIN = 64
CARD_RADIUS = 36
CARD_COLOR = (255, 255, 255)
TEXT_COLOR = (22, 26, 30)
MUTED_TEXT_COLOR = (255, 255, 255, 200)

AUTHOR_NAME = "Saad Ali"
AUTHOR_ROLE = "Frontend Developer"
AUTHOR_INITIALS = "SA"
KICKER_LABEL = "FRONTEND ENGINEERING"

# Deeper, more premium gradient themes than a flat brand blue -- rotate
# deterministically from the post text so re-runs (e.g. workflow retries)
# render the same card.
THEMES = [
    {"top": "#0B1220", "bottom": "#15335C", "accent": "#5EA8FF"},
    {"top": "#1A0B2E", "bottom": "#4A1D6B", "accent": "#C9A6FF"},
    {"top": "#111318", "bottom": "#2B2E36", "accent": "#F2C14E"},
    {"top": "#06211D", "bottom": "#0E4F45", "accent": "#4FE3C6"},
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
    accent_rgb = _hex_to_rgb(theme["accent"])

    background = _vertical_gradient(CANVAS_SIZE, theme["top"], theme["bottom"]).convert("RGBA")

    # Soft blurred accent shapes for visual depth.
    decor = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    decor_draw = ImageDraw.Draw(decor)
    decor_draw.ellipse([-220, -260, 480, 420], fill=theme["accent"] + "45")
    decor_draw.ellipse([760, 780, 1340, 1360], fill="#FFFFFF1F")
    decor = decor.filter(ImageFilter.GaussianBlur(90))
    background = Image.alpha_composite(background, decor)

    draw = ImageDraw.Draw(background)

    # Kicker pill ("FRONTEND ENGINEERING") above the card, for a consistent
    # topic label across the whole series.
    kicker_font = _load_font(FONT_BOLD_CANDIDATES, 28)
    kicker_text = KICKER_LABEL
    kicker_width = draw.textlength(kicker_text, font=kicker_font)
    pill_pad_x, pill_pad_y = 28, 16
    pill_box = (
        MARGIN,
        96,
        MARGIN + kicker_width + 2 * pill_pad_x,
        96 + 28 + 2 * pill_pad_y,
    )
    draw.rounded_rectangle(pill_box, radius=(pill_box[3] - pill_box[1]) // 2, outline=accent_rgb, width=3)
    draw.text((pill_box[0] + pill_pad_x, pill_box[1] + pill_pad_y - 2), kicker_text, font=kicker_font, fill=accent_rgb)

    card_box = (MARGIN, 212, CANVAS_SIZE[0] - MARGIN, 860)

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

    # Large decorative quote mark in the corner of the card.
    quote_font = _load_font(FONT_BOLD_CANDIDATES, 160)
    draw.text((card_box[0] + 34, card_box[1] - 44), "\u201c", font=quote_font, fill=accent_rgb + (70,))

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
        draw.text((start_x, start_y + i * line_height), line, font=body_font, fill=TEXT_COLOR)

    # Small accent bar under the text.
    bar_y = card_box[3] - 46
    draw.rounded_rectangle((start_x, bar_y, start_x + 70, bar_y + 6), radius=3, fill=accent_rgb)

    # Signature row below the card -- initials badge + name + role, so every
    # card in the series reads as the same consistent personal brand.
    badge_center = (MARGIN + 44, 932)
    badge_radius = 44
    draw.ellipse(
        (
            badge_center[0] - badge_radius,
            badge_center[1] - badge_radius,
            badge_center[0] + badge_radius,
            badge_center[1] + badge_radius,
        ),
        fill=accent_rgb,
    )
    initials_font = _load_font(FONT_BOLD_CANDIDATES, 34)
    initials_bbox = draw.textbbox((0, 0), AUTHOR_INITIALS, font=initials_font)
    initials_w = initials_bbox[2] - initials_bbox[0]
    initials_h = initials_bbox[3] - initials_bbox[1]
    draw.text(
        (badge_center[0] - initials_w / 2, badge_center[1] - initials_h / 2 - initials_bbox[1]),
        AUTHOR_INITIALS,
        font=initials_font,
        fill=(20, 20, 20),
    )

    name_font = _load_font(FONT_BOLD_CANDIDATES, 36)
    role_font = _load_font(FONT_REGULAR_CANDIDATES, 28)
    text_x = badge_center[0] + badge_radius + 24
    draw.text((text_x, badge_center[1] - 40), AUTHOR_NAME, font=name_font, fill=(255, 255, 255))
    draw.text((text_x, badge_center[1] + 2), AUTHOR_ROLE, font=role_font, fill=(230, 230, 230))

    image.save(output_path, "PNG")


if __name__ == "__main__":
    generate_post_image(
        "Example post text to preview the generated LinkedIn image card.",
        "preview.png",
    )
