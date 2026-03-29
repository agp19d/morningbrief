"""
build_lambda.py
---------------
Builds the Lambda deployment package (lambda.zip).

Steps:
  1. Installs Python dependencies into a temporary build directory using uv.
  2. Copies the contents of src/ into the same directory.
  3. Zips everything into lambda.zip at the project root.

Usage:
    python scripts/build_lambda.py

Run this before `terraform apply`. The Terraform config references lambda.zip
via the lambda_zip_path variable (default: ../lambda.zip relative to terraform/).

Requirements:
    - uv must be installed and available on PATH.
    - Run from the project root directory.
"""

import os
import shutil
import subprocess
import sys
import zipfile

# ---------------------------------------------------------------------------
# Paths (all relative to the project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(PROJECT_ROOT, "build", "package")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
ZIP_PATH = os.path.join(PROJECT_ROOT, "lambda.zip")

# Dependencies to install (must match pyproject.toml)
DEPENDENCIES = ["jinja2", "litellm", "tavily-python"]


def clean_build_dir() -> None:
    """Remove and recreate the build directory."""
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)
    print(f"Build directory ready: {BUILD_DIR}")


def install_dependencies() -> None:
    """Install production dependencies into the build directory using uv."""
    print(f"Installing dependencies: {', '.join(DEPENDENCIES)}")
    subprocess.run(
        ["uv", "pip", "install", "--target", BUILD_DIR, "--python", "3.12"]
        + DEPENDENCIES,
        check=True,
        cwd=PROJECT_ROOT,
    )
    print("Dependencies installed.")


def copy_source() -> None:
    """Copy all files and directories from src/ into the build directory."""
    print(f"Copying source from {SRC_DIR}...")
    for item in os.listdir(SRC_DIR):
        src = os.path.join(SRC_DIR, item)
        dst = os.path.join(BUILD_DIR, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    print("Source files copied.")


def build_zip() -> None:
    """Zip the build directory contents into lambda.zip."""
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

    print(f"Building {ZIP_PATH}...")
    file_count = 0
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(BUILD_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                # Store files relative to the build dir root so Lambda can
                # import them directly (e.g. lambda_function, config, etc.)
                arcname = os.path.relpath(file_path, BUILD_DIR)
                zf.write(file_path, arcname)
                file_count += 1

    size_mb = os.path.getsize(ZIP_PATH) / (1024 * 1024)
    print(f"Done: {ZIP_PATH} ({file_count} files, {size_mb:.1f} MB)")


def main() -> None:
    """Run the full build pipeline."""
    print("=== Building Lambda deployment package ===")
    clean_build_dir()
    install_dependencies()
    copy_source()
    build_zip()
    print("=== Build complete ===")


if __name__ == "__main__":
    main()
