from typing import Final

from prometheus_client import Counter, Gauge


class Metrics:
    """定義各項用來傳送給 Prometheus Server 的 Metric"""

    PREFIX: Final[str] = "discordbot_"
    """Metric 名字的前綴"""

    IS_CONNECTED: Final[Gauge] = Gauge(PREFIX + "connected", "機器人是否連接到 Discord", ["shard"])
    """機器人是否連接到 Discord，值為 1 或 0"""

    LATENCY: Final[Gauge] = Gauge(PREFIX + "latency_seconds", "機器人連接到 Discord 的延遲", ["shard"])
    """機器人連接到 Discord 的延遲 (單位: 秒)"""

    GUILDS: Final[Gauge] = Gauge(PREFIX + "guilds_total", "機器人所在的伺服器總數量")
    """機器人所在的伺服器總數量"""

    CHANNELS: Final[Gauge] = Gauge(PREFIX + "channels_total", "機器人所在的頻道總數量")
    """機器人所在的頻道總數量"""

    USERS: Final[Gauge] = Gauge(PREFIX + "users_total", "機器人能看到的使用者總數量")
    """機器人能看到的使用者總數量"""

    COMMANDS: Final[Gauge] = Gauge(PREFIX + "commands_total", "機器人能使用的指令的總數量")
    """機器人能使用的指令的總數量"""

    INTERACTION_EVENTS: Final[Counter] = Counter(
        PREFIX + "on_interaction_events",
        "互動指令 (Interaction) 被呼叫的次數",
        ["shard", "interaction", "command"],
    )
    """互動指令 (Interaction) 被呼叫的次數"""

    COMMAND_EVENTS: Final[Counter] = Counter(
        PREFIX + "on_command_events", "文字指令被呼叫的次數", ["shard", "command"]
    )
    """文字指令被呼叫的次數"""

    CPU_USAGE: Final[Gauge] = Gauge(PREFIX + "cpu_usage_percent", "系統的 CPU 使用率")
    """系統的 CPU 使用率 (0 ~ 100%)"""

    MEMORY_USAGE: Final[Gauge] = Gauge(PREFIX + "memory_usage_percent", "機器人程序的記憶體使用率")
    """機器人程序的記憶體使用率 (0 ~ 100%)"""

    PROCESS_START_TIME: Final[Gauge] = Gauge(
        PREFIX + "process_start_time_seconds", "機器人程序啟動時當下的時間"
    )
    """機器人程序啟動時當下的時間 (UNIX Timestamp)"""
