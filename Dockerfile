FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade

# Copy user data and startup script
COPY ./user_data /freqtrade/user_data
COPY startup.sh /freqtrade/startup.sh

# Switch to root to modify permissions
USER root

# Create logs directory and set permissions (remove su-exec dependency)
RUN mkdir -p ./user_data/logs && \
    chmod -R 777 ./user_data && \
    chmod +x /freqtrade/startup.sh && \
    chown -R ftuser:ftuser ./user_data

# Switch back to ftuser for security
USER ftuser

EXPOSE 8080

ENTRYPOINT ["/freqtrade/startup.sh"] 

CMD ["trade", \
     "--logfile", "./user_data/logs/freqtrade.log", \
     "--db-url", "sqlite:///./user_data/tradesv3.sqlite", \
     "--config", "./user_data/config.json", \
     "--strategy", "CryptoScalpingOptimizedJuly"]