# 📈 Stock News Alert

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Requests](https://img.shields.io/badge/requests-HTTP%20Client-green)](https://docs.python-requests.org/)
[![python-dotenv](https://img.shields.io/badge/python--dotenv-env%20loader-2ea44f)](https://pypi.org/project/python-dotenv/)
[![AlphaVantage](https://img.shields.io/badge/API-Alpha%20Vantage-orange)](https://www.alphavantage.co/)
[![NewsAPI](https://img.shields.io/badge/API-NewsAPI-red)](https://newsapi.org/)
[![Twilio](https://img.shields.io/badge/SMS-Twilio-purple)](https://www.twilio.com/)
[![Version](https://img.shields.io/badge/version-v1.0.0-informational)](https://github.com/natalnetwork/stock_news)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight stock monitoring tool that:

-   Fetches daily stock data from **Alpha Vantage**
-   Calculates percentage change using **Decimal** precision
-   Triggers an alert if a configurable threshold is exceeded
-   Retrieves related news from **NewsAPI**
-   Sends alerts to:
    -   Terminal
    -   SMS (Twilio)
    -   Email (SMTP)
    -   Or multiple outputs simultaneously

------------------------------------------------------------------------

## 🏷 Version

-   Current project version: **v1.0.0**

------------------------------------------------------------------------

## 🚀 Features

-   Free-tier compatible (`TIME_SERIES_DAILY`)
-   Financial-precision math (`Decimal`)
-   Clean modular architecture (`stock.py`, `news.py`)
-   CLI-based multi-output system
-   Environment-based secret management
-   Production-ready error handling

------------------------------------------------------------------------

## 📂 Project Structure

    stock-news-alert/
    ├── stock_news.py        # CLI entrypoint
    ├── cli_parser.py        # CLI argument parsing + normalization
    ├── alert_service.py     # Core workflow orchestration per symbol
    ├── app_types.py         # Shared lightweight type models
    ├── constants.py         # Configurable constants
    ├── stock.py             # Alpha Vantage logic
    ├── news.py              # NewsAPI client
    ├── report_formatter.py  # Report + SMS text formatting
    ├── notifiers.py         # SMS/Email notifier classes
    ├── requirements.txt
    ├── .env.example
    ├── .gitignore
    └── .env                 # NOT COMMITTED

------------------------------------------------------------------------

## 🧱 Architecture

-   `stock_news.py`: thin entrypoint (CLI mode routing + startup checks)
-   `cli_parser.py`: parses CLI args and normalizes symbols/output targets
-   `alert_service.py`: runs the stock→news→report→notify flow
-   `stock.py` + `news.py`: external API clients
-   `report_formatter.py`: terminal/email report and SMS message formatting
-   `notifiers.py`: Twilio + SMTP adapters with environment-based config
-   `app_types.py`: shared types for parser/service boundaries

------------------------------------------------------------------------

## 🛠 Setup

### 1) Create Virtual Environment

``` bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install Dependencies

``` bash
pip install -r requirements.txt
```

### 3) Configure Environment Variables

Create `.env`:

    ALPHAVANTAGE_KEY=...
    NEWSAPI_KEY=...

    # Twilio (optional)
    TWILIO_ACCOUNT_SID=...
    # or: TWILIO_SID=...
    TWILIO_AUTH_TOKEN=...
    TWILIO_FROM_NUMBER=+1...
    # or: TWILIO_PHONE=+1...

    # SMTP (optional)
    SMTP_HOST=mail.example.com
    SMTP_PORT=465
    SMTP_USER=...
    SMTP_PASSWORD=...
    SMTP_FROM=...

------------------------------------------------------------------------

## 💻 Usage

### Terminal (default)

``` bash
python stock_news.py
```

### SMS

``` bash
python stock_news.py --output sms:+5584991974595
```

### Email

``` bash
python stock_news.py --output email:test@gmail.com
```

### SMTP Test (ohne API Calls)

``` bash
python stock_news.py --send-test-email test@gmail.com
```

### Twilio SMS Test (ohne API Calls)

``` bash
python stock_news.py --send-test-sms +5584991974595
```

### Twilio SMS Test mit eigener Nachricht

``` bash
python stock_news.py --send-test-sms +5584991974595 --test-message "Hallo vom Stock Alert"
```

### Multiple Outputs

``` bash
python stock_news.py   --output terminal   --output sms:+5584991974595   --output email:test@gmail.com
```

### Multiple Symbols (optional alias)

``` bash
python stock_news.py --symbols TSLA="Tesla" IBM --output terminal
```

### Force News Fetch (ignore threshold)

``` bash
python stock_news.py --symbols TSLA="Tesla" IBM --output terminal --ignore-threshold
```

------------------------------------------------------------------------

## ⚙ Configuration

Edit `constants.py`:

-   `PRICE_CHANGE_THRESHOLD_PCT`
-   `NEWS_TERMS`
-   `NEWS_LIMIT`

------------------------------------------------------------------------

## ⚠ Notes

-   Alpha Vantage free tier is rate-limited.
-   NewsAPI free plan has limited historical access.
-   One SMS per article (template compliant).
-   SMTP uses SSL (port 465 typical).

------------------------------------------------------------------------

## 📄 License

MIT License