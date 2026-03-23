"""Tests for RiskManager — all 4 limit types, approved/rejected paths, boundary values."""

from __future__ import annotations

import pytest

from statistical_arbitrage.live_trading.risk_manager import RiskManager


@pytest.fixture
def risk_manager() -> RiskManager:
    """Default RiskManager with standard limits."""
    return RiskManager(
        max_position_size_eur=25.0,
        max_concurrent_positions=2,
        daily_loss_limit_eur=50.0,
        min_order_size_eur=5.0,
    )


class TestRiskManagerRejections:
    def test_below_minimum_order_size(self, risk_manager: RiskManager):
        result = risk_manager.check_order(
            order_amount_eur=3.0, current_positions=0, daily_realized_loss=0.0
        )
        assert result.approved is False
        assert result.limit_type == "min_order_size"
        assert "below minimum" in result.reason.lower()

    def test_above_max_position_size(self, risk_manager: RiskManager):
        result = risk_manager.check_order(
            order_amount_eur=30.0, current_positions=0, daily_realized_loss=0.0
        )
        assert result.approved is False
        assert result.limit_type == "max_position_size"
        assert "exceeds max" in result.reason.lower()

    def test_too_many_concurrent_positions(self, risk_manager: RiskManager):
        result = risk_manager.check_order(
            order_amount_eur=10.0, current_positions=2, daily_realized_loss=0.0
        )
        assert result.approved is False
        assert result.limit_type == "max_concurrent_positions"
        assert "concurrent" in result.reason.lower()

    def test_daily_loss_limit_breached(self, risk_manager: RiskManager):
        result = risk_manager.check_order(
            order_amount_eur=10.0, current_positions=0, daily_realized_loss=55.0
        )
        assert result.approved is False
        assert result.limit_type == "daily_loss_limit"
        assert "daily" in result.reason.lower()


class TestRiskManagerApprovals:
    def test_order_approved_when_all_limits_pass(self, risk_manager: RiskManager):
        result = risk_manager.check_order(
            order_amount_eur=10.0, current_positions=0, daily_realized_loss=0.0
        )
        assert result.approved is True
        assert result.reason is None
        assert result.limit_type is None

    def test_boundary_exactly_at_max_position_size(self, risk_manager: RiskManager):
        """Order exactly at max_position_size should be approved (not exceeded)."""
        result = risk_manager.check_order(
            order_amount_eur=25.0, current_positions=0, daily_realized_loss=0.0
        )
        assert result.approved is True

    def test_boundary_daily_loss_exactly_at_limit(self, risk_manager: RiskManager):
        """Daily loss exactly at the limit should be rejected (>= threshold)."""
        result = risk_manager.check_order(
            order_amount_eur=10.0, current_positions=0, daily_realized_loss=50.0
        )
        assert result.approved is False
        assert result.limit_type == "daily_loss_limit"


class TestRiskManagerFromSettings:
    def test_from_settings(self):
        """Verify from_settings class method wires values correctly."""

        class FakeSettings:
            max_position_size_eur = 100.0
            max_concurrent_positions = 5
            daily_loss_limit_eur = 200.0
            min_order_size_eur = 10.0

        rm = RiskManager.from_settings(FakeSettings())
        assert rm.max_position_size_eur == 100.0
        assert rm.max_concurrent_positions == 5
        assert rm.daily_loss_limit_eur == 200.0
        assert rm.min_order_size_eur == 10.0


class TestRiskManagerCheckOrder:
    def test_check_order_priority_min_size_first(self):
        """When multiple limits would fail, min_order_size is checked first."""
        rm = RiskManager(
            max_position_size_eur=2.0,  # would also fail
            max_concurrent_positions=0,  # would also fail
            daily_loss_limit_eur=0.0,  # would also fail
            min_order_size_eur=5.0,
        )
        result = rm.check_order(
            order_amount_eur=3.0, current_positions=1, daily_realized_loss=10.0
        )
        # min_order_size is checked first
        assert result.limit_type == "min_order_size"
