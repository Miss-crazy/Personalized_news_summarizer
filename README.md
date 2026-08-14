# 📰 Personalized News Summarizer with RAG & Adaptive Personalization

An end-to-end, privacy-focused AI news aggregation, clustering, summarization, and interactive Retrieval-Augmented Generation (RAG) system with real-time user preference learning.

---

## 📌 Overview

The **Personalized News Summarizer** automatically ingests news stories from multiple global and Indian sources, cleans and deduplicates them, converts them into dense vector embeddings, clusters related articles across outlets, generates concise executive summaries using local LLMs, and powers an interactive RAG interface where users can ask questions and receive personalized news digests tailored to their reading history and explicit/implicit feedback.

```
+--------------------------------------------------------------------------------------------------+
|                                    PROJECT WORKFLOW ARCHITECTURE                                 |
+--------------------------------------------------------------------------------------------------+

  [ Ingestion Sources ]
  +-- RSS Feeds (BBC, The Hindu, TOI, Reuters, NASA, Verge, etc.)
  +-- Web Scrapers (Hacker News, MIT Tech Review)
  +-- GNews API (Technology, Science, Business, Health, Sports)
            │
            ▼
  [ SQLite Relational Storage ] (Raw Articles, Deduplication via URL hashing & URLs)
            │
            ▼
  [ Embedding & Dimensionality Reduction ]
  +-- Model: sentence-transformers/all-MiniLM-L6-v2 (384-dimensional dense vectors)
  +-- UMAP (Uniform Manifold Approximation and Projection) -> 15 dimensions (for N >= 50)
            │
            ▼
  [ Topic Clustering ]
  +-- Algorithm: HDBSCAN (Hierarchical Density-Based Spatial Clustering of Applications with Noise)
  +-- Auto-detects topics without predefining K; isolates outliers & singletons
            │
            ▼
  [ LLM Synthesis & Topic Labeling ]
  +-- Model: Ollama / Phi-3 Mini (phi3:mini)
  +-- Generates concise 3-4 sentence summaries and 3-5 word topic labels
            │
            ▼
  [ ChromaDB Vector Store ] (Stores cluster summary embeddings & metadata)
            │
            ▼
  [ Personalized RAG & Adaptive Feedback Loop ]
  +-- Hybrid Score: S_final = (1 - α) * S_semantic + α * S_preference
  +-- Feedback: Explicit (Thumbs Up/Down) & Implicit (Dwell reading time)
  +-- Interactive Web Dashboard (FastAPI + Modern UI) & CLI REPL
```

---

## ✨ Key Features

- **🌐 Multi-Source Ingestion Pipeline**:
  - GNews API integration for major global topic feeds.
  - Standardized RSS & Atom feed parser with auto-deduplication.
  - Polite HTML Web Scrapers with fallback selectors and request throttling.
- **🧠 Unsupervised Semantic Clustering**:
  - Automatically identifies emerging news stories across distinct publishers without hardcoded topic counts ($K$).
  - UMAP dimensionality reduction + HDBSCAN clustering to cleanly isolate topic groups and noise/singletons.
- **📝 Local & Private LLM Summarization**:
  - Summarizes multi-article clusters using Ollama and local models like **Phi-3 Mini** (`phi3:mini`).
  - Zero API cost and complete data privacy for document processing.
- **🔍 Hybrid Personalized RAG (Retrieval-Augmented Generation)**:
  - Vector similarity search over cluster summaries stored in **ChromaDB**.
  - Adaptive user profiling: weights adjust dynamically based on user engagement.
  - Source diversity engine ensuring well-rounded news coverage across fields (World, Tech, Science).
- **📊 Modern Web UI & REST API**:
  - Built with FastAPI with interactive news cluster cards, source linkouts, background sync triggers, and instant feedback buttons (like/dislike/dwell tracking).
- **⏱️ Automated Dual-Loop Scheduler**:
  - APScheduler-driven background routines for automated periodic news ingestion and processing.

---

## 📡 News Sources Ingested

The project consumes articles from a curated list of trusted domestic and international publications:

| Category | Sources & Feeds |
|---|---|
| **National & Regional (India)** | *The Hindu* (National & Telangana), *Times of India* (National & Hyderabad), *NDTV News*, *The Indian Express*, *Hindustan Times*, *Economic Times*, *News18* |
| **Global & Technology** | *BBC News (World & Tech)*, *Reuters Top News*, *TechCrunch*, *The Verge*, *NASA Breaking News* |
| **Web Scrape Targets** | *Hacker News* (`news.ycombinator.com`), *MIT Technology Review* (`technologyreview.com`) |
| **GNews API Topics** | `technology`, `business`, `science`, `health`, `sports` |

---

## 🤖 ML Models & Algorithms Used

1. **Sentence Embeddings**:
   - **Model**: `all-MiniLM-L6-v2` (*Sentence-Transformers*)
   - **Output**: 384-dimensional dense semantic vectors representing article titles and snippets.
2. **Dimensionality Reduction**:
   - **Algorithm**: **UMAP** (*Uniform Manifold Approximation and Projection*)
   - **Target**: Compresses 384-dim embeddings down to 15 dimensions for faster, higher-density clustering when sample size $N \ge 50$.
3. **Clustering & Noise Isolation**:
   - **Algorithm**: **HDBSCAN** (*Hierarchical Density-Based Spatial Clustering of Applications with Noise*)
   - **Parameters**: `min_cluster_size=3`, `min_samples=2`, `metric='euclidean'`, `cluster_selection_method='eom'`. Handles noise points (label `-1`) as individual singletons.
4. **LLM Generation & Summarization**:
   - **Model**: **Phi-3 Mini** (`phi3:mini`) hosted locally via **Ollama** (supports custom models configurable via settings).
   - Generates 3–5 word topic labels and 3–4 sentence balanced executive summaries.
5. **Adaptive Personalization Function**:
   - Scores candidates via linear interpolation:
     $$\text{Score}_{\text{final}} = (1 - \alpha) \cdot \text{Score}_{\text{semantic}} + \alpha \cdot \text{Score}_{\text{user\_preference}}$$
   - Normalizes and updates user preference vectors upon thumbs up ($+1.0$), thumbs down ($-1.0$), and reading dwell time ($+\text{dwell\_seconds} / 60$).

---

## 🏗️ End-to-End Pipeline Architecture

```
[ Phase 1: Ingestion ]
  RSS Feeds / Scrapers / GNews ──► Deduplication (URL Hash) ──► SQLite (articles table)
                                                                       │
[ Phase 2: Processing & Clustering ]                                  ▼
  Fetch Unprocessed Articles ──► Embeddings (all-MiniLM-L6-v2) ──► UMAP (15D)
                                                                       │
  Ollama (Phi-3 Mini) ◄── HDBSCAN Clustering (eom) ◄────────────────────┘
         │
         ▼
  Generate Topic Labels & Summaries ──► SQLite (clusters table)
                                               │
[ Phase 3: Vector Indexing & RAG ]            ▼
  ChromaDB Vector Store ◄── Embed Summaries ───┘
         │
         ├──► Query ChromaDB (Cosine similarity top-k)
         ├──► Source Field Diversification (World / Tech / Science)
         └──► Ollama Prompting (System Prompt + Retrieved News Context + Query) ──► Answer
                                                                                        │
[ Phase 4: Personalization & Feedback ]                                                 ▼
  User Interactions (Like / Dislike / Dwell) ──► Dynamic Weight Updates ──► User Profile
```

---

## 📂 Project Structure

```plaintext
Personalized_news_summarizer/
├── config/
│   └── settings.py          # Central configuration (API keys, models, thresholds)
├── data/                    # SQLite database & ChromaDB vector files (generated)
├── ingestion/
│   ├── gnews_collector.py   # GNews REST API client
│   ├── rss_collector.py     # Feedparser-based RSS collector
│   ├── scraper.py           # BeautifulSoup web scraper for custom websites
│   └── pipeline.py          # Master ingestion pipeline runner
├── processing/
│   ├── embedder.py          # SentenceTransformer embedding generator
│   ├── clusterer.py         # UMAP dimension reduction + HDBSCAN clustering
│   ├── summarizer.py        # Ollama / Phi-3 Mini label & summary generator
│   └── pipeline.py          # Processing orchestrator
├── rag/
│   ├── prompt_templates.py  # System and RAG prompt templates
│   └── chain.py             # ChromaDB retrieval + Ollama QA chain
├── personalization/
│   ├── weight_updater.py    # Adaptive learning rate preference weight calculator
│   ├── feedback_handler.py  # Feedback signal dispatcher
│   └── retriever.py         # Preference-weighted personalized retriever
├── scheduler/
│   └── jobs.py              # APScheduler background automation
├── storage/
│   ├── database.py          # SQLite schema, tables, and CRUD operations
│   ├── user_profiles.py     # User preference storage and interaction history
│   └── vector_store.py      # ChromaDB collection wrapper
├── static/
│   ├── index.html           # Web UI layout
│   ├── style.css            # Modern responsive UI styling
│   └── app.js               # Frontend interaction logic & API connectors
├── requirements.txt         # Project Python dependencies
├── run.py                   # Master CLI interface
└── web_app.py               # FastAPI application backend
```

---

## 🚀 Getting Started

### 1. Prerequisites

- **Python**: 3.10+
- **Ollama**: Installed and running locally ([ollama.ai](https://ollama.ai/))

Pull the default language model:
```bash
ollama serve
ollama pull phi3:mini
```

### 2. Installation

Clone the repository and install dependencies:
```bash
git clone https://github.com/Miss-crazy/Personalized_news_summarizer.git
cd Personalized_news_summarizer
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory (or copy from `.env.example`):
```env
GNEWS_API_KEY=your_gnews_api_key_here
DB_PATH=data/news.db
CHROMA_PERSIST_DIR=data/chroma
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## 💻 Usage & CLI Commands

### Ingest & Process News
```bash
# 1. Fetch latest news from RSS, GNews, and Scrapers
python run.py --ingest

# 2. Embed, cluster with HDBSCAN, generate summaries, and sync to ChromaDB
python run.py --process
```

### Ask Questions with RAG
```bash
# Standard RAG Query
python run.py --ask "What are the latest developments in AI and tech?"

# Personalized RAG Query (biases output to user's learned preferences)
python run.py --pask alice "Tell me about space exploration"

# Interactive REPL session
python run.py --rag-repl
```

### User Feedback & Profiles
```bash
# Register feedback (thumbs_up / thumbs_down)
python run.py --feedback alice 1 thumbs_up

# View user profile preference weights
python run.py --profile alice
```

### Start Automated Continuous Scheduler
```bash
python run.py --scheduler
```

---

## 🌐 Running the Web Application

Launch the FastAPI web server:
```bash
uvicorn web_app:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to:
```
http://localhost:8000
```
From the web UI, you can:
- Browse real-time news clusters and summaries with direct source links.
- Ask questions to the RAG AI assistant with personalized ranking.
- Trigger manual Ingest / Process jobs directly from the interface.
- Provide thumbs up/down feedback and track dwell time to train your personalized feed.

---

## 🛡️ License

This project is licensed under the MIT License.
