"""Minimal DuckDB persistence layer.

DuckDB is used as a lightweight local analytical store for processed tables
(e.g. the assembled modelling dataset). Connections are opened per call to keep
the API simple and avoid stale handles in Streamlit's re-run model.
"""
from __future__ import annotations

import duckdb
import pandas as pd

from src.config import DB_PATH


def get_connection() -> duckdb.DuckDBPyConnection:
    """Open (and return) a DuckDB connection to the project database file."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def write_table(df: pd.DataFrame, table_name: str) -> None:
    """Create or replace ``table_name`` with the contents of ``df``."""
    con = get_connection()
    try:
        con.register("df_to_write", df)
        con.execute(f'CREATE OR REPLACE TABLE "{table_name}" AS SELECT * FROM df_to_write')
        con.unregister("df_to_write")
    finally:
        con.close()


def read_table(table_name: str) -> pd.DataFrame:
    """Read an entire table into a pandas DataFrame."""
    con = get_connection()
    try:
        return con.execute(f'SELECT * FROM "{table_name}"').fetchdf()
    finally:
        con.close()


def table_exists(table_name: str) -> bool:
    """Return True if ``table_name`` exists in the database."""
    con = get_connection()
    try:
        result = con.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = ?",
            [table_name],
        ).fetchone()
        return result is not None
    finally:
        con.close()
