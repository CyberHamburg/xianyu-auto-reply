"""
Playwright Chromium Զ밲װģ

ܣ
1.  Playwright Python ǷѰװδװԶ pip install
2.  Playwright Chromium ǷѰװ
3. δװǶ Python ʱԶذװ
4. ṩװȻص GUI ʾװ״̬
"""
import os
import sys
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional

from loguru import logger


def _get_bundled_browser_dir() -> Optional[Path]:
    from launcher.frozen_detect import is_frozen, get_project_root
    if not is_frozen():
        return None
    candidate = get_project_root() / "ms-playwright"
    if candidate.exists():
        return candidate
    return None


def get_playwright_browser_dir() -> Optional[Path]:
    """
    ȡ Playwright Ŀ¼

    ȼ
    1. Ŀ¼µ ms-playwright
    2.  PLAYWRIGHT_BROWSERS_PATH
    3. Windows: %LOCALAPPDATA%\ms-playwright
    4. Linux/Mac: ~/.cache/ms-playwright
    """
    bundled_dir = _get_bundled_browser_dir()
    if bundled_dir:
        return bundled_dir

    env_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate

    local_app = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app:
        candidate = Path(local_app) / "ms-playwright"
        if candidate.exists():
            return candidate

    candidate = Path.home() / ".cache" / "ms-playwright"
    if candidate.exists():
        return candidate

    return None


def ensure_playwright_browser_path() -> Optional[Path]:
    """ PLAYWRIGHT_BROWSERS_PATH Ŀ¼"""
    browser_dir = get_playwright_browser_dir()
    if browser_dir:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browser_dir)
        logger.info(f"Playwright Ŀ¼: {browser_dir}")
    return browser_dir


def get_chromium_executable_path() -> Optional[str]:
    """λ Chromium ִļ·"""
    browser_dir = get_playwright_browser_dir()
    if browser_dir and browser_dir.exists():
        try:
            chromium_dirs = [d for d in browser_dir.iterdir() if d.is_dir() and "chromium" in d.name.lower()]
            for cdir in chromium_dirs:
                candidates = [
                    cdir / "chrome-win64" / "chrome.exe",
                    cdir / "chrome-win" / "chrome.exe",
                    cdir / "chrome-linux" / "chrome",
                    cdir / "chrome-linux64" / "chrome",
                    cdir / "chrome-mac" / "Chromium.app" / "Contents" / "MacOS" / "Chromium",
                ]
                for candidate in candidates:
                    if candidate.exists():
                        return str(candidate)
        except Exception as e:
            logger.warning(f"λ Chromium ִļʧ: {e}")

    for candidate in (
        Path("/usr/bin/chromium-browser"),
        Path("/usr/bin/chromium"),
    ):
        if candidate.exists():
            return str(candidate)
    return None


def is_playwright_package_installed() -> bool:
    """
     Playwright Python ǷѰװ
    
    Returns:
        True ѰװFalse δװ
    """
    try:
        import playwright.async_api
        logger.info("Playwright Python Ѱװ")
        return True
    except ImportError:
        logger.info("Playwright Python δװ")
        return False


def install_playwright_package(
    progress_callback: Optional[Callable[[str], None]] = None,
) -> bool:
    """
    ʹ pip װ Playwright Python 
    
    Args:
        progress_callback: Ȼص
        
    Returns:
        True װɹFalse װʧ
    """
    def _notify(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)
    
    try:
        _notify("ڰװ Playwright Python ...")
        
        python_exe = _get_python_exe()
        cmd = [python_exe, "-m", "pip", "install", "playwright", "-q"]
        
        logger.info(f"ִаװ: {' '.join(cmd)}")
        
        popen_kwargs = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if sys.platform == "win32":
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        
        result = subprocess.run(cmd, **popen_kwargs)
        
        if result.returncode == 0:
            _notify("Playwright Python װɹ")
            return True
        else:
            _notify(f"Playwright Python װʧ: {result.stdout}")
            return False
            
    except Exception as e:
        _notify(f"װ Playwright 쳣: {e}")
        return False


def _get_python_exe() -> str:
    """
    ȡǰ Python ·

    (Nuitka standalone)ģʽʹͬĿ¼ python.exe
    ģʽʹõǰ

    Returns:
        Python ·
    """
    from launcher.frozen_detect import is_frozen
    if is_frozen():
        exe_dir = Path(sys.executable).parent
        for name in ("python.exe", "pythonw.exe", "python3.exe", "python"):
            candidate = exe_dir / name
            if candidate.exists():
                logger.info(f"ģʽʹǶ Python : {candidate}")
                return str(candidate)
        logger.warning("ģʽδҵͬĿ¼ Python ˵ǰ EXE")
        return sys.executable
    return sys.executable


def _find_driver_cmd_in_frozen_dir() -> Optional[list]:
    """
    ģʽֶ dist Ŀ¼ Playwright driver

    Nuitka standalone  playwright/driver/ µ node.exe  cli.js
    һ dist Ŀ¼ Python  import ʧʱ
    ȻֱͨӵЩļװ Chromium

    Returns:
        ҵʱ [node_exe, cli_js, "install", "chromium"]򷵻 None
    """
    from launcher.frozen_detect import get_project_root
    root = get_project_root()

    # Playwright driver  Nuitka dist пܵλ
    search_bases = [
        root / "playwright" / "driver",
        root / "playwright" / "driver" / "package",
    ]

    node_exe = None
    cli_js = None

    #  node ִļ
    for base in search_bases:
        for name in ("node.exe", "node"):
            candidate = base / name
            if candidate.exists():
                node_exe = str(candidate)
                break
        if node_exe:
            break

    #  cli.js
    for base in search_bases:
        candidate = base / "package" / "cli.js"
        if candidate.exists():
            cli_js = str(candidate)
            break
        candidate = base / "cli.js"
        if candidate.exists():
            cli_js = str(candidate)
            break

    if node_exe and cli_js:
        logger.info(f"ģʽֶλ driver: node={node_exe}, cli={cli_js}")
        return [node_exe, cli_js, "install", "chromium"]

    logger.warning(
        f"ģʽδҵ Playwright driver ļ "
        f"(node_exe={node_exe}, cli_js={cli_js})"
    )
    return None


def is_chromium_installed() -> bool:
    """
     Playwright Chromium ǷѰװ

    (frozen)ģʽֻͨļϵͳ飬 playwright 룻
    ģʽȼ playwright  registry 顣

    Returns:
        True ѰװFalse δװ
    """
    from launcher.frozen_detect import is_frozen

    ensure_playwright_browser_path()

    # ---------- ģʽֱӲ chromium ִļ ----------
    if is_frozen():
        chromium_path = get_chromium_executable_path()
        if chromium_path:
            logger.info(f"ģʽ: Chromium Ѱװ: {chromium_path}")
            return True
        logger.info("ģʽ: δ⵽ Chromium ")
        return False

    # ---------- ģʽȼ playwright  ----------
    if not is_playwright_package_installed():
        logger.info("Playwright δװ޷ Chromium")
        return False

    try:
        from cloakbrowser._impl_driver import compute_driver_executable
        driver_exe, _ = compute_driver_executable()
        if not os.path.exists(driver_exe):
            logger.info(f"Playwright driver : {driver_exe}")
            return False
    except Exception as e:
        logger.warning(f" Playwright driver ʧ: {e}")

    chromium_path = get_chromium_executable_path()
    if chromium_path:
        logger.info(f"Chromium Ѱװ: {chromium_path}")
        return True

    #  playwright  registry 
    try:
        from cloakbrowser._impl_browsers import get_playwright_browsers
        browsers = get_playwright_browsers()
        for b in browsers:
            if b.get("name") == "chromium" and b.get("installed"):
                logger.info("Chromium Ѱװ")
                return True
    except Exception as e:
        logger.warning(f" Chromium registry ʧ: {e}")

    logger.info("Chromium δװ")
    return False


def install_chromium(
    progress_callback: Optional[Callable[[str], None]] = None,
    done_callback: Optional[Callable[[bool, str], None]] = None,
) -> None:
    """
    ߳аװ Playwright Chromium 

    ͨӽ̵ playwright install chromium
    ʵʱȡݸ progress_callback չʾȡ

    Args:
        progress_callback: Ȼص fn(message: str)߳е
        done_callback: ɻص fn(success: bool, message: str)߳е
    """
    def _notify(msg: str):
        if progress_callback:
            progress_callback(msg)

    def _done(success: bool, msg: str):
        if done_callback:
            done_callback(success, msg)

    def _run():
        try:
            _notify("׼...")

            ensure_playwright_browser_path()

            # ʹ Playwright õ drivernode.exe + cli.jsֱִаװ
            # Ա Nuitka  python -m  self-execution 
            cmd = None
            try:
                from cloakbrowser._impl_driver import compute_driver_executable
                driver_exe, driver_cli = compute_driver_executable()
                cmd = [driver_exe, driver_cli, "install", "chromium"]
            except Exception as drv_err:
                logger.warning(f"ͨ playwright API ȡ driver ʧ: {drv_err}")

            # 1: ģʽֶ dist Ŀ¼ driver
            if cmd is None:
                from launcher.frozen_detect import is_frozen
                if is_frozen():
                    cmd = _find_driver_cmd_in_frozen_dir()

            # 2: ö python.exe -m playwright
            if cmd is None:
                python_exe = _get_python_exe()
                cmd = [python_exe, "-m", "playwright", "install", "chromium"]

            logger.info(f"ִаװ: {' '.join(cmd)}")
            _notify("޸ Chromium أԼ200MBĵȴ...")

            # Ϊexe޿̨ʽstdincreationflagsֹЧ
            popen_kwargs = dict(
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            if sys.platform == "win32":
                popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            process = subprocess.Popen(cmd, **popen_kwargs)

            # ʵʱȡ
            last_line = ""
            for line in iter(process.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue
                last_line = line
                logger.info(f"[playwright install] {line}")

                # ؽ
                if "%" in line:
                    _notify(f": {line}")
                elif "downloading" in line.lower() or "Downloading" in line:
                    _notify(f": {line}")
                elif "installing" in line.lower() or "Installing" in line:
                    _notify(f"װ: {line}")
                else:
                    _notify(line)

            process.wait()
            exit_code = process.returncode

            if exit_code == 0:
                logger.info("Chromium װִгɹжУ...")
                _notify("Уװ...")
                
                # θˣȷĿ
                if is_chromium_installed():
                    logger.info("Chromium װɹͨУ")
                    _notify("Chromium װɣ")
                    _done(True, "װɹ")
                else:
                    error_msg = "װִгɹУʧܣܰװ"
                    logger.error(error_msg)
                    _notify(error_msg)
                    _done(False, error_msg)
            else:
                error_msg = f"װʧܣ˳: {exit_code}: {last_line}"
                logger.error(error_msg)
                _notify(f"װʧ: {last_line}")
                _done(False, error_msg)

        except FileNotFoundError:
            msg = "Ҳ Python ޷װ"
            logger.error(msg)
            _notify(msg)
            _done(False, msg)
        except Exception as e:
            msg = f"װʱ쳣: {e}"
            logger.error(msg)
            _notify(str(e))
            _done(False, msg)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread


def check_and_install_chromium(
    progress_callback: Optional[Callable[[str], None]] = None,
    done_callback: Optional[Callable[[bool, str], None]] = None,
) -> Optional[threading.Thread]:
    """
     Playwright  Chromium ǷѰװδװԶ

    ̣
    1.  Playwright Python Ƿװδװ pip install
    2.  Chromium Ƿװδװ

    Args:
        progress_callback: Ȼص
        done_callback: ɻص fn(success, message)
    Returns:
        Ҫװذװ̣߳Ѱװ None
    """
    # 1.  Playwright Python 
    from launcher.frozen_detect import is_frozen
    if not is_playwright_package_installed():
        if is_frozen():
            # ģʽ playwright ӦǶ Nuitka 
            # ʧܿ Nuitka ̬⣬ pip װ
            # ֱӽ밲װ
            logger.warning(
                "ģʽ Playwright ʧܣ pip װ"
                "ֱӼ"
            )
            if progress_callback:
                progress_callback("⵽װֱӼ...")
        else:
            logger.info("Playwright Python δװʼԶװ...")
            if progress_callback:
                progress_callback("ڰװ Playwright Python ...")

            if not install_playwright_package(progress_callback):
                if done_callback:
                    done_callback(False, "Playwright Python װʧ")
                return None

    # 2.  Chromium 
    if is_chromium_installed():
        if done_callback:
            done_callback(True, "Ѿ")
        return None

    logger.info("Chromium δʼ޸...")
    return install_chromium(progress_callback, done_callback)
