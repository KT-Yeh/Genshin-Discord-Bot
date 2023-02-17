"""提供向 genshin-db api 請求的方法、資料解析模型，並將資料組成 discord Embed 格式"""

from .api import API
from .models import *
from .parsers import parse
from .request import *
