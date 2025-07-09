FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade
COPY ./user_data /freqtrade/user_data

USER root

RUN chmod -R 777 ./user_data/logs || true && \
    rm -rf ./user_data/logs && \
    mkdir -p ./user_data/logs && \
    chmod -R 777 ./user_data

USER ftuser

EXPOSE 8080

CMD ["trade", \
     "--logfile", "./user_data/logs/freqtrade.log", \
     "--db-url", "sqlite:////./user_data/tradesv3.sqlite", \
     "--config", "./user_data/config.json", \
     "--strategy", "SampleStrategy"]