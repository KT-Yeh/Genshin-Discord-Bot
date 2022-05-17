from pathlib import Path
from pydantic import BaseModel

class Config(BaseModel):
    application_id: int
    test_server_id: int
    bot_token: str
    auto_daily_reward_time: int = 8
    auto_check_resin_threshold: int = 145
    auto_loop_delay: float = 2.0
    slash_cmd_cooldown: float = 5.0

config = Config.parse_file(Path('config.json'), encoding='utf8')