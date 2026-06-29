# 🏥 Medical Telegram Data Warehouse

An end-to-end ELT pipeline for Ethiopian medical business intelligence, built on public Telegram channel data.

**Stack:** Python · Telethon · PostgreSQL · dbt · YOLOv8 · FastAPI · Dagster

---

## 📐 Architecture

```
Telegram Channels
      │  (Telethon scraper)
      ▼
Data Lake          ← data/raw/  (JSON + images)
      │  (SQLAlchemy loader)
      ▼
PostgreSQL         ← raw_messages table
      │  (dbt)
      ▼
Star Schema        ← staging → marts
      │  (YOLO enrichment)
      ▼
Enriched Marts     ← object detection results
      │  (FastAPI)
      ▼
Analytical API     ← /api/v1/...
```

---

## 🚀 Quickstart

### 1. Clone and set up environment

```bash
git clone https://github.com/BeteLhem401/medical-telegram-warehouse.git
cd medical-telegram-warehouse

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your Telegram API credentials
# Get them at: https://my.telegram.org
```

### 3. Run the scraper

```bash
python src/scraper.py
```

On first run, Telegram will send you a verification code via SMS/app.
Enter it in the terminal. A `telegram_session.session` file is created — **never commit this.**

### 4. Start the database

```bash
docker-compose up -d
```

### 5. Load data into PostgreSQL

```bash
python src/load_to_postgres.py
```

### 6. Run dbt transformations

```bash
cd medical_warehouse
dbt run
```

---

## 📁 Project Structure

```
medical-telegram-warehouse/
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── README.md
├── src/
│   ├── scraper.py
│   ├── load_to_postgres.py
│   └── yolo_detect.py
├── medical_warehouse/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/
│       │   └── stg_telegram_messages.sql
│       └── marts/
│           └── fct_messages.sql
├── api/
│   ├── main.py
│   ├── database.py
│   └── schemas.py
├── tests/
│   └── test_scraper_utils.py
├── data/
│   └── raw/
│       ├── telegram_messages/
│       │   └── YYYY-MM-DD/
│       │       └── channel_name.json
│       └── images/
│           └── channel_name/
│               └── message_id.jpg
└── logs/
```

---

## 📊 Data Lake Schema

Each message is stored as a JSON object:

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | int | Unique Telegram message ID |
| `channel_name` | str | Source channel username |
| `message_date` | ISO datetime | When the message was posted |
| `message_text` | str | Full text content |
| `has_media` | bool | Whether message has attached media |
| `image_path` | str or null | Local path to downloaded image |
| `views` | int | View count |
| `forwards` | int | Forward count |

---

## 🎯 Target Channels

| Channel | Focus |
|---------|-------|
| `@lobelia4cosmetics` | Cosmetics & health products |
| `@tikvahpharma` | Pharmaceuticals |
| `@CheMed123` | Medical products |

---

## ⚠️ Important Notes

- **Never commit `.env`** — it contains your API credentials
- **Never commit `*.session`** — it contains your Telegram session token
- The `data/` directory is gitignored — data stays local
- Run the scraper responsibly — respect Telegram's rate limits
