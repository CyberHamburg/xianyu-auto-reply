"""Backend-WebڣС׮ҵ߼ _bootstrap.py"""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path

# ǰĿ¼ĿĿ¼ӵ Python ·ҵ룩
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(project_root))

# ʽӵǰĿ¼ _bootstrap Nuitka 
_bootstrap_file = current_dir / "_bootstrap.py"
if _bootstrap_file.exists() and '_bootstrap' not in sys.modules:
    _spec = importlib.util.spec_from_file_location("_bootstrap", str(_bootstrap_file))
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules['_bootstrap'] = _mod
    _spec.loader.exec_module(_mod)

from _bootstrap import app  # noqa: E402

if __name__ == "__main__":
    from _bootstrap import run_server
    run_server()
