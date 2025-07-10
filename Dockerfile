FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade
COPY ./user_data /freqtrade/user_data
COPY startup.sh /freqtrade/startup.sh

USER root

RUN apt-get update && apt-get install -y su-exec && \
    chmod -R 777 ./user_data/logs || true && \
    rm -rf ./user_data/logs && \
    mkdir -p ./user_data/logs && \
    chmod -R 777 ./user_data && \
    chmod +x /freqtrade/startup.sh

EXPOSE 8080

ENTRYPOINT ["/freqtrade/startup.sh"] 

CMD ["trade", \
     "--logfile", "./user_data/logs/freqtrade.log", \
     "--db-url", "sqlite:///./user_data/tradesv3.sqlite", \
     "--config", "./user_data/config.json", \
     "--strategy", "MultiHorizonMomentumStrategy"]