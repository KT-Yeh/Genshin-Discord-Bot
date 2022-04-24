import genshin
import random
from PIL import Image, ImageFont, ImageDraw
from typing import Tuple
from io import BytesIO
from utility.utils import getServerName

def drawAvatar(img: Image.Image, avatar: Image.Image, pos: Tuple[float, float]):
    mask = Image.new('L', avatar.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(((0, 0), avatar.size), fill=255)
    img.paste(avatar, pos, mask=mask)

def drawRoundedRect(img: Image.Image, pos: Tuple[float, float, float, float], **kwargs):
    transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(transparent, 'RGBA')
    draw.rounded_rectangle(pos, **kwargs)
    img.paste(Image.alpha_composite(img, transparent))

def drawText(img: Image.Image, pos: Tuple[float, float], text: str, font: str, size: int, fill, anchor = None):
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(f'data/font/{font}', size)
    draw.text(pos, text, fill, font, anchor=anchor)

def drawRecordCard(avatar_bytes: bytes, record_card: genshin.models.RecordCard, user_stats: genshin.models.PartialGenshinUserStats) -> BytesIO:
    img = Image.open(f'data/record_card/{random.randint(1, 12)}.jpg')
    img = img.convert('RGBA')

    avatar = avatar = Image.open(BytesIO(avatar_bytes)).resize((250, 250))
    drawAvatar(img, avatar, (70, 210))

    drawRoundedRect(img, (340, 270, 990, 460), radius=30, fill=(0, 0, 0, 120))
    drawRoundedRect(img, (90, 520, 990, 1730), radius=30, fill=(0, 0, 0, 120))

    white = (255, 255, 255, 255)
    grey = (230, 230, 230, 255)

    drawText(img, (360, 270), record_card.nickname, 'SourceHanSerifTC-Bold.otf', 88, white)
    drawText(img, (370, 385), f'Lv.{record_card.level}  UID:{record_card.uid}  {getServerName(record_card.server)}', 'SourceHanSansTC-Medium.otf', 40, white)
    
    s = user_stats.stats
    stat_list = [(s.days_active, '活躍天數'), (s.achievements, '成就達成數'), (s.characters, '獲得角色數'),
                (s.anemoculi, '風神瞳'), (s.geoculi, '岩神瞳'), (s.electroculi, '雷神瞳'),
                (s.unlocked_waypoints, '解鎖傳送點'), (s.unlocked_domains, '解鎖秘境'), (s.spiral_abyss, '深境螺旋'),
                (s.luxurious_chests, '華麗的寶箱數'), (s.precious_chests, '珍貴的寶箱數'), (s.exquisite_chests, '精緻的寶箱數'),
                (s.common_chests, '普通的寶箱數'), (s.remarkable_chests, '奇饋寶箱數')]

    for n, stat in enumerate(stat_list):
        column = int(n % 3)
        row = int(n / 3)
        drawText(img, (245 + column * 295, 630 + row * 230), str(stat[0]), 'SourceHanSansTC-Bold.otf', 80, white, 'mm')
        drawText(img, (245 + column * 295, 700 + row * 230), str(stat[1]), 'SourceHanSansTC-Regular.otf', 40, grey, 'mm')

    img = img.convert('RGB')
    fp = BytesIO()
    img.save(fp, 'jpeg', optimize=True, quality=50)
    return fp