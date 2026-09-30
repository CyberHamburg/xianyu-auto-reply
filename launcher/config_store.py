"""
ó־ûģ

ܣ
1. ûдMySQLRedisϢļ
2. ´ʱԶѱ
3. ļܴ洢ֹй¶
"""
import base64
import json
import os
from pathlib import Path


# ļ
_CONFIG_FILE = "connection.dat"


def _get_config_path() -> Path:
    """
    ȡļ·
    
    Returns:
        ļ·
    """
    from launcher.frozen_detect import get_project_root
    base_dir = get_project_root()
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / _CONFIG_FILE


def _simple_encode(text: str) -> str:
    """
    򵥱룬Ĵ洢
    
    Args:
        text: ԭʼı
    Returns:
        Base64ַ
    """
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def _simple_decode(encoded: str) -> str:
    """
    򵥽
    
    Args:
        encoded: Base64ַ
    Returns:
        ԭʼı
    """
    return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")


def save_connection_config(config: dict) -> bool:
    """
    õļ
    
    ֶΣ룩򵥱󱣴档
    
    Args:
        config: ֵ䣬mysqlredisϢ
    Returns:
        TrueɹFalseʧ
    """
    try:
        save_data = {
            "mysql_host": config.get("mysql_host", ""),
            "mysql_port": str(config.get("mysql_port", "3306")),
            "mysql_user": config.get("mysql_user", ""),
            "mysql_password": _simple_encode(config.get("mysql_password", "")),
            "mysql_database": config.get("mysql_database", ""),
            "redis_host": config.get("redis_host", ""),
            "redis_port": str(config.get("redis_port", "6379")),
            "redis_password": _simple_encode(config.get("redis_password", "")),
            "redis_db": str(config.get("redis_db", "0")),
        }
        config_path = _get_config_path()
        config_path.write_text(json.dumps(save_data, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def load_connection_config() -> dict | None:
    """
    ļ
    
    Returns:
        ֵ䣬ļڻȡʧܷNone
    """
    config_path = _get_config_path()
    if not config_path.exists():
        return None
    
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return {
            "mysql_host": data.get("mysql_host", ""),
            "mysql_port": data.get("mysql_port", "3306"),
            "mysql_user": data.get("mysql_user", ""),
            "mysql_password": _simple_decode(data.get("mysql_password", "")),
            "mysql_database": data.get("mysql_database", ""),
            "redis_host": data.get("redis_host", ""),
            "redis_port": data.get("redis_port", "6379"),
            "redis_password": _simple_decode(data.get("redis_password", "")),
            "redis_db": data.get("redis_db", "0"),
        }
    except Exception:
        return None
