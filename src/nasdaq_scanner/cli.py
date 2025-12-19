"""CLI entry point for NASDAQ Scanner.

Command-line interface for running the daily movers and volatility analysis.
"""

import sys
import logging
from datetime import date
from pathlib import Path
from typing import Optional

try:
    import click
except ImportError:
    click = None  # type: ignore

# Import core modules
from nasdaq_scanner.core.universe import load_tickers
from nasdaq_scanner.core.metrics import calc_return_pct, calc_intraday_vol_pct
from nasdaq_scanner.core.ranking import top_n, bottom_n
from nasdaq_scanner.reporter.report import render_markdown, save_markdown
from nasdaq_scanner.providers.data_provider import fetch_ohlcv_batch

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    """Configure logging for CLI usage."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,  # Override any existing configuration
    )


def _handle_error(message: str, exception: Exception) -> None:
    """Handle errors consistently with logging and exit.

    Args:
        message: Error message to log.
        exception: Exception that occurred.
    """
    logger.error(f"{message}: {str(exception)}")
    sys.exit(1)


def run_analysis(
    analysis_date: date,
    universe_path: str,
    n: int = 10,
    output_path: Optional[str] = None,
) -> None:
    """Run the complete analysis pipeline.

    Args:
        analysis_date: Date to analyze.
        universe_path: Path to CSV file with ticker symbols.
        n: Number of top/bottom movers to include (default: 10).
        output_path: Optional path to save markdown report. If None, prints to stdout.
    """
    logger.info(f"Starting analysis for date: {analysis_date}")

    # Step 1: Load ticker universe
    logger.info(f"Loading ticker universe from: {universe_path}")
    try:
        symbols = load_tickers(universe_path)
        logger.info(f"Loaded {len(symbols)} tickers")
    except Exception as e:
        _handle_error("Failed to load ticker universe", e)

    if not symbols:
        logger.error("No tickers found in universe file")
        sys.exit(1)

    # Step 2: Fetch OHLCV data
    logger.info(f"Fetching OHLCV data for {len(symbols)} symbols...")
    try:
        ohlcv_df = fetch_ohlcv_batch(symbols, analysis_date)
        logger.info(f"Fetched data for {len(ohlcv_df)} symbols")
    except Exception as e:
        _handle_error("Failed to fetch data", e)

    if ohlcv_df.empty:
        logger.error("No OHLCV data was fetched")
        sys.exit(1)

    # Step 3: Calculate metrics
    logger.info("Calculating metrics...")
    try:
        # Calculate return percentage
        analysis_df = calc_return_pct(ohlcv_df)
        # Calculate intraday volatility
        analysis_df = calc_intraday_vol_pct(analysis_df)
        logger.info(f"Calculated metrics for {len(analysis_df)} symbols")
    except Exception as e:
        _handle_error("Failed to calculate metrics", e)

    # Step 4: Generate rankings
    logger.info(f"Generating top {n} rankings...")
    try:
        # Ensure symbol column exists for ranking
        if "symbol" not in analysis_df.columns:
            logger.error("'symbol' column not found in analysis data")
            sys.exit(1)

        top_movers = top_n(analysis_df, col="return_pct", n=n)
        bottom_movers = bottom_n(analysis_df, col="return_pct", n=n)
        volatile_movers = top_n(analysis_df, col="vol_pct", n=n)

        logger.info(
            f"Generated rankings: {len(top_movers)} top, "
            f"{len(bottom_movers)} bottom, {len(volatile_movers)} volatile"
        )
    except Exception as e:
        _handle_error("Failed to generate rankings", e)

    # Step 5: Generate markdown report
    logger.info("Generating markdown report...")
    try:
        markdown_content = render_markdown(
            analysis_date, top_movers, bottom_movers, volatile_movers
        )
    except Exception as e:
        _handle_error("Failed to generate report", e)

    # Step 6: Output report
    if output_path:
        logger.info(f"Saving report to: {output_path}")
        try:
            save_markdown(markdown_content, output_path)
            logger.info("Report saved successfully")
        except Exception as e:
            _handle_error("Failed to save report", e)
    else:
        # Print to stdout
        print(markdown_content)

    logger.info("Analysis completed successfully")


@click.command()
@click.option(
    "--date",
    "analysis_date_str",
    required=True,
    help="Analysis date in YYYY-MM-DD format",
)
@click.option(
    "--n",
    default=10,
    type=int,
    help="Number of top/bottom movers to include (default: 10)",
)
@click.option(
    "--universe",
    "universe_path",
    required=True,
    help="Path to CSV file with ticker symbols",
)
@click.option(
    "--output",
    "output_path",
    default=None,
    help="Path to save markdown report (default: print to stdout)",
)
def main(
    analysis_date_str: str,
    n: int,
    universe_path: str,
    output_path: Optional[str],
) -> None:
    """NASDAQ Daily Movers & Volatility Analyzer.

    Analyzes NASDAQ tickers for daily movers and volatility,
    generating a markdown report with top movers, bottom movers, and volatile movers.
    """
    _setup_logging()

    if click is None:
        print("Error: click is not installed. Install it with: pip install click")
        sys.exit(1)

    # Parse date
    try:
        analysis_date = date.fromisoformat(analysis_date_str)
    except ValueError:
        logger.error(f"Invalid date format: {analysis_date_str}. Use YYYY-MM-DD")
        sys.exit(1)

    # Validate universe file exists
    if not Path(universe_path).exists():
        logger.error(f"Universe file not found: {universe_path}")
        sys.exit(1)

    # Run analysis
    run_analysis(analysis_date, universe_path, n, output_path)


if __name__ == "__main__":
    main()
