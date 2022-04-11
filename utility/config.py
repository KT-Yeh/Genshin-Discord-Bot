import json
from pathlib import Path

class Config:
    def __init__(self):
        project_path = Path(__file__).parents[1]
        config_path = project_path.joinpath('config.json') 
        with open(config_path, encoding='utf-8') as file:
            data: dict = json.loads(file.read())
        
        self.application_id = data.get('application_id')
        self.test_server_id = data.get('test_server_id')
        self.bot_token = data.get('bot_token')
        self.bot_prefix = data.get('bot_prefix')
        self.bot_cooldown = data.get('bot_cooldown')
        self.auto_daily_reward_time = data.get('auto_daily_reward_time')
        self.auto_check_resin_threshold = data.get('auto_check_resin_threshold')

config = Config()