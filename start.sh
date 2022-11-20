#!/bin/bash

pid=0

term_handler() {
  if [ "$pid" -ne 0 ]; then
    kill -SIGTERM "$pid"
    wait "$pid"
  fi
  exit 143;
}

trap 'kill ${!}; term_handler' TERM

if [ -z "$APPLICATION_ID" ] || 
   [ -z "$TEST_SERVER_ID" ] || 
   [ -z "$BOT_TOKEN" ]; then
   echo "請確認你有設置 APPLICATION_ID、TEST_SERVER_ID、BOT_TOKEN 等環境變數。"
   exit 1
fi

cat >config.json <<CONFIG_JSON
{
    "application_id": $APPLICATION_ID,
    "test_server_id": $TEST_SERVER_ID,
    "bot_token": "$BOT_TOKEN",
    "schedule_daily_reward_time": ${SCHEDULE_DAILY_REWARD_TIME:=10},
    "schedule_check_resin_interval": ${SCHEDULE_CHECK_RESIN_INTERVAL:=10},
    "schedule_loop_delay": ${SCHEDULE_LOOP_DELAY:=2.0},
    "expired_user_days": ${EXPIRED_USER_DAYS:=30},
    "slash_cmd_cooldown": ${SLASH_CMD_COOLDOWN:=5.0},
    "discord_view_long_timeout": ${DISCORD_VIEW_LONG_TIMEOUT:=1800},
    "discord_view_short_timeout": ${DISCORD_VIEW_SHORT_TIMEOUT:=60},
    "database_file_path": "${DATABASE_FILE_PATH:=/app/database/bot.db}",
    "sentry_sdk_dsn": ${SENTRY_SDK_DSN:=null},
    "notification_channel_id": ${NOTIFICATION_CHANNEL_ID:=null}
}

CONFIG_JSON

python main.py &
pid="$!"

while true
do
  tail -f /dev/null & wait ${!}
done