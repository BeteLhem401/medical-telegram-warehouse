# 🏥 Medical Telegram Data Warehouse

An end-to-end ELT pipeline for Ethiopian medical business intelligence, built on public Telegram channel data.

**Built for:** 10 Academy Week 8 Challenge | Kara Solutions  
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
PostgreSQL         ← raw schema
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
git clone https://github.com/YOUR_USERNAME/medical-telegram-warehouse.git
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

---

## 📁 Project Structure

```
medical-telegram-warehouse/
├── .env.example              # Credential template
├── .gitignore                # Protects secrets and data
├── requirements.txt          # Python dependencies
├── README.md
├── data/
│   └── raw/
│       ├── telegram_messages/
│       │   └── YYYY-MM-DD/
│       │       └── channel_name.json
│       └── images/
│           └── channel_name/
│               └── message_id.jpg
├── src/
│   └── scraper.py            # Task 1: Telegram scraper
├── medical_warehouse/        # Task 3: dbt project (coming soon)
├── api/                      # Task 5: FastAPI (coming soon)
├── logs/                     # Scraping activity logs
└── tests/                    # Unit tests
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
| `@tikvahethiopia` | Pharmaceuticals |
| `@CheMed123` | Medical products |

---

## 📋 Task Progress

- [x] Task 1 — Data Scraping & Collection
- [ ] Task 2 — PostgreSQL Data Warehouse
- [ ] Task 3 — dbt Star Schema Transformation
- [ ] Task 4 — YOLO Image Enrichment
- [ ] Task 5 — FastAPI Analytical API
- [ ] Task 6 — Dagster Orchestration

---

## ⚠️ Important Notes

- **Never commit `.env`** — it contains your API credentials
- **Never commit `*.session`** — it contains your Telegram session token
- The `data/` directory is gitignored — data stays local
- Run the scraper responsibly — respect Telegram's rate limits
