"""Injectable candle data source protocol — follows D028.

Provides:
- ``CandleDataSource``: runtime-checkable Protocol for async candle fetching.
- ``MockCandleDataSource``: deterministic test source with configurable batch delivery.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CandleDataSource(Protocol):
    """Async interface for fetching OHLCV candle data."""

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str, since: int | None = None, limit: int = 100
    ) -> list[list[float | int]]: ...


class MockCandleDataSource:
    """Deterministic candle source for testing.

    Feeds candles from a pre-built list, advancing an internal pointer
    on each call to simulate streaming data.

    Each candle is ``[timestamp, open, high, low, close, volume]``.

    Args:
        candles: Full list of candle data.
        batch_size: Number of candles returned per ``fetch_ohlcv`` call.
    """

    def __init__(
        self, candles: list[list[float | int]], batch_size: int | None = None
    ) -> None:
        self.candles = candles
        self.batch_size = batch_size or len(candles)
        self._pointer = 0

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str, since: int | None = None, limit: int = 100
    ) -> list[list[float | int]]:
        """Return the next batch of candles.

        Returns all candles up to the current pointer + batch_size.
        """
        end = min(self._pointer + self.batch_size, len(self.candles))
        result = self.candles[: end]
        self._pointer = end
        return result
