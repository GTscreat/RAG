# 📰 Armenian News Intelligence & Publishing System (RAG Pipeline)

> An end-to-end automated news processing, ranking, content generation, and multi-channel publishing system for Armenian news media.

## 🎯 System Overview

This project implements a sophisticated **Retrieval-Augmented Generation (RAG)** pipeline specifically designed for Armenian news content. The system continuously:

1. **Collects** news articles from multiple Armenian media sources
2. **Processes** them with embeddings and Named Entity Recognition (NER)
3. **Ranks** articles based on topic importance, entity significance, frequency, and source credibility
4. **Generates** AI-enhanced content in Armenian and Russian languages
5. **Publishes** to Telegram channels with intelligent scheduling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  COLLECTOR   │───▶│    RANKER    │───▶│   COMPOSER   │───▶│  SPREADER  │ │
│  │              │    │              │    │              │    │            │ │
│  │ • Selector   │    │ • Thematic   │    │ • Selector   │    │ • Selector │ │
│  │ • Chunker    │    │ • Frequency  │    │ • Composing  │    │ • Publish  │ │
│  │ • Embedding  │    │ • NER Score  │    │ • LLM Prompts│    │ • Telegram │ │
│  │ • NER        │    │ • Ranking    │    │              │    │            │ │
│  └──────────────┘    │ • Top25      │    └──────────────┘    └────────────┘ │
│                      └──────────────┘                                        │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        RETRIEVER (RAG Q&A)                            │   │
│  │  Query Embedding → Semantic Search → LLM Answer Generation            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│                           ┌─────────────────┐                                │
│                           │   PostgreSQL    │                                │
│                           │    Database     │                                │
│                           └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
RAG/
├── main.py                    # Main orchestrator (multi-threaded execution)
├── main_out.py                # RAG Query Interface (Q&A mode)
├── db.py                      # SQLAlchemy ORM models & database connection
├── db_connector.py            # Raw psycopg2 connector (utility)
├── schema.sql                 # PostgreSQL schema definitions
├── migrate_data.py            # SQLite → PostgreSQL migration tool
├── requirements.txt           # Python dependencies
│
├── collector/                 # 📥 DATA COLLECTION MODULE
│   ├── article_selector.py    # Select unprocessed articles from DB
│   ├── chunker.py             # Text chunking with overlap
│   ├── embedding.py           # Armenian text embeddings (Sentence Transformers)
│   ├── local_embedding.py     # Standalone embedding utilities
│   ├── ner.py                 # Named Entity Recognition pipeline
│   └── utils.py               # Article filtering utilities
│
├── ranker/                    # 📊 RANKING & SCORING MODULE
│   ├── thematic_classifier.py # Topic classification via embeddings
│   ├── frequency_classifier.py# Duplicate/similarity detection
│   ├── ner_importance.py      # NER-based content importance scoring
│   ├── ranking.py             # Multi-factor ranking algorithm
│   └── top25.py               # Top candidates selection + AI scoring
│
├── composer/                  # ✍️ CONTENT GENERATION MODULE
│   ├── selector.py            # Select next unprocessed top article
│   ├── composing.py           # Armenian content generation (GPT-4.1)
│   ├── composing_ru.py        # Russian content generation (GPT-4.1)
│   └── llm_prompts.py         # Prompt templates library
│
├── spreader/                  # 📤 PUBLISHING MODULE
│   ├── selector.py            # Urgency-based publishing queue
│   ├── publishing.py          # Telegram publishing logic
│   ├── telegram_message.py    # Message formatting (MarkdownV2)
│   └── selector_urgent_value.txt
│
├── retriever/                 # 🔍 RAG QUERY MODULE
│   ├── retriever.py           # Semantic search & article retrieval
│   ├── llm_client.py          # LLM API client (OpenAI/Anthropic)
│   ├── prompt_templates.py    # RAG prompt configurations
│   └── rag_query.py           # Interactive query interface
│
└── data/                      # 📂 DATA & TEMPLATES
    ├── tamplates/
    │   ├── thematic_corpus.json           # Topic classification corpus
    │   ├── thematic_corpus_embeddings.json# Pre-computed topic embeddings
    │   ├── media_rating.json              # Source credibility ratings
    │   ├── ner.md                         # NER documentation
    │   └── *.py                           # Embedding generation scripts
    ├── ner_class.db                       # NER classification database
    └── nerdatabase.db                     # Entity database
```

---

## 🔧 Core Modules

### 1. 📥 Collector Module (`collector/`)

Responsible for ingesting and preprocessing news articles.

| Component | Description |
|-----------|-------------|
| `article_selector.py` | Selects articles from the last N hours that haven't been embedded yet |
| `chunker.py` | Splits articles into overlapping chunks (512 chars, 256 overlap) |
| `embedding.py` | Generates embeddings using `Metric-AI/armenian-text-embeddings-1` |
| `ner.py` | Extracts named entities using `daviddallakyan2005/armenian-ner` |

**Embedding Flow:**
```python
# Chunk Configuration
max_chunk_size = 512
overlap_size = 256

# Embedding Model
model = "Metric-AI/armenian-text-embeddings-1"
prefix = "passage: "  # For documents
query_prefix = "query: "  # For queries
```

**NER Pipeline:**
```python
# Model: daviddallakyan2005/armenian-ner
# Strategy: "simple" aggregation
# Entities are merged if consecutive and same type
```

---

### 2. 📊 Ranker Module (`ranker/`)

Scores and ranks articles using multiple factors.

#### Ranking Weights
| Factor | Weight | Description |
|--------|--------|-------------|
| Thematic Importance | 25% | Topic category score from corpus |
| NER Content Importance | 32% | Named entity significance score |
| Frequency Importance | 28% | Similarity with other recent articles |
| Source Importance | 15% | Media outlet credibility rating |

**Thematic Classification:**
```python
# Categories: Միdelays (International), Անdelays (Security), Քdelays (Political), etc.
# Similarity threshold: 0.75 for primary category
# Secondary threshold: 0.50 for hybrid categories (e.g., "Politics-Security")
```

**Frequency Detection:**
```python
# Cosine similarity threshold: ≥ 0.75
# Compares against last 100 articles
# Identifies duplicate/similar stories
```

**AI Scoring (Top25):**
```python
# OpenAI GPT-4o evaluates:
# - Importance (1-5)
# - Urgency (1-3)  
# - Domestic sentiment (neutral/pro/anti)
# - Geopolitical orientation (proarmenian/antiarmenian/neutral)

# Final Score = 0.55 × total_score + 0.45 × ai_score
```

---

### 3. ✍️ Composer Module (`composer/`)

Generates AI-enhanced content in Armenian and Russian.

**Prompt Architecture:**
```python
# Base Components:
ROLE1 = "Professional Armenian news editor for Telegram"
ROLE2 = "Professional Russian news editor for Armenian news"

# Operational Modes:
OPERATIONAL_HIGH    # Concise, fast, neutral
OPERATIONAL_BALANCED # Include context, essential facts

# Objectivity Spectrum:
OBJECTIVITY_NEUTRAL        # No bias
OBJECTIVITY_TOPIC_ADJUSTED # Armenia's national interests perspective

# Output Format:
TELEGRAM_OUTPUT_FORMAT = 'title: "...", content: "..."'
```

**Geopolitical Adaptation:**
```python
if geopolitical == "antiarmenian":
    prompt += OBJECTIVITY_TOPIC_ADJUSTED + STYLE_REPHRASED
else:
    prompt += OBJECTIVITY_NEUTRAL + STYLE_DIRECT
```

---

### 4. 📤 Spreader Module (`spreader/`)

Manages intelligent content publishing to Telegram.

**Publishing Channels:**
| Language | Channel | Bot Token Env |
|----------|---------|---------------|
| Armenian | @newsarmaipowerd | `TELEGRAM_BOT_TOKEN` |
| Russian | @newsrusaipowerd | `TELEGRAM_BOT_TOKEN_RU` |

**Publishing Logic:**
```python
# Priority: Urgency 3 (ultra-urgent) → High score → Oldest first

# Adaptive Sleep Intervals:
# urgency > 1        → 2 minutes
# not_published > 12 → 3 minutes  
# not_published > 8  → 4 minutes
# not_published > 5  → 5 minutes
# default            → 6 minutes
```

**Message Format (MarkdownV2):**
```
*Title*

Content text here...

*[Ավdelays](source_url)*

@newsarmaipowerd
```

---

### 5. 🔍 Retriever Module (`retriever/`)

Provides RAG-based question answering over the news corpus.

**Query Flow:**
```
User Question → Query Embedding → Semantic Search → Top K Articles → LLM Generation → Answer
```

**Configuration:**
```python
TOP_ID = 20  # Number of articles to retrieve
OPENAI_MODEL = "gpt-4.1"
```

**System Role:**
```python
# Political scientist persona
# Aware of social/political developments
# Must cite sources with URL and date
# Direct quotes in Armenian quotation marks («»)
# All responses in Armenian
```

---

## 🗄️ Database Schema

### PostgreSQL Tables

```sql
-- Core News Table
CREATE TABLE news (
    id SERIAL PRIMARY KEY,
    website_id INTEGER REFERENCES websites(id),
    url VARCHAR,
    title VARCHAR,
    content TEXT,
    published_at TIMESTAMP,
    meta JSONB
);

-- Chunk Embeddings (One-to-Many)
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES news(id) ON DELETE CASCADE,
    chunk_content TEXT,
    chunk_start INTEGER,
    chunk_end INTEGER,
    embedding BYTEA
);

-- Article Parameters (One-to-One)
CREATE TABLE parameters (
    id INTEGER PRIMARY KEY REFERENCES news(id) ON DELETE CASCADE,
    category VARCHAR,
    aver_embedding BYTEA,
    similarity JSONB,
    entities JSONB
);

-- Ranking Scores (One-to-One)
CREATE TABLE ranks (
    id INTEGER PRIMARY KEY REFERENCES news(id) ON DELETE CASCADE,
    topic_importance REAL,
    ner_content_importance REAL,
    frequency_importance REAL,
    source_importance REAL,
    total_score REAL
);

-- Top Candidates (One-to-One)
CREATE TABLE top (
    id INTEGER PRIMARY KEY REFERENCES news(id) ON DELETE CASCADE,
    total_score REAL,
    ai_score REAL,
    urgency INTEGER,
    sentiment VARCHAR,
    geopolitical VARCHAR,
    final_score REAL
);

-- Processed Content (One-to-One)
CREATE TABLE processed (
    base_id INTEGER PRIMARY KEY REFERENCES news(id) ON DELETE CASCADE,
    title VARCHAR,
    generated_content TEXT,
    published VARCHAR,
    title_r VARCHAR,
    generated_content_r TEXT,
    published_r VARCHAR
);

-- Named Entities
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    entity_group VARCHAR,
    score REAL,
    word VARCHAR,
    ner_score REAL,
    category_id INTEGER REFERENCES entity_categories(id)
);

CREATE TABLE entity_categories (
    id SERIAL PRIMARY KEY,
    code INTEGER,
    path VARCHAR,
    ner_category_index INTEGER,
    ner_category_opp_index INTEGER
);
```

---

## 🚀 Getting Started

### Prerequisites

```bash
# Python 3.8+
# PostgreSQL 12+
```

### Installation

```bash
# Clone the repository
git clone <repository_url>
cd RAG

# Install dependencies
pip install -r requirements.txt

# Additional dependencies (may be needed)
pip install psycopg2-binary python-dotenv transformers torch
```

### Environment Variables

Create a `.env` file:

```env
# Database Configuration
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name

# OpenAI API
OPENAI_API_KEY=sk-...

# Telegram Bots
TELEGRAM_BOT_TOKEN=your_armenian_bot_token
TELEGRAM_BOT_TOKEN_RU=your_russian_bot_token

# Optional: Anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Database Setup

```bash
# Create database
psql -U postgres -c "CREATE DATABASE your_database_name;"

# Apply schema
psql -U postgres -d your_database_name -f schema.sql

# (Optional) Migrate from SQLite
python migrate_data.py
```

---

## 🏃 Running the System

### Main Pipeline (Full Automation)

```bash
python main.py
```

This starts three concurrent threads:
1. **Main Processing Loop** - Collect, process, rank, generate content
2. **Spreader Loop** - Publish to Telegram on schedule
3. **Monitor Loop** - Watch for urgent content

### RAG Query Interface

```bash
python main_out.py
```

Interactive Q&A over the news corpus:
```
 Delays որdelays delays delays delays:
> Delays վdelays delays delays delays Delaysdelays?
```

---

## 📊 Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MAIN PROCESSING LOOP                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. SELECT NEW ARTICLES (last 1 hour, unprocessed)                   │
│         ↓                                                            │
│  2. CHUNK ARTICLES (512 chars, 256 overlap)                          │
│         ↓                                                            │
│  3. COMPUTE EMBEDDINGS (armenian-text-embeddings-1)                  │
│         ↓                                                            │
│  4. RUN NER (armenian-ner model)                                     │
│         ↓                                                            │
│  5. UPDATE AVERAGE EMBEDDINGS (per article)                          │
│         ↓                                                            │
│  6. THEMATIC CLASSIFICATION (topic corpus similarity)                │
│         ↓                                                            │
│  7. FREQUENCY CLASSIFICATION (duplicate detection)                   │
│         ↓                                                            │
│  8. RANK NEWS (multi-factor scoring)                                 │
│         ↓                                                            │
│  9. REFRESH TOP 25 + AI SCORING (GPT-4o evaluation)                  │
│         ↓                                                            │
│  10. GENERATE CONTENT (Armenian + Russian, GPT-4.1)                  │
│         ↓                                                            │
│  [Sleep 90 seconds → Repeat]                                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        SPREADER LOOP                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. SELECT TO PUBLISH (urgency → score → age priority)               │
│         ↓                                                            │
│  2. PUBLISH ARMENIAN (Telegram @newsarmaipowerd)                     │
│         ↓                                                            │
│  3. PUBLISH RUSSIAN (Telegram @newsrusaipowerd)                      │
│         ↓                                                            │
│  [Adaptive sleep 2-6 minutes based on queue/urgency]                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration Files

### `data/tamplates/thematic_corpus.json`

Defines topic categories with example articles for classification:

```json
[
  {
    "category": "Միdelays",  // International
    "score": 3,
    "examples": ["Example news articles..."]
  },
  {
    "category": "Delays",  // Security
    "score": 6,
    "examples": [...]
  }
]
```

### `data/tamplates/media_rating.json`

Source credibility ratings (1-5):

```json
[
  {"url": "armenpress.am", "score": 5},
  {"url": "news.am", "score": 5},
  {"url": "hraparak.am", "score": 2},
  {"url": "iravunk.com", "score": 0}
]
```

---

## 🛠️ Key Technical Details

### Embedding Model
- **Model**: `Metric-AI/armenian-text-embeddings-1`
- **Type**: Sentence Transformers
- **Normalization**: Enabled
- **Prefix**: `passage:` for documents, `query:` for queries

### NER Model
- **Model**: `daviddallakyan2005/armenian-ner`
- **Framework**: Hugging Face Transformers
- **Aggregation**: Simple (merges adjacent same-type entities)

### LLM Configuration
- **Provider**: OpenAI
- **Model**: GPT-4.1 (content generation), GPT-4o (scoring)
- **Temperature**: 0.1-0.2 (low for consistency)

### Database
- **Type**: PostgreSQL with JSONB support
- **ORM**: SQLAlchemy
- **Embedding Storage**: BYTEA (binary)

---

## 📝 API Reference

### Collector Functions

```python
# Select unprocessed articles from last N hours
select_new_articles(time_window_hours: int = 1) -> List[News]

# Chunk articles and store in embeddings table
chunk_articles_and_store(articles, max_chunk_size=512, overlap_size=256)

# Compute and store embeddings
embed_chunks(chunks, batch_size=32, prefix="passage: ", save_mode="update")

# Run NER pipeline
run_ner_on_articles(articles, ner_pipeline) -> List[Dict]
```

### Ranker Functions

```python
# Update average embeddings per article
update_aver_embeddings()

# Classify articles by topic
run_thematic_classifier()

# Detect similar articles
run_frequency_classifier()

# Compute final ranking
rank_news()

# Select top 25 and get AI scores
refresh_top_and_score() -> Dict
```

### Composer Functions

```python
# Get next unprocessed article ID
get_next_unprocessed_top_id() -> int | None

# Generate prompt for article
prompt_gen_request(base_id) -> Tuple[str, Dict]

# Generate content with OpenAI
generate_content_with_openai(prompt, content) -> str

# Save processed content
save_processed(base_id, openai_response)
```

### Spreader Functions

```python
# Select content for publishing
select_to_publish()

# Execute publishing cycle
publishing_cycle() -> int  # Returns sleep time
publishing_cycle_ru()

# Get current urgent count
get_urgent_value() -> int
```

### Retriever Functions

```python
# Embed a query
embed_query(text: str) -> np.ndarray

# Get top K unique articles by similarity
get_top_k_unique_articles(query_emb, top_id=20) -> List[Dict]

# Generate answer using LLM
generate_answer(query, articles, provider="openai") -> Dict
```

---

## 🔒 Security Notes

- Store API keys in `.env` file (never commit!)
- Use environment variables for sensitive data
- Database credentials should be secured
- Telegram bot tokens are sensitive

---

## 📄 License

[Specify your license here]

---

## 🤝 Contributing

[Contribution guidelines]

---

## 📞 Support

[Contact information]
