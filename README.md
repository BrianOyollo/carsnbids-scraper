# CarsnBids_scraper

**carsnbids_scraper** is a component of a data engineering pipeline that scrapes vehicle auction data from [carsandbids.com](https://carsandbids.com), stores the raw data in Amazon S3, and tracks progress using a local SQLite database. It sends phone notifications via [ntfy.sh](https://ntfy.sh) and is built using [uv](https://github.com/astral-sh/uv) for fast dependency and environment management.

This scraper is designed to run automatically on an AWS EC2 instance.

## 📌 Project Structure

```bash

carsnbids_scraper/
├── .python-version          # Python version for uv environment
├── main.py                  # Alternate entry point (uv project root)
├── pyproject.toml           # uv/PEP 621 project config
├── uv.lock                  # uv dependency lock file
│
├── src/                         # Current version of the scraper
│   ├── driver_setup.py          # WebDriver setup for Selenium
│   ├── logger.py                # Logging setup
│   ├── main.py                  # Entry-point script
│   ├── notify.py                # Sends notifications via ntfy
│   ├── scrape_auction_urls.py  # Scrapes auction URLs
│   ├── scrape_auction.py       # Scrapes detailed auction data
│   ├── sqlite_setup.py         # Initializes and manages SQLite DB
│   └── utils.py                # General utility functions
│
├── v2/                      # Old version (archived)                 # Entry-point script for v2
├── requirements.txt
└── README.md
```

---

## 🚀 Features

- Scrapes completed auctions from carsandbids.com using Selenium
  
- Runs on an AWS EC2 instance
  
- Prevents duplicate scraping using a local SQLite database
  
- Uploads raw JSON auction data to Amazon S3
  
- Sends real-time notifications via ntfy
  
- Uses `uv` for environment and dependency management
  

---

## 🔧 Setup & Installation

### Prerequisites

- Python 3.13+
  
- [uv]([Installation | uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer)) installed (install via `pipx` or directly):
  

### 1. Clone the repository

```bash
git clone https://github.com/BrianOyollo/Cars-and-Bids.git
cd src
```

### 2. Set up the project environment with `uv`

```bash
uv sync
```

### 3. Set up environment variables

Create a `.env` file in the root directory or use environment variables directly:

```bash
RAW_AUCTIONS_BUCKET=      # Name of the S3 bucket to store raw auction data
AWS_ACCESS_KEY_ID=        # AWS access key ID for S3 upload permissions
AWS_SECRET_ACCESS_KEY=    # AWS secret access key corresponding to the access key ID
SQLITE_DB_PATH=           # Path to the local SQLite database used for tracking scraped URLs. Defaults to carsnbids.db
MAX_PAGES_TO_SCRAPE=     # Maximum number of listing pages to scrape during a run. Default is 6
NTFY_TOPIC=               # Topic name for sending notifications via ntfy.sh (https://docs.ntfy.sh/)
```

### 4. Initialize SQLite DB

```bash
cd src/
uv run sqlite_setup.py
```

### 4. Run the scraper

```bash
cd src/
uv run main.py
```

---

## 📲 Notifications

The project uses [ntfy.sh](https://ntfy.sh) to send push notifications to your phone. See a simple setup [here](https://docs.ntfy.sh/). Add the topic created to env variable under `NTFY_TOPIC`

---

## 📦 Tools

| Tool / Library | Purpose |
| --- | --- |
| **Selenium** | Automates browser interaction to scrape auction listings from [carsandbids.com](https://carsandbids.com) |
| **SQLite** | Lightweight local database to track already scraped auction URLs |
| **boto3** | AWS SDK for Python used to upload raw auction data to Amazon S3 |
| **ntfy** | Sends push notifications to your phone via [ntfy.sh](https://ntfy.sh) |
| **pandas** | (Used in the broader pipeline) for data cleaning and transformation in later stages |
| **uv** | Fast Python package manager and virtual environment tool for managing dependencies and isolation |
| **python-dotenv** | Loads environment variables from a `.env` file |

---

## 🗃️ Part of a Bigger Pipeline

This scraper is the **first stage** in a broader data engineering project focused on vehicle auction data from carsandbids.com.

---

## Educational Use

This project is **strictly for educational purposes** — designed to practice and demonstrate data engineering skills.

It is **not affiliated with carsandbids.com.**

## 📬 Contact

Have questions or feedback? Reach out at [oyollobrian@gmail.com](oyollobrian@gmail.com)