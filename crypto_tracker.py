# crypto_tracker.py
"""
Cryptocurrency Price Tracker (Selenium + Chrome)
------------------------------------------------
ALL FEATURES INCLUDED:

✅ Live Price Scraping (real-time data from CoinMarketCap)
✅ Dynamic Page Handling (JavaScript-rendered content)
✅ Top 10 Coins Data (name, symbol, price, 24h change, market cap)
✅ CSV Export (structured, timestamped)
✅ Headless Browser Option (background run)
✅ Historical Logging (append new entries)
✅ Filtering (by price range, top gainers, top losers)
✅ Continuous Auto Logging (runs every X seconds)
✅ Persistent Browser Session (faster, stable scraping)
"""

import argparse
import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ---------- DRIVER SETUP ----------
def build_driver(headless: bool = True, window_size: str = "1920,1080") -> webdriver.Chrome:
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={window_size}")
    chrome_prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.experimental_options["prefs"] = chrome_prefs

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://coinmarketcap.com/")
    return driver


# ---------- HELPERS ----------
def parse_money(text: str) -> Optional[float]:
    """Convert '$64,000' or '$1.2B' into float."""
    if not text:
        return None
    text = text.replace(",", "").replace("$", "").replace("—", "").strip()
    multiplier = 1
    if text.endswith("K"):
        multiplier = 1_000
        text = text[:-1]
    elif text.endswith("M"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("B"):
        multiplier = 1_000_000_000
        text = text[:-1]
    elif text.endswith("T"):
        multiplier = 1_000_000_000_000
        text = text[:-1]
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def parse_percent(text: str) -> Optional[float]:
    """Convert '+3.25%' into float."""
    if not text:
        return None
    text = text.replace("%", "").replace("+", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


# ---------- SCRAPER ----------
def scrape_top_n(driver: webdriver.Chrome, n: int = 10, timeout: int = 30) -> List[Dict]:
    """Scrape top N cryptocurrencies from CoinMarketCap."""
    wait = WebDriverWait(driver, timeout)
    try:
        driver.refresh()
        driver.execute_script("window.scrollTo(0, 600);")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, "table tbody tr td:nth-child(4)"), "$"
            )
        )
    except TimeoutException:
        driver.save_screenshot("debug_timeout.png")
        print("⚠️ Timeout: Table not loaded. Screenshot saved as debug_timeout.png")
        return []

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    records = []
    for i, row in enumerate(rows[:n]):
        try:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 8:
                continue
            raw_name = cols[2].text.strip().split("\n")
            name = raw_name[0]
            symbol = raw_name[1] if len(raw_name) > 1 else ""
            price = cols[3].text.strip()
            change_24h = cols[4].text.strip()
            market_cap = cols[7].text.strip()

            rec = {
                "rank": cols[1].text.strip(),
                "name": name,
                "symbol": symbol,
                "price": parse_money(price),
                "change_24h": parse_percent(change_24h),
                "market_cap": parse_money(market_cap),
            }
            records.append(rec)
        except Exception as e:
            print(f"⚠️ Failed to parse row {i}: {e}")
    return records


# ---------- DATA UTILITIES ----------
def save_to_csv(records: List[Dict], output_file: str):
    """Append scraped data to CSV with timestamp."""
    if not records:
        return
    df = pd.DataFrame(records)
    df["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    header = not os.path.exists(output_file)
    df.to_csv(output_file, mode="a", header=header, index=False)


def filter_top_gainers(df: pd.DataFrame, top_k: int = 5):
    return df.sort_values(by="change_24h", ascending=False).head(top_k)


def filter_top_losers(df: pd.DataFrame, top_k: int = 5):
    return df.sort_values(by="change_24h", ascending=True).head(top_k)


def filter_by_price(df: pd.DataFrame, min_price: Optional[float] = None, max_price: Optional[float] = None):
    if min_price is not None:
        df = df[df["price"] >= min_price]
    if max_price is not None:
        df = df[df["price"] <= max_price]
    return df


# ---------- MAIN LOOP ----------
def main(args):
    driver = None
    try:
        driver = build_driver(headless=args.headless)
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Browser ready. Starting continuous tracking...")

        while True:
            try:
                records = scrape_top_n(driver, n=args.topn, timeout=args.timeout)
                if not records:
                    print("⚠️ No data found this cycle.")
                else:
                    save_to_csv(records, args.output)
                    df = pd.DataFrame(records)

                    print("\n✅ Latest Market Snapshot:")
                    print(df[["rank", "name", "symbol", "price", "change_24h", "market_cap"]].to_string(index=False))

                    # ---- Filters ----
                    if args.min_price or args.max_price:
                        df_filtered = filter_by_price(df, args.min_price, args.max_price)
                        if not df_filtered.empty:
                            print("\n💰 Coins Matching Price Filter:")
                            print(df_filtered[["name", "symbol", "price", "change_24h"]].to_string(index=False))
                        else:
                            print("\n💰 No coins matched the price filter.")

                    if args.show_gainers:
                        gainers = filter_top_gainers(df, args.show_gainers)
                        print(f"\n🚀 Top {args.show_gainers} Gainers:")
                        print(gainers[["name", "symbol", "change_24h"]].to_string(index=False))

                    if args.show_losers:
                        losers = filter_top_losers(df, args.show_losers)
                        print(f"\n📉 Top {args.show_losers} Losers:")
                        print(losers[["name", "symbol", "change_24h"]].to_string(index=False))

            except Exception as e:
                print("Error during scrape:", e)

            print(f"\n⏳ Waiting {args.interval} seconds before next scrape...\n")
            try:
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n🛑 Auto-tracking stopped by user.")
                break

    except WebDriverException as e:
        print("WebDriver error:", e)
    finally:
        if driver:
            driver.quit()
            print("Browser closed.")


# ---------- CLI ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full Cryptocurrency Price Tracker (All Features, Seconds Interval)")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--topn", type=int, default=10, help="Number of top coins to scrape")
    parser.add_argument("--output", type=str, default="crypto_prices.csv", help="CSV output file")
    parser.add_argument("--timeout", type=int, default=30, help="Page load timeout (seconds)")
    parser.add_argument("--interval", type=int, default=10, help="Seconds between scrapes")
    parser.add_argument("--show-gainers", type=int, default=5, help="Show top K gainers each run")
    parser.add_argument("--show-losers", type=int, default=5, help="Show top K losers each run")
    parser.add_argument("--min-price", type=float, default=None, help="Minimum price filter")
    parser.add_argument("--max-price", type=float, default=None, help="Maximum price filter")
    args = parser.parse_args()
    main(args)
