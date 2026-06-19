"""Pytest bootstrap: ensure the project root is importable as ``src``.

Having a root-level ``conftest.py`` makes pytest add the project root to
``sys.path``, so ``import src...`` works without installing the package.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
