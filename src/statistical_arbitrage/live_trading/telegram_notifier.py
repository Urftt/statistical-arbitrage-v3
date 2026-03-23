"""Telegram notification sender for live trading events.

Sends fire-and-forget HTML-formatted messages to a Telegram chat via the
Bot API.  All HTTP errors are caught and logged — a notification failure
never crashes the trading loop.

Usage::

    notifier = TelegramNotifier(bot_token="123:ABC", chat_id="-100123")
    await notifier.send_fill(order_event)
    await notifier.close()
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from statistical_arbitrage.live_trading.models import (
    ErrorEvent,
    OrderEvent,
    RiskBreachEvent,
)

logger = logging.getLogger(__name__)

# Telegram Bot API base URL — token is appended at runtime.
_API_BASE = "https://api.telegram.org/bot"


class TelegramNotifier:
    """Async Telegram notification sender using httpx.

    Parameters
    ----------
    bot_token:
        Telegram Bot API token from @BotFather.  Empty string disables
        the notifier (graceful no-op).
    chat_id:
        Target chat or group ID.  Empty string disables the notifier.
    """

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._client = httpx.AsyncClient(timeout=10.0)
        self._enabled = bool(bot_token and chat_id)

        if not self._enabled:
            logger.warning(
                "TelegramNotifier disabled: %s",
                "token not configured" if not bot_token else "chat_id not configured",
            )
        else:
            logger.info("TelegramNotifier enabled (token configured, chat_id configured)")

    # ------------------------------------------------------------------
    # Public send methods — one per event type
    # ------------------------------------------------------------------

    async def send_fill(self, event: OrderEvent) -> None:
        """Format and send an order-fill notification."""
        order = event.order
        text = (
            "<b>🔔 Order Filled</b>\n\n"
            f"<b>Session:</b> <code>{event.session_id}</code>\n"
            f"<b>Side:</b> {order.side}\n"
            f"<b>Symbol:</b> {order.symbol}\n"
            f"<b>Amount:</b> {order.filled_amount:.6f}\n"
            f"<b>Price:</b> €{order.fill_price:.4f}\n"
            f"<b>Fee:</b> €{order.fee:.4f}\n"
            f"<b>Status:</b> {order.status}\n"
            f"<b>Position:</b> {event.position_after}"
        )
        await self._send(text)

    async def send_error(self, event: ErrorEvent) -> None:
        """Format and send a trading-error notification."""
        text = (
            "<b>🚨 Trading Error</b>\n\n"
            f"<b>Session:</b> <code>{event.session_id}</code>\n"
            f"<b>Type:</b> {event.error_type}\n"
            f"<b>Message:</b> {event.message}\n"
            f"<b>Time:</b> {event.timestamp.isoformat()}"
        )
        await self._send(text)

    async def send_risk_breach(self, event: RiskBreachEvent) -> None:
        """Format and send a risk-limit-breach notification."""
        text = (
            "<b>⚠️ Risk Limit Breach</b>\n\n"
            f"<b>Session:</b> <code>{event.session_id}</code>\n"
            f"<b>Limit:</b> {event.check_result.limit_type}\n"
            f"<b>Reason:</b> {event.check_result.reason}\n"
            f"<b>Order:</b> {event.order_details}"
        )
        await self._send(text)

    async def send_daily_summary(self, summary: dict[str, Any]) -> None:
        """Format and send a daily trading summary notification."""
        text = (
            "<b>📊 Daily Trading Summary</b>\n\n"
            f"<b>Date:</b> {summary.get('date', 'N/A')}\n"
            f"<b>Total P&L:</b> €{summary.get('total_pnl', 0.0):.2f}\n"
            f"<b>Trades:</b> {summary.get('trade_count', 0)}\n"
            f"<b>Sessions:</b> {summary.get('session_count', 0)}"
        )
        await self._send(text)

    # ------------------------------------------------------------------
    # Internal transport
    # ------------------------------------------------------------------

    async def _send(self, text: str) -> None:
        """POST *text* to the Telegram sendMessage endpoint.

        All exceptions are caught and logged at WARNING level — this method
        never raises.  When the notifier is disabled (empty token or chat_id),
        returns immediately without making an HTTP call.
        """
        if not self._enabled:
            return

        url = f"{_API_BASE}{self._bot_token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Telegram message sent successfully")
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Telegram send failed (HTTP %s): %s",
                exc.response.status_code,
                exc,
            )
        except httpx.ConnectError as exc:
            logger.warning("Telegram send failed (connection error): %s", exc)
        except httpx.TimeoutException as exc:
            logger.warning("Telegram send failed (timeout): %s", exc)
        except Exception as exc:
            logger.warning(
                "Telegram send failed (unexpected %s): %s",
                type(exc).__name__,
                exc,
            )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying httpx.AsyncClient."""
        await self._client.aclose()
