"""Report generation functions for creating markdown reports.

This module provides functions for generating markdown reports with tables
for top movers, bottom movers, and volatile movers.
"""

import pandas as pd
from datetime import date
from pandas import DataFrame
from pathlib import Path


def _dataframe_to_markdown_table(df: DataFrame) -> str:
    """Convert DataFrame to markdown table format.

    Args:
        df: DataFrame to convert.

    Returns:
        Markdown formatted table string.
    """
    if df.empty:
        return "*(No data)*\n"

    # Use pandas to_markdown if available, otherwise manual formatting
    try:
        return df.to_markdown(index=False) + "\n"
    except AttributeError:
        # Fallback: manual markdown table generation
        return _manual_markdown_table(df)


def _manual_markdown_table(df: DataFrame) -> str:
    """Manually generate markdown table from DataFrame.

    Args:
        df: DataFrame to convert. Must not be empty (checked by caller).

    Returns:
        Markdown formatted table string.
    """
    lines = []
    columns = df.columns.tolist()

    # Header row
    header = "| " + " | ".join(str(col) for col in columns) + " |"
    lines.append(header)

    # Separator row
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    lines.append(separator)

    # Data rows
    for _, row in df.iterrows():
        data_row = "| " + " | ".join(str(row[col]) for col in columns) + " |"
        lines.append(data_row)

    return "\n".join(lines) + "\n"


def render_markdown(
    analysis_date: date,
    top: DataFrame,
    bottom: DataFrame,
    volatile: DataFrame,
) -> str:
    """Generate markdown report with tables for movers.

    Args:
        analysis_date: Date of the analysis.
        top: DataFrame with top movers (상승). Should contain 'symbol' column.
        bottom: DataFrame with bottom movers (하락). Should contain 'symbol' column.
        volatile: DataFrame with volatile movers (변동성). Should contain 'symbol' column.

    Returns:
        Markdown formatted string with header, date, and tables.
        Original DataFrames are not modified.

    Examples:
        >>> df_top = pd.DataFrame({'symbol': ['AAPL'], 'return_pct': [5.0]})
        >>> df_bottom = pd.DataFrame({'symbol': ['TSLA'], 'return_pct': [-5.0]})
        >>> df_vol = pd.DataFrame({'symbol': ['GOOGL'], 'vol_pct': [10.0]})
        >>> report = render_markdown(date(2024, 1, 15), df_top, df_bottom, df_vol)
        >>> 'NASDAQ' in report or 'Daily Movers' in report
        True
    """
    # Create copies to avoid side effects
    top_df = top.copy()
    bottom_df = bottom.copy()
    volatile_df = volatile.copy()

    lines = []

    # Header
    lines.append("# NASDAQ Daily Movers & Volatility Analyzer")
    lines.append("")
    lines.append(f"**Date:** {analysis_date.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Top Movers Section
    lines.append("## 📈 Top Movers (상승)")
    lines.append("")
    lines.append(_dataframe_to_markdown_table(top_df))
    lines.append("")

    # Bottom Movers Section
    lines.append("## 📉 Bottom Movers (하락)")
    lines.append("")
    lines.append(_dataframe_to_markdown_table(bottom_df))
    lines.append("")

    # Volatile Movers Section
    lines.append("## 📊 Volatile Movers (변동성)")
    lines.append("")
    lines.append(_dataframe_to_markdown_table(volatile_df))
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*This report is for informational purposes only and does not constitute investment advice.*")

    return "\n".join(lines)


def save_markdown(content: str, filepath: str) -> None:
    """Save markdown content to file.

    Args:
        content: Markdown content to save.
        filepath: Path to output file.

    Raises:
        IOError: If file cannot be written.

    Examples:
        >>> save_markdown("# Report", "report.md")
    """
    try:
        path = Path(filepath)
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except IOError as e:
        raise IOError(f"Error writing markdown file {filepath}: {str(e)}") from e

