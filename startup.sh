#!/bin/bash

# Check if config.json exists in user_data, if not create it
if [ ! -f "./user_data/config.json" ]; then
    echo "Config file not found, creating default config.json..."
    mkdir -p ./user_data
    
    # Create a basic config.json directly in user_data (running as root)
    cat > ./user_data/config.json << 'EOF'
{
    "max_open_trades": 3,
    "stake_currency": "USDT",
    "stake_amount": 0.01,
    "tradable_balance_ratio": 0.99,
    "fiat_display_currency": "USD",
    "dry_run": true,
    "dry_run_wallet": 1000,
    "cancel_open_orders_on_exit": false,
    "trading_mode": "spot",
    "margin_mode": "",
    "unfilledtimeout": {
        "entry": 10,
        "exit": 10,
        "exit_timeout_count": 0,
        "unit": "minutes"
    },
    "entry_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1,
        "price_last_balance": 0.0,
        "check_depth_of_market": {
            "enabled": false,
            "bids_to_ask_delta": 1
        }
    },
    "exit_pricing": {
        "price_side": "same",
        "use_order_book": true,
        "order_book_top": 1
    },
    "exchange": {
        "name": "binance",
        "key": "",
        "secret": "",
        "ccxt_config": {},
        "ccxt_async_config": {},
        "pair_whitelist": [
            "BTC/USDT",
            "ETH/USDT",
            "ADA/USDT",
            "DOT/USDT",
            "LINK/USDT"
        ],
        "pair_blacklist": []
    },
    "pairlists": [
        {
            "method": "StaticPairList"
        }
    ],
    "edge": {
        "enabled": false,
        "process_throttle_secs": 3600,
        "calculate_since_number_of_days": 7,
        "allowed_risk": 0.01,
        "stoploss_range_min": -0.01,
        "stoploss_range_max": -0.1,
        "stoploss_range_step": -0.01,
        "minimum_winrate": 0.60,
        "minimum_expectancy": 0.20,
        "min_trade_number": 10,
        "max_trade_duration_minute": 1440,
        "remove_pumps": false
    },
    "telegram": {
        "enabled": true,
        "token": "",
        "chat_id": ""
    },
    "api_server": {
        "enabled": true,
        "listen_ip_address": "0.0.0.0",
        "listen_port": 8080,
        "verbosity": "error",
        "enable_openapi": false,
        "jwt_secret_key": "your-secret-key-here",
        "CORS_origins": [],
        "username": "",
        "password": ""
    },
    "bot_name": "freqtrade",
    "initial_state": "running",
    "force_entry_enable": false,
    "internals": {
        "process_throttle_secs": 5
    }
}
EOF
    # Set proper ownership and permissions for ftuser
    chown -R ftuser:ftuser ./user_data
    chmod -R 755 ./user_data
    chmod 644 ./user_data/config.json
    echo "Created default config.json"
fi

# Ensure proper ownership of user_data directory
chown -R ftuser:ftuser ./user_data 2>/dev/null || true

# Switch to ftuser and start freqtrade with the provided arguments
exec su-exec ftuser freqtrade "$@" 