"""Check if all required packages are installed."""

import sys

required_packages = [
    'pandas',
    'numpy',
    'yfinance',
    'streamlit',
    'click',
    'python-dotenv',
    'pydantic',
    'httpx',
]

missing_packages = []

for package in required_packages:
    try:
        if package == 'python-dotenv':
            __import__('dotenv')
        else:
            __import__(package)
        print(f"✅ {package}")
    except ImportError:
        print(f"❌ {package} - MISSING")
        missing_packages.append(package)

if missing_packages:
    print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n✅ All required packages are installed!")
    sys.exit(0)

