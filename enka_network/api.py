from utility import config


class EnkaAPI:
    BASE_URL = "https://enka.network"
    USER_URL = BASE_URL + "/u/" + "{uid}"
    USER_DATA_URL = BASE_URL + "/api/uid/{uid}"

    @classmethod
    def get_user_url(cls, uid: int) -> str:
        return cls.USER_URL.format(uid=uid)

    @classmethod
    def get_user_data_url(cls, uid: int) -> str:
        return cls.USER_DATA_URL.format(uid=uid) + (
            f"?key={config.enka_api_key}" if config.enka_api_key else ""
        )


class EnkaError:
    class GeneralError(Exception):
        message: str = "目前無法從API伺服器取得資料"

        def __str__(self) -> str:
            return self.message

    class Maintenance(GeneralError):
        message = "目前 Enka API 伺服器維護中，無法使用"

    class PlayerNotExist(GeneralError):
        message = "查詢不到 UID，此玩家不存在"

    class RateLimit(GeneralError):
        message = "目前向 Enka API 請求時受到速率限制，請稍後再試"

    class ServerError(GeneralError):
        message = "Enka API 伺服器端發生錯誤，目前無法使用"

    class WrongUIDFormat(GeneralError):
        message = "UID 格式錯誤"
