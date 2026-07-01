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
Analytical API     ← /api/...
      │  (Dagster)
      ▼
Orchestrated Pipeline ← scheduled, monitored runs
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
dbt test
```

### 7. Run object detection enrichment

```bash
python src/yolo_detect.py
python src/load_yolo_to_postgres.py
```

### 8. Start the analytical API

```bash
uvicorn api.main:app --reload
```

Docs available at `http://127.0.0.1:8000/docs`

### 9. Run the orchestrated pipeline

```bash
dagster dev -f pipeline.py
```

UI available at `http://localhost:3000`

---

## 📁 Project Structure

```
medical-telegram-warehouse/
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── pipeline.py
├── README.md
├── src/
│   ├── scraper.py
│   ├── load_to_postgres.py
│   ├── yolo_detect.py
│   └── load_yolo_to_postgres.py
├── medical_warehouse/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/
│       │   └── stg_telegram_messages.sql
│       └── marts/
│           ├── dim_channels.sql
│           ├── dim_dates.sql
│           ├── fct_messages.sql
│           ├── fct_image_detections.sql
│           └── schema.yml
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
├── docs/
│   ├── project-report.md
│   └── screenshots/
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

## ⭐ Star Schema (Warehouse Layer)

**Dimensions:** `dim_channels`, `dim_dates`
**Facts:** `fct_messages`, `fct_image_detections`

`fct_image_detections` adds YOLOv8 object-detection results, joined to `fct_messages` on `message_id`, with a derived `image_category` (`promotional` / `product_display` / `lifestyle` / `other`).

23 dbt tests cover `unique`, `not_null`, `relationships`, `accepted_values`, plus one custom test (`assert_no_future_messages`).

---

## 🖼️ Object Detection Enrichment (YOLOv8)

```bash
python src/yolo_detect.py              # detect objects in scraped images
python src/load_yolo_to_postgres.py    # load results into raw schema
```

Detected objects are classified into `promotional` / `product_display` / `lifestyle` / `other` and joined to messages via `models/marts/fct_image_detections.sql`.

---

## 🔌 Analytical API

```bash
uvicorn api.main:app --reload
```

Docs: `http://127.0.0.1:8000/docs`

| Endpoint | Purpose |
|---|---|
| `GET /api/reports/top-products` | Most frequently mentioned terms |
| `GET /api/channels/{channel_name}/activity` | Per-channel post stats |
| `GET /api/search/messages?query=...` | Keyword search across messages |
| `GET /api/reports/visual-content` | % of posts with images, by channel |

---

## ⚙️ Pipeline Orchestration (Dagster)

```bash
dagster dev -f pipeline.py
```

UI: `http://localhost:3000`

Job `medical_warehouse_pipeline` runs four ops in order:

```
scrape_telegram_data → load_raw_to_postgres → run_yolo_enrichment → run_dbt_transformations
```

Scheduled daily at 06:00 UTC, with a failure sensor that logs alerts on any failed run.

---

## ✅ Testing

```bash
cd medical_warehouse
dbt test
```

23 tests covering `unique`, `not_null`, `relationships`, `accepted_values`, and one custom business-rule test (`assert_no_future_messages`).

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
- **Never commit `yolov8n.pt`** — it's a model weights binary, kept out of git
- The `data/` directory is gitignored — data stays local
- Run the scraper responsibly — respect Telegram's rate limits