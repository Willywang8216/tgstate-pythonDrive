from __future__ import annotations

from typing import List, Optional


def split_channel_config(raw: str | None) -> list[str]:
    """
    将 CHANNEL_NAME 配置拆分为列表。

    支持逗号 / 分号 / 换行分隔，例如:
    "@ch1, -100123, 123456789"
    """
    if not raw:
        return []
    # 统一将分号替换为逗号
    s = raw.replace(";", ",")
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return parts


def get_primary_channel(raw: str | None) -> str | None:
    """
    从 CHANNEL_NAME 配置中获取第一个频道/群组，作为“默认频道”。

    例如:
    - "@ch1"              -> "@ch1"
    - "@ch1, -1002, 123"  -> "@ch1"
    """
    parts = split_channel_config(raw)
    return parts[0] if parts else None


def is_valid_channel_identifier(part: str) -> bool:
    """
    校验单个频道/群组标识是否合法。

    允许:
    - @username
    - 数字 ID（例如 123456789）
    - 负数 ID（例如 -1001234567890）
    """
    if not part:
        return False
    part = part.strip()
    if not part:
        return False
    if part.startswith("@"):
        # 最少需要有 @+1 个字符
        return len(part) > 1
    # 纯数字或负数 ID
    if part.lstrip("-").isdigit():
        return True
    return False


def validate_channel_config(raw: str | None) -> bool:
    """
    校验 CHANNEL_NAME 配置，支持多个以逗号分隔。
    任意一个标识无效则整体视为无效。
    """
    for part in split_channel_config(raw):
        if not is_valid_channel_identifier(part):
            return False
    return True