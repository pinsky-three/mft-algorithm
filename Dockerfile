FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade

# Copy user data
COPY ./user_data /freqtrade/user_data

# Copy startup script as backup
COPY startup.sh /freqtrade/startup.sh

# Switch to root to modify permissions and fix python path issues
USER root

# Create logs directory, set permissions, and ensure config exists
RUN mkdir -p ./user_data/logs && \
    chmod -R 777 ./user_data && \
    chmod +x /freqtrade/startup.sh && \
    chown -R ftuser:ftuser ./user_data && \
    ls -la /freqtrade/startup.sh && \
    echo "Startup script verified and made executable"

# Fix potential Python path issues for Railway environment
RUN echo "Checking Python and freqtrade installation..." && \
    python -c "import freqtrade; print('freqtrade module found')" && \
    which python && \
    python --version && \
    ls -la /home/ftuser/.local/bin/freqtrade || echo "Binary not found" && \
    echo "Python environment verified"

# Create default config if it doesn't exist (simplified approach)
RUN if [ ! -f "./user_data/config.json" ]; then \
        echo '{"max_open_trades": 3, "stake_currency": "USDT", "stake_amount": 0.01, "tradable_balance_ratio": 0.99, "fiat_display_currency": "USD", "dry_run": true, "dry_run_wallet": 1000, "cancel_open_orders_on_exit": false, "trading_mode": "spot", "margin_mode": "", "unfilledtimeout": {"entry": 10, "exit": 10, "exit_timeout_count": 0, "unit": "minutes"}, "entry_pricing": {"price_side": "same", "use_order_book": true, "order_book_top": 1, "price_last_balance": 0.0, "check_depth_of_market": {"enabled": false, "bids_to_ask_delta": 1}}, "exit_pricing": {"price_side": "same", "use_order_book": true, "order_book_top": 1}, "exchange": {"name": "binance", "key": "", "secret": "", "ccxt_config": {}, "ccxt_async_config": {}, "pair_whitelist": ["BTC/USDT", "ETH/USDT", "SOL/USDT"], "pair_blacklist": []}, "pairlists": [{"method": "StaticPairList"}], "edge": {"enabled": false}, "telegram": {"enabled": false, "token": "", "chat_id": ""}, "api_server": {"enabled": true, "listen_ip_address": "0.0.0.0", "listen_port": 8080, "verbosity": "error", "enable_openapi": false, "jwt_secret_key": "your-secret-key-here", "CORS_origins": [], "username": "", "password": ""}, "bot_name": "freqtrade", "initial_state": "running", "force_entry_enable": false, "internals": {"process_throttle_secs": 5}}' > ./user_data/config.json && \
        chown ftuser:ftuser ./user_data/config.json; \
    fi

# Create a robust entrypoint script that handles multiple execution methods
RUN printf '#!/bin/bash\n\
echo "Starting freqtrade with Railway-compatible execution..."\n\
\n\
# Method 1: Try the standard freqtrade binary\n\
if command -v freqtrade >/dev/null 2>&1; then\n\
    echo "Using freqtrade binary"\n\
    exec freqtrade "$@"\n\
fi\n\
\n\
# Method 2: Try python module execution\n\
if python -c "import freqtrade" >/dev/null 2>&1; then\n\
    echo "Using python module execution"\n\
    exec python -m freqtrade "$@"\n\
fi\n\
\n\
# Method 3: Try direct module path\n\
if [ -f "/usr/local/lib/python3.11/site-packages/freqtrade/__main__.py" ]; then\n\
    echo "Using direct module path"\n\
    exec python /usr/local/lib/python3.11/site-packages/freqtrade/__main__.py "$@"\n\
fi\n\
\n\
echo "ERROR: Could not find freqtrade installation"\n\
exit 1\n' > /freqtrade/entrypoint-railway.sh

RUN chmod +x /freqtrade/entrypoint-railway.sh

# Switch back to ftuser for security
USER ftuser

EXPOSE 8080

# Use our robust entrypoint script for Railway compatibility
ENTRYPOINT ["/freqtrade/entrypoint-railway.sh"]

CMD ["trade", \
     "--logfile", "./user_data/logs/freqtrade.log", \
     "--db-url", "sqlite:///./user_data/tradesv3.sqlite", \
     "--config", "./user_data/config.json", \
     "--strategy", "CryptoScalpingOptimizedJuly"]