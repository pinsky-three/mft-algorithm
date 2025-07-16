FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade

# Copy user data
COPY ./user_data /freqtrade/user_data

# Copy startup script as backup
COPY startup.sh /freqtrade/startup.sh

# Switch to root to modify permissions
USER root

# Create logs directory, set permissions, and ensure config exists
RUN mkdir -p ./user_data/logs && \
    chmod -R 777 ./user_data && \
    chmod +x /freqtrade/startup.sh && \
    chown -R ftuser:ftuser ./user_data && \
    ls -la /freqtrade/startup.sh && \
    echo "Startup script verified and made executable"

# Create default config if it doesn't exist (simplified approach)
RUN if [ ! -f "./user_data/config.json" ]; then \
        echo '{"max_open_trades": 3, "stake_currency": "USDT", "stake_amount": 50, "tradable_balance_ratio": 0.99, "fiat_display_currency": "USD", "dry_run": true, "dry_run_wallet": 1000, "cancel_open_orders_on_exit": false, "trading_mode": "spot", "margin_mode": "", "unfilledtimeout": {"entry": 10, "exit": 10, "exit_timeout_count": 0, "unit": "minutes"}, "entry_pricing": {"price_side": "same", "use_order_book": true, "order_book_top": 1, "price_last_balance": 0.0, "check_depth_of_market": {"enabled": false, "bids_to_ask_delta": 1}}, "exit_pricing": {"price_side": "same", "use_order_book": true, "order_book_top": 1}, "exchange": {"name": "binance", "key": "", "secret": "", "ccxt_config": {}, "ccxt_async_config": {}, "pair_whitelist": ["BTC/USDT", "ETH/USDT", "SOL/USDT"], "pair_blacklist": []}, "pairlists": [{"method": "StaticPairList"}], "edge": {"enabled": false}, "telegram": {"enabled": true, "token": "", "chat_id": ""}, "api_server": {"enabled": true, "listen_ip_address": "0.0.0.0", "listen_port": 8080, "verbosity": "error", "enable_openapi": false, "jwt_secret_key": "your-secret-key-here", "CORS_origins": [], "username": "", "password": ""}, "bot_name": "freqtrade", "initial_state": "running", "force_entry_enable": false, "internals": {"process_throttle_secs": 5}}' > ./user_data/config.json && \
        chown ftuser:ftuser ./user_data/config.json; \
    fi

# Switch back to ftuser for security
USER ftuser

EXPOSE 8080

# Use direct freqtrade command instead of startup script to avoid Railway issues
ENTRYPOINT ["freqtrade"]

CMD ["trade", \
     "--logfile", "./user_data/logs/freqtrade.log", \
     "--db-url", "sqlite:///./user_data/tradesv3.sqlite", \
     "--config", "./user_data/config.json", \
     "--strategy", "CryptoScalpingOptimizedJuly"]