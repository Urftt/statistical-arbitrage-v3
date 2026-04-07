"""
Data cache manager — query the API once, cache forever, only fetch deltas.

Architecture:
- raw/     → Exactly what came from the API (individual fetch chunks)
- cache/   → Merged continuous timeseries per symbol/timeframe (single parquet per combo)
- Each cache file stores metadata: last_updated timestamp, total candle count

Usage:
    cache = DataCacheManager()
    df = cache.get_candles("ETH/EUR", "1h", days_back=90)  # Fetches from API first time
    df = cache.get_candles("ETH/EUR", "1h", days_back=90)  # Instant — reads from cache
    cache.refresh("ETH/EUR", "1h")  # Fetches only new candles since last update
"""

import time
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl

from config.settings import settings


class DataCacheManager:
    """
    Manages cached OHLCV data with incremental API updates.
    
    Data flow:
    1. get_candles() checks cache first
    2. If cache miss or stale, fetches from API via CCXT
    3. Merges new data into cache (deduplicates by timestamp)
    4. Returns full dataset from cache
    """

    TIMEFRAME_MS = {
        "1m": 60_000,
        "5m": 300_000,
        "15m": 900_000,
        "30m": 1_800_000,
        "1h": 3_600_000,
        "2h": 7_200_000,
        "4h": 14_400_000,
        "6h": 21_600_000,
        "8h": 28_800_000,
        "12h": 43_200_000,
        "1d": 86_400_000,
    }

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or settings.data.data_root / "cache"
        self.raw_dir = settings.data.raw_data_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._client = None

    @property
    def client(self):
        """Lazy-init CCXT client — only created when we actually need API access."""
        if self._client is None:
            import ccxt
            self._client = ccxt.bitvavo({"enableRateLimit": True})
        return self._client

    def _cache_path(self, symbol: str, timeframe: str) -> Path:
        """Get cache file path for a symbol/timeframe combo."""
        safe_symbol = symbol.replace("/", "-")
        return self.cache_dir / f"{safe_symbol}_{timeframe}.parquet"

    def _meta_path(self, symbol: str, timeframe: str) -> Path:
        """Get metadata file path."""
        safe_symbol = symbol.replace("/", "-")
        return self.cache_dir / f"{safe_symbol}_{timeframe}.meta.json"

    def has_cache(self, symbol: str, timeframe: str) -> bool:
        """Check if we have cached data for this symbol/timeframe."""
        return self._cache_path(symbol, timeframe).exists()

    def get_cache_info(self, symbol: str, timeframe: str) -> dict | None:
        """Get info about cached data."""
        path = self._cache_path(symbol, timeframe)
        if not path.exists():
            return None
        
        df = pl.read_parquet(path)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": len(df),
            "start": df["datetime"].min(),
            "end": df["datetime"].max(),
            "file_size_mb": round(path.stat().st_size / 1_048_576, 2),
        }

    def list_cached(self) -> list[dict]:
        """List all cached datasets."""
        results = []
        for path in sorted(self.cache_dir.glob("*.parquet")):
            # Parse filename: SYMBOL_TIMEFRAME.parquet
            stem = path.stem  # e.g., "ETH-EUR_1h"
            parts = stem.rsplit("_", 1)
            if len(parts) == 2:
                symbol = parts[0].replace("-", "/")
                timeframe = parts[1]
                info = self.get_cache_info(symbol, timeframe)
                if info:
                    results.append(info)
        return results

    def _fetch_from_api(
        self,
        symbol: str,
        timeframe: str,
        since_ms: int | None = None,
        until_ms: int | None = None,
    ) -> pl.DataFrame:
        """
        Fetch OHLCV data from Bitvavo API with pagination.
        
        Args:
            symbol: Trading pair (e.g., 'ETH/EUR')
            timeframe: Candle interval (e.g., '1h')
            since_ms: Start timestamp in milliseconds
            until_ms: End timestamp in milliseconds (default: now)
        """
        if until_ms is None:
            until_ms = int(datetime.now().timestamp() * 1000)

        all_candles = []
        current_since = since_ms
        max_limit = 1000

        while current_since is not None and current_since < until_ms:
            ohlcv = self.client.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=current_since,
                limit=max_limit,
            )

            if not ohlcv:
                break

            all_candles.extend(ohlcv)

            last_ts = ohlcv[-1][0]
            if last_ts >= until_ms or len(ohlcv) < max_limit:
                break

            # Move past last candle
            current_since = last_ts + self.TIMEFRAME_MS.get(timeframe, 3_600_000)

        if not all_candles:
            return pl.DataFrame(
                schema={
                    "datetime": pl.Datetime("ns"),
                    "timestamp": pl.Int64,
                    "open": pl.Float64,
                    "high": pl.Float64,
                    "low": pl.Float64,
                    "close": pl.Float64,
                    "volume": pl.Float64,
                }
            )

        df = pl.DataFrame(
            {
                "timestamp": [c[0] for c in all_candles],
                "open": [float(c[1]) for c in all_candles],
                "high": [float(c[2]) for c in all_candles],
                "low": [float(c[3]) for c in all_candles],
                "close": [float(c[4]) for c in all_candles],
                "volume": [float(c[5]) for c in all_candles],
            }
        )

        df = df.with_columns(
            (pl.col("timestamp") * 1_000_000).cast(pl.Datetime("ns")).alias("datetime")
        )
        df = df.select(["datetime", "timestamp", "open", "high", "low", "close", "volume"])
        df = df.unique(subset=["timestamp"]).sort("timestamp")

        # Filter to requested range
        if until_ms:
            df = df.filter(pl.col("timestamp") <= until_ms)

        return df

    def get_candles(
        self,
        symbol: str,
        timeframe: str = "1h",
        days_back: int = 90,
        force_refresh: bool = False,
    ) -> pl.DataFrame:
        """
        Get candle data — from cache if available, otherwise fetches from API.
        
        This is the main entry point. It:
        1. Checks cache for existing data
        2. Fetches missing data from API (only the gap)
        3. Merges and saves to cache
        4. Returns the full dataset
        
        Args:
            symbol: Trading pair (e.g., 'ETH/EUR')
            timeframe: Candle interval (e.g., '1h', '4h', '1d')
            days_back: How many days of history to ensure we have
            force_refresh: Ignore cache and re-fetch everything
            
        Returns:
            Polars DataFrame with OHLCV data
        """
        cache_path = self._cache_path(symbol, timeframe)
        target_start_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
        now_ms = int(datetime.now().timestamp() * 1000)

        existing_df = None
        needs_fetch = True
        fetch_since = target_start_ms

        # Check cache
        if not force_refresh and cache_path.exists():
            existing_df = pl.read_parquet(cache_path)
            if not existing_df.is_empty():
                cache_start = existing_df["timestamp"].min()
                cache_end = existing_df["timestamp"].max()

                # Do we need older data?
                if cache_start <= target_start_ms:
                    # Cache covers the start. Do we need newer data?
                    # Only fetch if cache is more than 1 candle behind
                    gap_ms = now_ms - cache_end
                    candle_ms = self.TIMEFRAME_MS.get(timeframe, 3_600_000)
                    
                    if gap_ms <= candle_ms * 2:
                        # Cache is fresh enough
                        needs_fetch = False
                    else:
                        # Only fetch the delta
                        fetch_since = cache_end + candle_ms
                else:
                    # Need older data — fetch from target start to cache start
                    fetch_since = target_start_ms

        if needs_fetch:
            print(f"📡 Fetching {symbol} {timeframe} data from API...")
            new_df = self._fetch_from_api(symbol, timeframe, since_ms=fetch_since, until_ms=now_ms)

            if existing_df is not None and not existing_df.is_empty() and not new_df.is_empty():
                # Merge with existing cache
                df = pl.concat([existing_df, new_df])
                df = df.unique(subset=["timestamp"]).sort("timestamp")
            elif not new_df.is_empty():
                df = new_df
            elif existing_df is not None:
                df = existing_df
            else:
                return pl.DataFrame()

            # Save to cache
            df.write_parquet(cache_path)
            print(f"💾 Cached {len(df)} candles → {cache_path.name}")
        else:
            df = existing_df

        # Filter to requested range
        df = df.filter(pl.col("timestamp") >= target_start_ms)

        return df

    def refresh(self, symbol: str, timeframe: str) -> pl.DataFrame:
        """Force refresh — fetch latest data and merge with cache."""
        return self.get_candles(symbol, timeframe, days_back=365, force_refresh=False)

    def refresh_all(self) -> dict[str, int]:
        """Refresh all cached datasets."""
        results = {}
        for info in self.list_cached():
            symbol = info["symbol"]
            timeframe = info["timeframe"]
            df = self.refresh(symbol, timeframe)
            results[f"{symbol}_{timeframe}"] = len(df)
        return results

    def get_available_pairs(self) -> pl.DataFrame:
        """Get all EUR trading pairs on Bitvavo, ranked by market cap (descending).

        Market cap is pulled from CoinGecko's free `/coins/markets` endpoint
        (denominated in EUR) and cross-referenced with Bitvavo's live EUR market
        list so only pairs actually tradeable on Bitvavo are returned.

        Returns a DataFrame with columns: symbol, base, quote, market_cap,
        quote_volume. Rows are sorted by `market_cap` descending so callers that
        take the first N rows get the N largest crypto assets available on
        Bitvavo (BTC, ETH, XRP, SOL, ...). Pairs without a CoinGecko match or
        with zero market cap are ranked last (ordered by 24h quote_volume as a
        tie-breaker).

        Falls back to quote_volume-only ranking if CoinGecko is unreachable.
        """
        markets = self.client.load_markets()
        tickers = self.client.fetch_tickers()

        # 1. Pull top coins by market cap from CoinGecko (EUR-denominated).
        #    Free tier allows unauthenticated requests; 250 rows is enough to
        #    rank every Bitvavo EUR listing that has a CoinGecko entry.
        market_cap_by_base: dict[str, float] = {}
        try:
            import urllib.request
            import json as _json

            url = (
                "https://api.coingecko.com/api/v3/coins/markets"
                "?vs_currency=eur&order=market_cap_desc&per_page=250&page=1&sparkline=false"
            )
            req = urllib.request.Request(
                url, headers={"User-Agent": "statistical-arbitrage-v3/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                coingecko_rows = _json.loads(resp.read())
            for row in coingecko_rows:
                base = (row.get("symbol") or "").upper()
                mcap = row.get("market_cap") or 0
                if base and mcap:
                    market_cap_by_base[base] = float(mcap)
        except Exception:
            # CoinGecko unreachable — fall through to quote_volume-only ranking.
            market_cap_by_base = {}

        # 2. Build the Bitvavo EUR pair list, enriched with market cap + volume.
        pairs = []
        for symbol, info in markets.items():
            if info.get("quote") != "EUR" or not info.get("active", True):
                continue
            base = info.get("base") or ""
            ticker = tickers.get(symbol) or {}
            quote_volume = ticker.get("quoteVolume")
            pairs.append({
                "symbol": symbol,
                "base": base,
                "quote": info.get("quote"),
                "market_cap": market_cap_by_base.get(base.upper(), 0.0),
                "quote_volume": float(quote_volume) if quote_volume is not None else 0.0,
            })

        return pl.DataFrame(pairs).sort(
            ["market_cap", "quote_volume"], descending=[True, True]
        )

    def bulk_download(
        self,
        symbols: list[str],
        timeframe: str = "1h",
        days_back: int = 90,
    ) -> dict[str, pl.DataFrame]:
        """
        Download data for multiple symbols at once.
        
        Args:
            symbols: List of trading pairs
            timeframe: Candle interval
            days_back: Days of history
            
        Returns:
            Dict mapping symbol → DataFrame
        """
        results = {}
        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] {symbol}...")
            try:
                df = self.get_candles(symbol, timeframe, days_back=days_back)
                results[symbol] = df
            except Exception as e:
                print(f"  ⚠️  Failed: {e}")
                results[symbol] = pl.DataFrame()
        return results


# Module-level singleton for convenience
_cache_manager: DataCacheManager | None = None


def get_cache_manager() -> DataCacheManager:
    """Get or create the singleton cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = DataCacheManager()
    return _cache_manager
