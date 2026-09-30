"""
Դ빤

ܣ
1. ָĿ¼.pyļΪ.pycֽļ
2. ɹɾ.pyԴļĿ¼еĸӰԭʼ룩
3. Ŀ¼ṹ䣬.pycļ__pycache__ͬĿ¼

ע⣺˽űֻڴжԷĿ¼еĸִУ޸ԭʼĿԴ
"""
import compileall
import os
import py_compile
import sys
from pathlib import Path


def compile_directory(target_dir: str) -> bool:
    """
    Ŀ¼.pyΪ.pycȻɾ.pyԴļ
    
    .pycļֱӷ.pyͬĿ¼main.py -> main.pyc
    Ƿ__pycache__СPythonֱӼ.pycļ
    .pyԴļڡ
    
    Args:
        target_dir: ҪĿ¼·ӦΪĿ¼еĸ
    Returns:
        TrueɹFalseʧ
    """
    target = Path(target_dir)
    if not target.exists():
        print(f"[WARN] Directory not found: {target_dir}")
        return False
    
    print(f"[INFO] Compiling .py to .pyc in: {target_dir}")
    
    success_count = 0
    fail_count = 0
    
    # .pyļ
    for py_file in target.rglob("*.py"):
        try:
            # Ϊ.pycֱӷ.pyͬĿ¼ main.py -> main.pyc
            # PythonֱӼأԴļ
            pyc_file = py_file.with_suffix(".pyc")
            py_compile.compile(str(py_file), cfile=str(pyc_file), doraise=True)
            # ɾ .py ԴļɾĿ¼
            py_file.unlink()
            success_count += 1
        except py_compile.PyCompileError as e:
            print(f"[WARN] Compile failed: {py_file} - {e}")
            fail_count += 1
    
    # ɾ __pycache__ Ŀ¼Ҫ
    for pycache in target.rglob("__pycache__"):
        if pycache.is_dir():
            import shutil
            shutil.rmtree(pycache, ignore_errors=True)
    
    print(f"[INFO] Compiled {success_count} files, {fail_count} failures in {target_dir}")
    return fail_count == 0


def main():
    """
    вָҪĿ¼б
    
    ÷: python compile_pyc.py <dir1> <dir2> ...
    """
    if len(sys.argv) < 2:
        print("Usage: python compile_pyc.py <dir1> [dir2] ...")
        sys.exit(1)
    
    all_ok = True
    for directory in sys.argv[1:]:
        if not compile_directory(directory):
            all_ok = False
    
    if not all_ok:
        print("[WARN] Some files failed to compile")
        sys.exit(1)
    else:
        print("[INFO] All files compiled successfully")


if __name__ == "__main__":
    main()
