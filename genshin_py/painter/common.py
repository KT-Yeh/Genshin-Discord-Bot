from PIL import Image, ImageDraw, ImageFont


def draw_avatar(img: Image.Image, avatar: Image.Image, pos: tuple[int, int]):
    """以圓形畫個人頭像"""
    mask = Image.new("L", avatar.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(((0, 0), avatar.size), fill=255)
    img.paste(avatar, pos, mask=mask)


def draw_text(
    img: Image.Image,
    pos: tuple[float, float],
    text: str,
    font_name: str,
    size: int,
    fill,
    anchor=None,
):
    """在圖片上印文字"""
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(f"data/font/{font_name}", size)  # type: ignore
    draw.text(pos, text, fill, font, anchor=anchor)
