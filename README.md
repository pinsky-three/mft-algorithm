# FreqTrade Docker Setup

This repository contains a Dockerfile for running FreqTrade, a free and open-source cryptocurrency trading bot.

## About FreqTrade

FreqTrade is a cryptocurrency algorithmic trading software developed in Python. It allows you to run trading strategies and backtest them using historical data.

## Getting Started

### Prerequisites

- Docker installed on your system
- Basic understanding of cryptocurrency trading
- FreqTrade configuration files

### Building the Docker Image

```bash
docker build -t freqtrade-custom .
```

### Running the Container

#### Basic Run
```bash
docker run -d \
  --name freqtrade \
  --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  -v ./user_data:/freqtrade/user_data \
  freqtrade-custom
```

#### With Custom Configuration
```bash
docker run -d \
  --name freqtrade \
  --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  -v ./user_data:/freqtrade/user_data \
  freqtrade-custom \
  trade \
  --config /freqtrade/user_data/config.json \
  --strategy YourCustomStrategy
```

### Directory Structure

Make sure you have the following directory structure in your project:

```
.
├── Dockerfile
├── README.md
└── user_data/
    ├── config.json
    ├── strategies/
    │   └── SampleStrategy.py
    ├── logs/
    └── data/
```

### Configuration

1. **Config File**: Place your `config.json` in the `user_data/` directory
2. **Strategies**: Place your trading strategies in `user_data/strategies/`
3. **Logs**: Trading logs will be stored in `user_data/logs/`
4. **Database**: SQLite database will be created in `user_data/`

### Default Configuration

The Dockerfile is configured with the following defaults:
- **Log file**: `/freqtrade/user_data/logs/freqtrade.log`
- **Database**: SQLite at `/freqtrade/user_data/tradesv3.sqlite`
- **Config**: `/freqtrade/user_data/config.json`
- **Strategy**: `SampleStrategy`
- **API Port**: 8080 (localhost only)

### API Access

The FreqTrade REST API is exposed on port 8080 (localhost only). You can access it at:
- `http://localhost:8080/api/v1/`

For API documentation, visit: https://www.freqtrade.io/en/stable/rest-api/

### Docker Compose Alternative

If you prefer using Docker Compose, create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  freqtrade:
    build: .
    container_name: freqtrade
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - "./user_data:/freqtrade/user_data"
```

Then run:
```bash
docker-compose up -d
```

### Common Commands

#### View Logs
```bash
docker logs freqtrade
```

#### Stop Container
```bash
docker stop freqtrade
```

#### Start Container
```bash
docker start freqtrade
```

#### Execute Commands in Container
```bash
docker exec -it freqtrade /bin/bash
```

#### Run Backtesting
```bash
docker run --rm \
  -v ./user_data:/freqtrade/user_data \
  freqtrade-custom \
  backtesting \
  --config /freqtrade/user_data/config.json \
  --strategy SampleStrategy
```

### Customization

To customize the image further:

1. **Add Dependencies**: Modify the Dockerfile to install additional Python packages
2. **Custom Strategies**: Place your strategies in `user_data/strategies/`
3. **Configuration**: Modify `user_data/config.json` for your trading preferences

### Security Notes

- The API is bound to localhost only (127.0.0.1:8080)
- Never expose the API port publicly without proper authentication
- Keep your API keys secure and never commit them to version control

### Troubleshooting

1. **Permission Issues**: Ensure the `user_data` directory has proper permissions
2. **Config Errors**: Check your `config.json` syntax
3. **Strategy Errors**: Verify your strategy file is in the correct location

### Useful Links

- [FreqTrade Documentation](https://www.freqtrade.io/)
- [FreqTrade GitHub](https://github.com/freqtrade/freqtrade)
- [Strategy Examples](https://github.com/freqtrade/freqtrade-strategies)

### License

This project follows the same license as FreqTrade. Please refer to the FreqTrade repository for license information. 