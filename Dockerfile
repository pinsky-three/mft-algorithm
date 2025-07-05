FROM freqtradeorg/freqtrade:stable

# Set working directory
WORKDIR /freqtrade

# Create user_data directory structure
RUN mkdir -p /freqtrade/user_data/logs

# Expose API port
EXPOSE 8080

# Set up volume for user_data
VOLUME ["/freqtrade/user_data"]

# Default command - runs freqtrade with the same parameters as in docker-compose
CMD ["trade", \
     "--logfile", "/freqtrade/user_data/logs/freqtrade.log", \
     "--db-url", "sqlite:////freqtrade/user_data/tradesv3.sqlite", \
     "--config", "/freqtrade/user_data/config.json", \
     "--strategy", "SampleStrategy"]

