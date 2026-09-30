"""
ļʼģ

ܣ
ʱԼ data Ŀ¼ȱļԶģļ
ûֻ޸еֵɡ

Զɵļ
- data/update_config.json  ߸·ַ
"""
import json
import sys
from pathlib import Path


def _get_data_dir() -> Path:
    """ȡ data Ŀ¼·Զ"""
    from launcher.frozen_detect import get_project_root
    base_dir = get_project_root()
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# ҪԶɵļĬ
_CONFIG_TEMPLATES = {
    "update_config.json": {
        "update_url": "https://xy-update.zhinianboke.com"
    },
}


def init_config_files():
    """
    Լ첢ʼļ

     _CONFIG_TEMPLATESӦļԶģ塣
    ѴڵļᱻǣӰʷݡ
    """
    data_dir = _get_data_dir()
    for filename, default_content in _CONFIG_TEMPLATES.items():
        config_path = data_dir / filename
        if not config_path.exists():
            try:
                config_path.write_text(
                    json.dumps(default_content, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except Exception:
                pass
