# SocialPlus.ai — Full-Stack Comment Intelligence Platform

> **"Understand Every Comment. Discover Every Insight."**

SocialPlus.ai is an enterprise-grade AI-powered Social Media and E-commerce Comment Intelligence Platform. Built from scratch with a clean, modular architecture, it extracts, classifies, moderates, and visualizes customer feedback, audience sentiment, emotional dimensions, comment intent, spam, toxicity, and product feature aspects across:
- **YouTube** (Videos, Shorts, and Channels)
- **Meta** (Instagram Professional accounts & Facebook Pages)
- **E-commerce** (Amazon India, Flipkart, Myntra, Meesho, Ajio, Snapdeal, Tata CLiQ, Nykaa, JioMart)
- **Universal File Upload** (CSV, XLSX, XLS, JSON, TXT)
- **Direct Manual Comment Input**

---

## 1. System Architecture

```
SocialPlus.AI/
├── backend/
│   ├── main.py                  # FastAPI server, CORS, route registry, static mounting
│   ├── config.py                # Pydantic BaseSettings, .env loader & status helpers
│   ├── database.py              # SQLAlchemy engine, session maker (SQLite local, PostgreSQL ready)
│   ├── models/
│   │   └── db_models.py         # AnalysisRun and CommentItem ORM models
│   ├── schemas/
│   │   └── api_schemas.py       # Pydantic validation & normalized schemas
│   ├── connectors/              # Modular Data Ingestion Layer
│   │   ├── base_connector.py    # Abstract connector & normalized data structure
│   │   ├── youtube_connector.py # YouTube Data API v3 & permitted public route
│   │   ├── instagram_connector.py # Meta Graph API v20.0 & public notice
│   │   ├── facebook_connector.py  # Meta Page Graph API & public notice
│   │   ├── ecommerce_connector.py # 9 platform adapters (Amazon, Flipkart, etc.)
│   │   ├── file_parser.py       # Auto-detecting CSV, Excel, JSON, TXT parser
│   │   └── connector_registry.py # Central factory for platform connectors
│   ├── analysis/                # Unified AI/ML Intelligence Pipeline
│   │   ├── pipeline.py          # Unified pipeline orchestrator
│   │   ├── sentiment.py         # 5-class multilingual sentiment (Pos, Neg, Neu, Mix, Sarcastic)
│   │   ├── emotion.py           # 10 emotional dimensions (Joy, Love, Anger, Trust, etc.)
│   │   ├── intent.py            # 11-class intent analyzer (Inquiry, Complaint, Request, etc.)
│   │   ├── moderation.py        # Independent Spam vs Toxicity scoring & safety status
│   │   ├── emoji_intelligence.py # Emoji extraction, sentiment mapping, frequency
│   │   ├── keywords.py          # Multilingual stopwords, n-grams, word cloud
│   │   └── aspect_analysis.py   # Dynamic Aspect-Based Sentiment Analysis (ABSA)
│   ├── services/
│   │   ├── history_service.py   # Persistence, search, and pagination in SQLite
│   │   └── report_generator.py  # PDF (ReportLab), HTML, Excel (.xlsx), CSV, JSON
│   ├── api/                     # REST API Routes
│   └── utils/
│       ├── security.py          # SSRF prevention & HTML sanitization
│       └── helpers.py           # URL & ID extractors (YouTube, Meta)
├── frontend/                    # Pure Vanilla Frontend (No React/Next.js)
│   ├── index.html               # Clean, minimalist single-page app
│   ├── css/
│   │   ├── style.css            # Professional colors, typography, cards
│   │   ├── dashboard.css        # Charts layout, tables, explorer, badges
│   │   └── responsive.css       # Mobile & tablet responsiveness
│   └── js/
│       ├── app.js               # Navigation, modals, toast alerts, health checks
│       ├── charts.js            # Chart.js visualization controllers
│       ├── youtube.js           # YouTube controller (3 modes)
│       ├── meta.js              # Instagram & Facebook controller
│       ├── ecommerce.js         # E-commerce platform search & review extractor
│       ├── upload.js            # Drag-and-drop file upload & manual input
│       └── dashboard.js         # Dashboard render, filterable comment table
├── tests/                       # Automated Pytest Suite (21/21 passing)
├── uploads/                     # File upload directory with sample datasets
├── reports/                     # Generated PDF & Excel reports directory
├── .env.example                 # Configuration template
├── requirements.txt             # Python dependencies
├── README.md                    # System documentation
└── run.py                       # Single-command startup runner
```

---

## 2. Key Features

### 2.1 Unified AI/ML Analysis Pipeline
Every comment from any source (YouTube API, public connectors, Instagram, Facebook, E-commerce, CSV/Excel/JSON upload, or manual paste) is normalized into a standard record and processed through the exact same NLP pipeline:
1. **5-Class Sentiment Intelligence**: Positive, Negative, Neutral, Mixed, Sarcastic (mutually exclusive primary distribution summing to 100%). Context-aware for English, Hindi, and Hinglish.
2. **10-Dimension Emotion Intelligence**: Joy, Love, Anger, Sadness, Surprise, Fear, Frustration, Disappointment, Excitement, Trust.
3. **Comment Intent Classifier**: Question, Product Inquiry, Support Request, Complaint, Appreciation, Suggestion, Request, Promotional, Spam, Irrelevant, General Feedback.
4. **Auto-Moderation & Safety**: Independent Spam Probability (0.0 to 1.0) and Toxicity Score (0.0 to 1.0). Legitimate negative customer complaints or product criticism are **never** flagged as spam.
5. **Aspect-Based Sentiment Analysis (ABSA)**: Extracts discussed features (Battery, Camera, Display, Performance, Build, Price, Delivery, Packaging, Sound, Support) and calculates aspect-level satisfaction.
6. **Emoji Intelligence**: Extracts emojis, classifies contextual sentiment polarity, and generates frequency statistics.
7. **Keyword & Phrase Cloud**: Eliminates English and Hindi/Hinglish stopwords; extracts unigrams, bigrams, and weighted word cloud tags.

### 2.2 Rich Interactive Dashboard
- **Main KPI Cards**: Total analyzed, Positive %, Negative %, Neutral %, Spam count, Toxic count, Average Confidence, Average Rating.
- **Visual Analytics with Chart.js**:
  - Sentiment Donut Chart & Sentiment Spectrum progress pill.
  - Emotion breakdown bar chart.
  - Comment intent distribution chart.
  - Auto-moderation safety doughnut chart.
  - Product aspect breakdown table.
  - Emoji frequency grid.
  - Ranked keywords & interactive Word Cloud.
- **Comment Explorer Table**:
  - Real-time search box (by keyword or author).
  - Multi-dimension filter dropdowns (Sentiment, Emotion, Intent, Moderation).
  - Sorting (Default, Most Likes, Highest Rating, AI Confidence).
  - Backend/client-side pagination controls.
  - One-click "Inspect" modal displaying full text, classification explanation, signals, and moderation reasons.

### 2.3 Comprehensive Report Downloads
- **PDF Report**: Styled professional document generated via ReportLab with SocialPlus.ai headers, KPI cards, tables, and sample feedback.
- **HTML Report**: Completely self-contained offline HTML file with responsive styling and data badges.
- **Excel (.xlsx)**: Formatted workbook with multiple sheets (Executive Summary, Comments Data, Aspects).
- **CSV**: Standard comma-separated values of all analyzed comments.
- **JSON**: Machine-readable full intelligence payload.

---

## 3. Installation & Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(The application works immediately out of the box even without API keys for File Upload, Manual Comment Analysis, and public diagnostic checks!)*

### Step 3: Run the Application
Launch both backend and frontend on `http://127.0.0.1:8000`:
```bash
python run.py
```
Or with uvicorn directly:
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- **Web Application UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 4. API Credentials Configuration

### YouTube Data API v3
1. Visit the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **YouTube Data API v3**.
3. Create an API Key in **Credentials**.
4. Set the key in `.env`:
   ```ini
   YOUTUBE_API_KEY=AIzaSyYourActualKeyHere
   ```

### Meta Graph API (Instagram & Facebook)
1. Visit [Meta for Developers](https://developers.facebook.com/).
2. Create an App (type: **Business**).
3. Add the **Instagram Graph API** and **Facebook Login** products.
4. Configure permissions:
   - Instagram: `instagram_basic`, `instagram_manage_comments`, `pages_show_list`, `pages_read_engagement`
   - Facebook: `pages_show_list`, `pages_read_engagement`, `pages_read_user_content`
5. Set credentials in `.env`:
   ```ini
   META_APP_ID=123456789012345
   META_APP_SECRET=your_meta_app_secret
   META_REDIRECT_URI=http://localhost:8000/auth/meta/callback
   META_API_VERSION=v20.0
   ```

---

## 5. Platform Limitations & Ethical Standards

SocialPlus.ai adheres strictly to platform terms of service, robots directives, and security guidelines:
- **YouTube Public Route**: Modern unauthenticated bulk scraping is restricted by YouTube consent and bot defenses. If the API key is not configured, SocialPlus.ai transparently explains the limitation and enables **Upload File** or **Manual Input** mode.
- **Instagram & Facebook Public Routes**: Meta enforces login authentication walls. The app provides official Graph API OAuth connect flows and direct CSV/Excel upload support.
- **E-commerce Platforms**:
  - Amazon India: Employs strict CAPTCHA challenges; the app guides users to upload exported review files without attempting fragile CAPTCHA bypasses.
  - Flipkart: Supports public review extraction where available, and falls back to upload mode.
  - Myntra, Meesho, Ajio, Tata CLiQ, Nykaa, JioMart: Use app-signed tokens or prohibit automated scraping; the app clearly displays status `Upload Required`.
- **SSRF Protection**: All user-submitted URLs are validated before outbound requests to prevent Server-Side Request Forgery against localhost or private IP addresses.

---

## 6. Automated Testing

Run the automated test suite covering all connectors, AI engines, reports, and API routes:
```bash
pytest tests/ -v
```
All **21 automated tests** run and pass in ~2 seconds:
- `test_sentiment_five_categories`
- `test_multilingual_sentiment`
- `test_emotion_dimensions`
- `test_intent_classification`
- `test_moderation_rules`
- `test_emoji_analyzer`
- `test_keyword_analyzer`
- `test_aspect_analyzer`
- `test_unified_pipeline`
- `test_health_check_endpoint`
- `test_ecommerce_platforms_endpoint`
- `test_manual_analysis_endpoint`
- `test_unsupported_public_fetch_endpoint`
- `test_youtube_video_id_extraction`
- `test_instagram_and_facebook_identifiers`
- `test_security_ssrf_validation`
- `test_unconfigured_api_connectors`
- `test_ecommerce_registry`
- `test_file_parsing_csv`
- `test_file_parsing_json`
- `test_all_report_formats`



## Updated UI and Amazon marketplace support
- Refreshed the interface to a black-and-yellow theme.
- Analyzer cards now open focused analyzer pages with a Back control.
- Meta Analyzer includes large Instagram and Facebook platform cards.
- Amazon is labeled generically and URL detection recognizes common regional Amazon domains.
- Amazon review pagination now uses the resolved marketplace host rather than always forcing amazon.in.

## Important access limitations
This application does not bypass Instagram/Facebook authentication, CAPTCHA, login walls, or platform access controls. Use authorized Meta Graph API access or upload an exported dataset when comments are not publicly accessible. Amazon marketplace recognition does not guarantee that every regional marketplace exposes product/review pages to automated retrieval.


## E-commerce all-accessible review collection
- E-commerce extraction defaults to all reviews exposed through the public page UI; `max_reviews` is optional and omitted by the frontend.
- Shared browser-visible review collection supports public review cards, load-more/next controls and infinite-scroll pages for Amazon, Flipkart, Meesho, AJIO and Myntra.
- Raw reviews are stored in the local SQLite database in `ecommerce_review_items` and merged into later runs for the same resolved product URL.
- Retrieve the local archive with `GET /api/ecommerce/stored-reviews?product_url=<encoded-product-url>&page=1&page_size=100`.
- Install browser binaries after installing requirements: `python -m playwright install chromium`.
- Collection stops when the public page has no advancing review pagination, repeated pages, or the source blocks access. It does not bypass login, CAPTCHA, or access controls, and cannot guarantee reviews the site does not expose.
