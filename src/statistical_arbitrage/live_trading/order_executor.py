"""Order execution abstraction — injectable protocol following D028 (CandleDataSource).

Provides:
- ``OrderExecutor``: runtime-checkable Protocol (not an ABC) defining the async
  interface every executor must satisfy.
- ``MockOrderExecutor``: deterministic executor for testing — configurable fills,
  error injection, and full submission recording.
- ``BitvavoOrderExecutor``: production executor using authenticated async CCXT
  against the Bitvavo exchange.
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

import ccxt
import ccxt.async_support as ccxt_async

from statistical_arbitrage.live_trading.models import LiveOrder

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def round_to_significant_figures(value: float, sig_figs: int = 5) -> float:
    """Round *value* to *sig_figs* significant figures.

    Bitvavo requires amounts with at most 5 significant figures.

    Args:
        value: The number to round.
        sig_figs: Number of significant figures (default 5).

    Returns:
        Rounded float.
    """
    if value == 0:
        return 0.0
    magnitude = math.floor(math.log10(abs(value)))
    factor = 10 ** (sig_figs - 1 - magnitude)
    return round(value * factor) / factor


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class OrderExecutor(Protocol):
    """Async interface for order submission and balance queries.

    Implementations must be injectable — the engine only depends on this
    protocol, never on a concrete class.
    """

    async def submit_order(
        self, symbol: str, side: str, amount: float
    ) -> LiveOrder: ...

    async def fetch_balance(self) -> dict[str, dict[str, float]]: ...

    async def cancel_order(self, order_id: str, symbol: str) -> bool: ...

    async def close(self) -> None: ...


# ---------------------------------------------------------------------------
# Mock implementation (tests)
# ---------------------------------------------------------------------------


class MockOrderExecutor:
    """Deterministic executor for unit / integration tests.

    Attributes:
        submitted_orders: List of every ``LiveOrder`` returned by
            ``submit_order`` — lets tests assert on call history.
    """

    def __init__(
        self,
        default_fill_price: float = 100.0,
        default_fee_rate: float = 0.0025,
        error_on_next_order: Exception | None = None,
        balance: dict[str, dict[str, float]] | None = None,
    ) -> None:
        self.default_fill_price = default_fill_price
        self.default_fee_rate = default_fee_rate
        self.error_on_next_order = error_on_next_order
        self.balance = balance or {
            "EUR": {"free": 1000.0, "used": 0.0, "total": 1000.0}
        }
        self.submitted_orders: list[LiveOrder] = []
        self._closed = False

    async def submit_order(
        self, symbol: str, side: str, amount: float
    ) -> LiveOrder:
        if self.error_on_next_order is not None:
            err = self.error_on_next_order
            self.error_on_next_order = None  # one-shot
            raise err

        fill_price = self.default_fill_price
        cost = amount * fill_price
        fee = cost * self.default_fee_rate
        now = datetime.now(UTC)

        order = LiveOrder(
            order_id=str(uuid.uuid4()),
            session_id="mock-session",
            side=side,  # type: ignore[arg-type]
            symbol=symbol,
            requested_amount=amount,
            filled_amount=amount,
            fill_price=fill_price,
            fee=fee,
            status="filled",
            created_at=now,
            filled_at=now,
        )
        self.submitted_orders.append(order)
        return order

    async def fetch_balance(self) -> dict[str, dict[str, float]]:
        return self.balance

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        return True

    async def close(self) -> None:
        self._closed = True


# ---------------------------------------------------------------------------
# Bitvavo production implementation
# ---------------------------------------------------------------------------


class BitvavoOrderExecutor:
    """Production executor using ``ccxt.async_support.bitvavo``.

    Handles:
    - 5-significant-figure amount rounding (Bitvavo constraint)
    - Fill price extraction: ``order['average']`` → ``cost / filled`` fallback
    - CCXT exception classification with clear error messages

    Args:
        api_key: Bitvavo API key.
        api_secret: Bitvavo API secret.
        sandbox: If True, use Bitvavo sandbox/testnet (default False).
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        sandbox: bool = False,
    ) -> None:
        self._exchange = ccxt_async.bitvavo(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
            }
        )
        if sandbox:
            self._exchange.set_sandbox_mode(True)

    # -- public interface ---------------------------------------------------

    async def submit_order(
        self, symbol: str, side: str, amount: float
    ) -> LiveOrder:
        """Submit a market order on Bitvavo.

        Args:
            symbol: Trading pair, e.g. ``"BTC/EUR"``.
            side: ``"buy"`` or ``"sell"``.
            amount: Quantity in base currency.

        Returns:
            Populated ``LiveOrder`` with fill details.

        Raises:
            ccxt.InsufficientFunds: Account balance too low.
            ccxt.InvalidOrder: Order violates exchange rules (e.g. below min).
            ccxt.NetworkError: Connectivity issue — caller decides retry policy.
            ccxt.ExchangeNotAvailable: Exchange is down.
        """
        rounded_amount = round_to_significant_figures(amount, 5)
        now = datetime.now(UTC)

        try:
            raw = await self._exchange.create_market_order(
                symbol, side, rounded_amount
            )
        except ccxt.InsufficientFunds as exc:
            logger.error(
                "Insufficient funds for %s %s %s: %s",
                side, rounded_amount, symbol, exc,
            )
            raise
        except ccxt.InvalidOrder as exc:
            logger.error(
                "Invalid order %s %s %s: %s",
                side, rounded_amount, symbol, exc,
            )
            raise
        except ccxt.NetworkError as exc:
            logger.error("Network error submitting order: %s", exc)
            raise
        except ccxt.ExchangeNotAvailable as exc:
            logger.error("Exchange not available: %s", exc)
            raise

        fill_price = self._extract_fill_price(raw)
        filled_amount = float(raw.get("filled", rounded_amount))
        cost = float(raw.get("cost", filled_amount * fill_price))
        fee_info = raw.get("fee") or {}
        fee = float(fee_info.get("cost", 0.0))

        status: str
        if filled_amount >= rounded_amount:
            status = "filled"
        elif filled_amount > 0:
            status = "partial"
        else:
            status = "failed"

        return LiveOrder(
            order_id=str(raw.get("id", uuid.uuid4())),
            session_id="",  # caller sets session_id
            side=side,  # type: ignore[arg-type]
            symbol=symbol,
            requested_amount=rounded_amount,
            filled_amount=filled_amount,
            fill_price=fill_price,
            fee=fee,
            status=status,  # type: ignore[arg-type]
            created_at=now,
            filled_at=datetime.now(UTC) if status == "filled" else None,
        )

    async def fetch_balance(self) -> dict[str, dict[str, float]]:
        """Query account balances.

        Returns:
            ``{currency: {free, used, total}}`` for every held currency.
        """
        raw = await self._exchange.fetch_balance()
        result: dict[str, dict[str, float]] = {}
        for currency, details in raw.items():
            if isinstance(details, dict) and "free" in details:
                result[currency] = {
                    "free": float(details.get("free", 0)),
                    "used": float(details.get("used", 0)),
                    "total": float(details.get("total", 0)),
                }
        return result

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel a pending order.

        Returns:
            ``True`` if the cancellation was acknowledged by the exchange.
        """
        try:
            await self._exchange.cancel_order(order_id, symbol)
            return True
        except ccxt.OrderNotFound:
            logger.warning("Order %s not found for cancellation", order_id)
            return False
        except ccxt.NetworkError as exc:
            logger.error("Network error cancelling order %s: %s", order_id, exc)
            raise

    async def close(self) -> None:
        """Close the underlying CCXT exchange connection."""
        await self._exchange.close()

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _extract_fill_price(raw: dict) -> float:
        """Extract fill price from a CCXT order response.

        Priority: ``average`` → ``cost / filled`` → 0.0 fallback.
        """
        avg = raw.get("average")
        if avg is not None:
            return float(avg)

        cost = raw.get("cost")
        filled = raw.get("filled")
        if cost is not None and filled is not None and float(filled) > 0:
            return float(cost) / float(filled)

        return 0.0
