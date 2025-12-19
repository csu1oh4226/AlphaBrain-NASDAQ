"""Example usage of data collection module.

This script demonstrates how to use the data collection module
to fetch market data from different sources.
"""

from datetime import date
from nasdaq_scanner.providers import collect_data, load_ticker_list, YFinanceProvider

# Example 1: Collect data for NASDAQ-100
print("Example 1: Collecting data for NASDAQ-100")
df, failed = collect_data('nasdaq-100', date(2024, 1, 15))
print(f"Successfully collected: {len(df)} tickers")
print(f"Failed: {len(failed)} tickers")
print(f"\nFirst few rows:")
print(df.head())
print(f"\nFailed tickers: {failed[:5]}...")  # Show first 5

# Example 2: Collect data from CSV file
print("\n" + "="*50)
print("Example 2: Collecting data from CSV file")
df, failed = collect_data('nasdaq_tickers.csv', date(2024, 1, 15))
print(f"Successfully collected: {len(df)} tickers")
print(f"Failed: {len(failed)} tickers")

# Example 3: Collect data from custom ticker list
print("\n" + "="*50)
print("Example 3: Collecting data from custom ticker list")
custom_tickers = ['AAPL', 'MSFT', 'GOOGL', 'INVALID_TICKER']
df, failed = collect_data(custom_tickers, date(2024, 1, 15))
print(f"Successfully collected: {len(df)} tickers")
print(f"Failed: {len(failed)} tickers")
print(f"Failed tickers: {failed}")

# Example 4: Using custom provider
print("\n" + "="*50)
print("Example 4: Using custom provider")
provider = YFinanceProvider()
df, failed = collect_data(
    ['AAPL', 'MSFT'],
    date(2024, 1, 15),
    provider=provider,
    max_retries=3
)
print(f"Successfully collected: {len(df)} tickers")

# Example 5: Check data structure
print("\n" + "="*50)
print("Example 5: Data structure")
if len(df) > 0:
    print(f"Columns: {df.columns.tolist()}")
    print(f"Data types:\n{df.dtypes}")
    print(f"\nSample data:")
    print(df.head())

