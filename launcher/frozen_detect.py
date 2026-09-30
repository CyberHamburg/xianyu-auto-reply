"""
ģʽ⹤

ܣ
1. ͳһǷڱģʽNuitka/PyInstaller/cx_Freezeȣ
2. ȡĿĿ¼ģʽΪexeĿ¼ģʽΪlauncherĸĿ¼

Nuitka ʹ __compiled__ PyInstaller ʹ sys.frozen
"""
import sys
from pathlib import Path


def is_frozen() -> bool:
    """
    ⵱ǰǷڱ/ģʽ
    
    ֧֣
    - Nuitka:  __compiled__ 
    - PyInstaller/cx_Freeze:  sys.frozen 
    
    Returns:
        True ʾڱģʽFalse ʾģʽ
    """
    # Nuitka ģע __compiled__ 
    # Ҫ builtins ͨ __name__ 
    try:
        # Nuitka standalone ģʽ
        import __main__
        if hasattr(__main__, "__compiled__"):
            return True
    except Exception:
        pass
    
    # Nuitka Ҳͨ sys.executable Ƿָ .exe Ҳ python.exe
    if sys.platform == "win32":
        exe_name = Path(sys.executable).name.lower()
        #  exe Ʋ python صģ˵Ǳĳ
        if exe_name not in ("python.exe", "pythonw.exe", "python3.exe", "python"):
            # һȷϲ⻷
            if not exe_name.startswith("python"):
                return True
    
    # PyInstaller / cx_Freeze 
    if getattr(sys, "frozen", False):
        return True
    
    return False


def get_project_root() -> Path:
    """
    ȡĿĿ¼
    
    ģʽΪexeĿ¼ģʽΪlauncherĸĿ¼
    
    Returns:
        ĿĿ¼Path
    """
    if is_frozen():
        return Path(sys.executable).parent
    # ģʽlauncher Ŀ¼ĸĿ¼
    return Path(__file__).parent.parent
