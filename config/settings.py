"""
Configuration settings for the statistical arbitrage platform.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class BitvavoSettings(BaseSettings):
    """Bitvavo API configuration settings."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API credentials
    bitvavo_api_key: str = Field(default="", description="Bitvavo API key")
    bitvavo_api_secret: str = Field(default="", description="Bitvavo API secret")

    # API endpoints
    bitvavo_rest_url: str = Field(
        default="https://api.bitvavo.com/v2",
        description="Bitvavo REST API URL"
    )
    bitvavo_ws_url: str = Field(
        default="wss://ws.bitvavo.com/v2/",
        description="Bitvavo WebSocket URL"
    )

    # Rate limiting
    rate_limit_per_second: int = Field(
        default=10,
        description="Maximum API requests per second"
    )

    # Data collection defaults
    default_interval: str = Field(
        default="1h",
        description="Default candle interval"
    )
    default_limit: int = Field(
        default=1000,
        description="Default number of candles per request"
    )


class DataSettings(BaseSettings):
    """Data storage and processing settings."""

    # Data directories
    data_root: Path = Field(default=PROJECT_ROOT / "data")
    raw_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "raw")
    processed_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "processed")
    results_dir: Path = Field(default=PROJECT_ROOT / "data" / "results")

    # File formats
    data_format: Literal["parquet", "csv"] = Field(
        default="parquet",
        description="Default data storage format"
    )

    # Processing settings
    use_polars: bool = Field(
        default=True,
        description="Use Polars instead of Pandas for data processing"
    )


class StrategySettings(BaseSettings):
    """Trading strategy configuration."""

    # Initial pairs for analysis
    initial_pairs: list[str] = Field(
        default=["ETH-EUR", "ETC-EUR"],
        description="Initial cryptocurrency pairs to analyze"
    )

    # Pairs trading parameters
    lookback_window: int = Field(
        default=60,
        description="Lookback window for spread calculation (in periods)"
    )
    entry_threshold: float = Field(
        default=2.0,
        description="Z-score threshold for entering positions"
    )
    exit_threshold: float = Field(
        default=0.5,
        description="Z-score threshold for exiting positions"
    )
    stop_loss: float = Field(
        default=3.0,
        description="Z-score threshold for stop-loss"
    )

    # Backtesting parameters
    initial_capital: float = Field(
        default=10000.0,
        description="Initial capital for backtesting (EUR)"
    )
    position_size: float = Field(
        default=0.5,
        description="Fraction of capital per position (0-1)"
    )
    transaction_fee: float = Field(
        default=0.0025,
        description="Transaction fee as decimal (0.25% = 0.0025)"
    )


class LiveTradingSettings(BaseSettings):
    """Risk limits and defaults for live trading on Bitvavo.

    Conservative defaults: small position sizes, strict loss limits.
    All EUR amounts are portfolio-level unless noted otherwise.
    """

    max_position_size_eur: float = Field(
        default=25.0,
        description="Maximum EUR value per single trade (€25 default)",
    )
    max_concurrent_positions: int = Field(
        default=2,
        description="Maximum number of open positions at once",
    )
    daily_loss_limit_eur: float = Field(
        default=50.0,
        description="Portfolio-level daily realized loss limit (EUR)",
    )
    min_order_size_eur: float = Field(
        default=5.0,
        description="Bitvavo minimum order size (EUR)",
    )
    default_trade_size_eur: float = Field(
        default=10.0,
        description="Default trade size when no override is given (EUR)",
    )


class TelegramSettings(BaseSettings):
    """Telegram Bot API configuration for trade notifications.

    Empty defaults = notifications disabled (graceful no-op).
    Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in config/.env to enable.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    telegram_bot_token: str = Field(
        default="",
        description="Telegram Bot API token (from @BotFather)",
    )
    telegram_chat_id: str = Field(
        default="",
        description="Telegram chat/group ID to send notifications to",
    )


class Settings(BaseSettings):
    """Main application settings."""

    bitvavo: BitvavoSettings = Field(default_factory=BitvavoSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    strategy: StrategySettings = Field(default_factory=StrategySettings)
    live_trading: LiveTradingSettings = Field(default_factory=LiveTradingSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)

    # General settings
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")


# Singleton settings instance
settings = Settings()
