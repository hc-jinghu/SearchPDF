#!/usr/bin/env python3
"""
uninstall.py
Removes all traces of SearchPDF:
  - pip packages installed by install.py
  - PaddleOCR model cache (~/.paddleocr)
  - This project folder (optional)
"""

import sys
import os
import shutil
import subprocess
import platform
from pathlib import Path


PACKAGES = [
    "paddlepaddle",
    "paddleocr",
    "PyQt6",
    "PyQt6-Qt6",
    "PyQt6-sip",
    "Pillow",
    "pymupdf",
]

PROJECT_DIR = Path(__file__).resolve().parent


def confirm(prompt: str) -> bool:
    answer = input(f"{prompt} [y/N]: ").strip().lower()
    return answer == "y"


def uninstall_packages():
    print("\n[1/3] Uninstalling pip packages...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y"] + PACKAGES
    )
    if result.returncode == 0:
        print("      Done.")
    else:
        print("      Some packages may not have been installed — that's fine.")


def remove_model_cache():
    print("\n[2/3] Removing PaddleOCR model cache...")
    cache_dir = Path.home() / ".paddleocr"
    if cache_dir.exists():
        size_mb = sum(
            f.stat().st_size for f in cache_dir.rglob("*") if f.is_file()
        ) / (1024 * 1024)
        print(f"      Found: {cache_dir}  ({size_mb:.0f} MB)")
        if confirm("      Delete model cache?"):
            shutil.rmtree(cache_dir)
            print("      Deleted.")
        else:
            print("      Skipped.")
    else:
        print("      No cache found — nothing to do.")


def remove_project_folder():
    print(f"\n[3/3] Remove project folder?")
    print(f"      {PROJECT_DIR}")
    print("      (This deletes all app files including this uninstaller.)")
    if confirm("      Delete project folder?"):
        # Schedule deletion via shell so Python can exit cleanly first
        os_name = platform.system()
        if os_name == "Windows":
            # Use cmd to delete after a short delay so Python releases file handles
            cmd = f'cmd /c "ping 127.0.0.1 -n 2 >nul && rmdir /s /q \"{PROJECT_DIR}\""'
            subprocess.Popen(cmd, shell=True, close_fds=True)
        else:
            # macOS / Linux: use a subshell
            subprocess.Popen(
                f'sleep 1 && rm -rf "{PROJECT_DIR}"',
                shell=True,
                close_fds=True,
            )
        print("      Scheduled for deletion.")
    else:
        print("      Skipped.")


def main():
    os_name  = platform.system()
    arch     = platform.machine()

    print("=" * 52)
    print("  SearchPDF — Uninstaller")
    print("=" * 52)
    print(f"  OS: {os_name}  |  Arch: {arch}")
    print()
    print("  This will remove:")
    print("    - pip packages (paddlepaddle, paddleocr, PyQt6, Pillow, pymupdf)")
    print("    - PaddleOCR model cache (~/.paddleocr)")
    print("    - Optionally: this project folder")
    print()

    if not confirm("Continue with uninstall?"):
        print("\nAborted.")
        sys.exit(0)

    uninstall_packages()
    remove_model_cache()
    remove_project_folder()

    print("\n" + "=" * 52)
    print("  Uninstall complete.")
    print("=" * 52)


if __name__ == "__main__":
    main()
