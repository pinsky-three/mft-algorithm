FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade

# Copy user data
COPY ./user_data /freqtrade/user_data

# Switch to root for setup
USER root

# # CRITICAL: Backup freqtrade source before Railway volume mounting destroys it
# RUN echo "Backing up freqtrade source for Railway compatibility..." && \
#     cp -r /freqtrade/freqtrade /usr/local/lib/python3.13/site-packages/ && \
#     echo "Freqtrade source backed up to Python site-packages"

# # Create logs directory, set permissions, and ensure config exists
# RUN mkdir -p ./user_data/logs && \
#     chmod -R 777 ./user_data && \
#     chown -R ftuser:ftuser ./user_data

# # Verify freqtrade installation and create startup script to handle Railway volume mounts
# RUN echo "Checking Python and freqtrade installation..." && \
#     python -c "import freqtrade; print('freqtrade module found at:', freqtrade.__file__)" && \
#     which python && \
#     python --version && \
#     echo "Python environment verified"

# # Create Railway startup script that uses backed up freqtrade source
# RUN echo '#!/bin/sh' > /usr/local/bin/freqtrade-railway && \
#     echo 'echo "=== Railway Freqtrade Startup ==="' >> /usr/local/bin/freqtrade-railway && \
#     echo 'echo "Python: $(which python) ($(python --version 2>&1))"' >> /usr/local/bin/freqtrade-railway && \
#     echo 'echo "Working dir: $(pwd)"' >> /usr/local/bin/freqtrade-railway && \
#     echo '' >> /usr/local/bin/freqtrade-railway && \
#     echo '# Try standard PYTHONPATH first' >> /usr/local/bin/freqtrade-railway && \
#     echo 'echo "Trying standard freqtrade import..."' >> /usr/local/bin/freqtrade-railway && \
#     echo 'export PYTHONPATH="/freqtrade:$PYTHONPATH"' >> /usr/local/bin/freqtrade-railway && \
#     echo 'cd /freqtrade' >> /usr/local/bin/freqtrade-railway && \
#     echo 'python -c "import freqtrade" 2>/dev/null' >> /usr/local/bin/freqtrade-railway && \
#     echo 'if [ $? -eq 0 ]; then' >> /usr/local/bin/freqtrade-railway && \
#     echo '  echo "Using standard freqtrade installation"' >> /usr/local/bin/freqtrade-railway && \
#     echo 'else' >> /usr/local/bin/freqtrade-railway && \
#     echo '  echo "Standard freqtrade not available (likely due to Railway volume mounting)"' >> /usr/local/bin/freqtrade-railway && \
#     echo '  echo "Using backed up freqtrade from Python site-packages"' >> /usr/local/bin/freqtrade-railway && \
#     echo '  # Remove /freqtrade from PYTHONPATH' >> /usr/local/bin/freqtrade-railway && \
#     echo '  export PYTHONPATH=$(echo "$PYTHONPATH" | sed "s|/freqtrade:||g")' >> /usr/local/bin/freqtrade-railway && \
#     echo '  python -c "import freqtrade" 2>/dev/null' >> /usr/local/bin/freqtrade-railway && \
#     echo '  if [ $? -eq 0 ]; then' >> /usr/local/bin/freqtrade-railway && \
#     echo '    echo "Freqtrade successfully loaded from backup"' >> /usr/local/bin/freqtrade-railway && \
#     echo '  else' >> /usr/local/bin/freqtrade-railway && \
#     echo '    echo "Even backup failed. System info:"' >> /usr/local/bin/freqtrade-railway && \
#     echo '    python -c "import sys; print(\"Python path:\"); [print(\"  \", p) for p in sys.path]"' >> /usr/local/bin/freqtrade-railway && \
#     echo '    ls -la /usr/local/lib/python3.13/site-packages/ | grep freqtrade || echo "No freqtrade in site-packages"' >> /usr/local/bin/freqtrade-railway && \
#     echo '  fi' >> /usr/local/bin/freqtrade-railway && \
#     echo 'fi' >> /usr/local/bin/freqtrade-railway && \
#     echo '' >> /usr/local/bin/freqtrade-railway && \

#     echo 'if [ ! -f "./user_data/config.json" ]; then' >> /usr/local/bin/freqtrade-railway && \
#     echo 'echo \'{"max_open_trades": 3, "stake_currency": "USDT", "stake_amount": 50, "tradable_balance_ratio": 0.99, "fiat_display_currency": "USD", "dry_run": true, "dry_run_wallet": 1000, "cancel_open_orders_on_exit": false, "trading_mode": "spot", "margin_mode": "", "unfilledtimeout": {"entry": 10, "exit": 10, "exit_timeout_count": 0, "unit": "minutes"}, "entry_pricing": {"price_side": "same", "use_order_book": true, "order_book_top": 1, "price_last_balance": 0.0, "check_depth_of_market": {"enabled": false, "bids_to_ask_delta": 1}}, "exit_pricing": {"price_side": "same", "use_order_book": true, "order_book_top": 1}, "exchange": {"name": "binance", "key": "", "secret": "", "ccxt_config": {}, "ccxt_async_config": {}, "pair_whitelist": ["BTC/USDT", "ETH/USDT", "SOL/USDT"], "pair_blacklist": []}, "pairlists": [{"method": "StaticPairList"}], "edge": {"enabled": false}, "telegram": {"enabled": false, "token": "", "chat_id": ""}, "api_server": {"enabled": true, "listen_ip_address": "0.0.0.0", "listen_port": 8080, "verbosity": "error", "enable_openapi": false, "jwt_secret_key": "your-secret-key-here", "CORS_origins": [], "username": "", "password": ""}, "bot_name": "freqtrade", "initial_state": "running", "force_entry_enable": false, "internals": {"process_throttle_secs": 5}}\' > ./user_data/config.json && \\' >> /usr/local/bin/freqtrade-railway && \
#     echo 'chown ftuser:ftuser ./user_data/config.json;' >> /usr/local/bin/freqtrade-railway && \
#     echo 'fi' >> /usr/local/bin/freqtrade-railway && \

#     echo 'echo "=== Starting freqtrade ==="' >> /usr/local/bin/freqtrade-railway && \
#     echo 'exec python -m freqtrade "$@"' >> /usr/local/bin/freqtrade-railway

# RUN chmod +x /usr/local/bin/freqtrade-railway


# Switch back to ftuser for security
USER ftuser

EXPOSE 8080

# Use our Railway-compatible script that handles volume mounting
ENTRYPOINT ["freqtrade-railway"]

CMD ["trade", \
     "--logfile", "./user_data/logs/freqtrade.log", \
     "--db-url", "sqlite:///./user_data/tradesv3.sqlite", \
     "--config", "./user_data/config.json", \
     "--strategy", "CryptoScalpingOptimizedJuly"]