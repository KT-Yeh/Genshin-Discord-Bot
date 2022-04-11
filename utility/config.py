import json
from pathlib import Path

class Config:
    def __init__(self):
        project_path = Path(__file__).parents[1]
        config_path = project_path.joinpath('config.json') 
        with open(config_path, encoding='utf-8') as file:
            data = json.loads(file.read())
        
        self.application_id = data['application_id']
        self.bot_token = data['bot_token']
        self.bot_prefix = data['bot_prefix']
        self.bot_cooldown = data['bot_cooldown']
        self.auto_daily_reward_time = data['auto_daily_reward_time']
        self.auto_check_resin_threshold = data['auto_check_resin_threshold']

config = Config()