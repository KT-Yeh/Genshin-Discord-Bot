import genshin
import random
from urllib import request
from PIL import Image, ImageFont, ImageDraw
from typing import Tuple, Sequence, Optional, List
from io import BytesIO
from pathlib import Path
from utility.utils import getServerName

def drawAvatar(img: Image.Image, avatar: Image.Image, pos: Tuple[float, float]):
    """以圓形畫個人頭像"""
    mask = Image.new('L', avatar.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(((0, 0), avatar.size), fill=255)
    img.paste(avatar, pos, mask=mask)

def drawRoundedRect(img: Image.Image, pos: Tuple[float, float, float, float], **kwargs):
    """畫半透明圓角矩形"""
    transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(transparent, 'RGBA')
    draw.rounded_rectangle(pos, **kwargs)
    img.paste(Image.alpha_composite(img, transparent))

def drawText(img: Image.Image, pos: Tuple[float, float], text: str, font: str, size: int, fill, anchor = None):
    """在圖片上印文字"""
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(f'data/font/{font}', size)
    draw.text(pos, text, fill, font, anchor=anchor)

def drawBasicCard(avatar_bytes: bytes, uid: int, user_stats: genshin.models.PartialGenshinUserStats) -> Image.Image:
    img: Image.Image = Image.open(f'data/image/record_card/{random.randint(1, 12)}.jpg')
    img = img.convert('RGBA')

    avatar: Image.Image = Image.open(BytesIO(avatar_bytes)).resize((250, 250))
    drawAvatar(img, avatar, (70, 210))

    drawRoundedRect(img, (340, 270, 990, 460), radius=30, fill=(0, 0, 0, 120))
    drawRoundedRect(img, (90, 520, 990, 1730), radius=30, fill=(0, 0, 0, 120))
    
    info = user_stats.info
    drawText(img, (665, 335), info.nickname, 'SourceHanSerifTC-Bold.otf', 88, (255, 255, 255, 255), 'mm')
    drawText(img, (665, 415), f'{getServerName(info.server)}  Lv.{info.level}  UID:{uid}', 'SourceHanSansTC-Medium.otf', 40, (255, 255, 255, 255), 'mm')

    return img

def drawRecordCard(avatar_bytes: bytes, uid: int, user_stats: genshin.models.PartialGenshinUserStats) -> BytesIO:
    """製作個人紀錄卡片圖

    ------
    Parameters
    avatar_bytes `bytes`: Discord使用者的頭像圖片，以bytes方式傳入
    uid `int`: 原神角色UID
    user_stats `PartialGenshinUserStats`: 從Hoyolab取得的使用者遊戲紀錄
    ------
    Returns
    `BytesIO`: 製作完成的圖片存在記憶體，回傳file pointer，存取前需要先`seek(0)`
    """
    img = drawBasicCard(avatar_bytes, uid, user_stats)
    
    white = (255, 255, 255, 255)
    grey = (230, 230, 230, 255)
    
    s = user_stats.stats
    stat_list = [(s.days_active, '活躍天數'), (s.achievements, '成就達成數'), (s.characters, '獲得角色數'),
                (s.anemoculi, '風神瞳'), (s.geoculi, '岩神瞳'), (s.electroculi, '雷神瞳'), (s.dendroculi, '草神瞳'),
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

def drawExplorationCard(avatar_bytes: bytes, uid: int, user_stats: genshin.models.PartialGenshinUserStats) -> BytesIO:
    """製作個人世界探索度卡片圖

    ------
    Parameters
    avatar_bytes `bytes`: Discord使用者的頭像圖片，以bytes方式傳入
    uid `int`: 原神角色UID
    user_stats `PartialGenshinUserStats`: 從Hoyolab取得的使用者遊戲紀錄
    ------
    Returns
    `BytesIO`: 製作完成的圖片存在記憶體，回傳file pointer，存取前需要先`seek(0)`
    """
    img = drawBasicCard(avatar_bytes, uid, user_stats)

    white = (255, 255, 255, 255)
    grey = (230, 230, 230, 255)

    explored_list = [
        ['蒙德', 0], ['璃月', 0], ['雪山', 0], ['稻妻', 0],
        ['淵下宮', 0], ['層岩·表', 0], ['層岩·底', 0], ['須彌', 0]
    ]
    offering_list = [
        ['忍冬之樹', 0], ['神櫻眷顧', 0], ['流明石', 0], ['夢之樹', 0]
    ]
    for e in user_stats.explorations:
        explored_list[e.id - 1][1] = e.explored

        if e.id == 3 and len(e.offerings) >= 1:
            offering_list[0][1] = e.offerings[0].level
        if e.id == 4 and len(e.offerings) >= 2:
            offering_list[1][1] = e.offerings[0].level
        if e.id == 6 and len(e.offerings) >= 1:
            offering_list[2][1] = e.offerings[0].level
        if e.id == 8 and len(e.offerings) >= 2:
            offering_list[3][1] = e.offerings[0].level
    
    stat_list: List[Tuple[str, float, str]] = []
    for e in explored_list:
        stat_list.append(('探索', e[1], e[0]))
    for o in offering_list:
        stat_list.append(('等級', o[1], o[0]))

    for n, stat in enumerate(stat_list):
        column = int(n % 3)
        row = int(n / 3)
        drawText(img, (245 + column * 295, 620 + row * 270), stat[0], 'SourceHanSansTC-Regular.otf', 41, grey, 'mm')
        drawText(img, (245 + column * 295, 691 + row * 270), f"{stat[1]:g}", 'SourceHanSansTC-Bold.otf', 82, white, 'mm')
        drawText(img, (245 + column * 295, 770 + row * 270), stat[2], 'SourceHanSansTC-Regular.otf', 45, grey, 'mm')

    img = img.convert('RGB')
    fp = BytesIO()
    img.save(fp, 'jpeg', optimize=True, quality=50)
    return fp

def drawCharacter(img: Image.Image, character: genshin.models.AbyssCharacter, size: Tuple[int, int], pos: Tuple[float, float]):
    """畫角色頭像，包含背景框
    
    ------
    Parameters
    character `AbyssCharacter`: 角色資料
    size `Tuple[int, int]`: 背景框大小
    pos `Tuple[float, float]`: 要畫的左上角位置
    """
    background = Image.open(f'data/image/character/char_{character.rarity}star_bg.png').convert('RGBA').resize(size)
    avatar_file = Path(f'data/image/character/{character.id}.png')
    # 若本地沒有圖檔則從URL下載
    if avatar_file.exists() == False:
        request.urlretrieve(character.icon, f'data/image/character/{character.id}.png')
    avatar = Image.open(avatar_file).resize((size[0], size[0]))
    img.paste(background, pos, background)
    img.paste(avatar, pos, avatar)

def drawAbyssStar(img: Image.Image, number: int, size: Tuple[int, int], pos: Tuple[float, float]):
    """畫深淵星星數量
    
    ------
    Parameters
    number `int`: 星星數量
    size `Tuple[int, int]`: 單顆星星大小
    pos `Tuple[float, float]`: 正中央位置，星星會自動置中
    """
    star = Image.open(f'data/image/spiral_abyss/star.png').convert('RGBA').resize(size)
    pad = 5
    upper_left = (pos[0] - number / 2 * size[0] - (number - 1) * pad, pos[1] - size[1] / 2)
    for i in range(0, number):
        img.paste(star, (int(upper_left[0] + i * (size[0] + 2 * pad)), int(upper_left[1])), star)

def drawAbyssCard(abyss_floor: genshin.models.Floor, characters: Optional[Sequence[genshin.models.PartialCharacter]] = None) -> BytesIO:
    """繪製深淵樓層紀錄圖，包含每一間星數以及上下半所使用的角色和等級

    ------
    Parameters
    abyss_floor `Floor`: 深境螺旋某一樓層的資料
    characters `Sequence[Character]`: 玩家的角色資料
    ------
    Returns
    `BytesIO`: 製作完成的圖片存在記憶體，回傳file pointer，存取前需要先`seek(0)`
    """
    img = Image.open('data/image/spiral_abyss/background_blur.jpg')
    img = img.convert('RGBA')
    
    character_size = (172, 210)
    character_pad = 8
    # 顯示第幾層深淵
    drawText(img, (1050, 145), f'{abyss_floor.floor}', 'SourceHanSansTC-Bold.otf', 85, (50, 50, 50), 'mm')
    # 繪製每一間
    for i, chamber in enumerate(abyss_floor.chambers):
        # 顯示此間星星數
        drawAbyssStar(img, chamber.stars, (70, 70), (1050, 500 + i * 400))
        # 上下半間
        for j, battle in enumerate(chamber.battles):
            middle = 453 + j * 1196
            left_upper = (int(middle - len(battle.characters) / 2 * character_size[0] - (len(battle.characters) - 1) * character_pad), 395 + i * 400)
            for k, character in enumerate(battle.characters):
                x = left_upper[0] + k * (character_size[0] + 2 * character_pad)
                y = left_upper[1]
                drawCharacter(img, character, (172, 210), (x, y))
                if characters != None:
                    constellation = next((c.constellation for c in characters if c.id == character.id), 0) # 匹配角色ID並取得命座
                    text = f'{constellation}命 {character.level}級'
                else:
                    text = f'{character.level}級'
                drawText(img, (x + character_size[0] / 2, y + character_size[1] * 0.90), text, 'SourceHanSansTC-Regular.otf', 30, (50, 50, 50), 'mm')
    img = img.convert('RGB')
    fp = BytesIO()
    img.save(fp, 'jpeg', optimize=True, quality=40)
    return fp