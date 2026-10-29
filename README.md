# Automated Micro-Influencer Outreach System

> **EDXSO AI Engineer Intern – Assignment 1**  
> An automated end-to-end pipeline that discovers relevant micro-influencers, filters and classifies them based on multi-dimensional criteria, enriches their profiles with verified data, generates personalized outreach messages (Email pitch & Instagram DM), and manages a delivery and tracking layer with strict duplicate prevention.

---

## 📋 Table of Contents
1. [System Architecture & Flow](#system-architecture--flow)
2. [Technology Stack & Tools](#technology-stack--tools)
3. [Data Sources & Discovery Methodology](#data-sources--discovery-methodology)
4. [Filtering & Classification Logic](#filtering--classification-logic)
5. [Profile Enrichment Process](#profile-enrichment-process)
6. [AI Message Personalization & Prompts](#ai-message-personalization--prompts)
7. [Sending Layer & Duplicate Prevention](#sending-layer--duplicate-prevention)
8. [Deliverables & Dataset Formats](#deliverables--dataset-formats)
9. [Setup & Quickstart Guide](#setup--quickstart-guide)
10. [Automated Testing](#automated-testing)
11. [Scalability & Limitations](#scalability--limitations)

---

## 1. System Architecture & Flow

The system implements the sequential, modular 7-stage workflow requested by the assignment specification:

```
┌─────────────────────────┐
│  1. Influencer Discovery │  Fetches 50+ real creators from directories & indexes
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 2. Filtering & Classify │  Evaluates 5k-100k follower range, engagement, brand fit
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  3. Profile Enrichment  │  Populates mandatory fields, verified emails, demographics
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 4. AI Personalization   │  Generates Email Pitch (60-90w) & Instagram DM (15-30w)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 5. Review & Sending     │  Sandbox Simulation or Live SMTP dispatch
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│   6. Outreach Tracker   │  Idempotent delivery log preventing duplicate contact
└─────────────────────────┘
```

---

## 2. Technology Stack & Tools

| Component | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Backend & CLI** | Python 3.12, Flask, Pandas, Rich | Core data pipeline, CLI runner, REST API |
| **Web Scraping & Extraction** | BeautifulSoup4, Requests, HTTPX | Discovery extraction from public indices |
| **AI / LLM Personalization** | Google Gemini API, OpenAI / Groq, Contextual Heuristic AI | Dual dynamic message synthesis with strict word count guardrails |
| **Sending Layer** | Python `smtplib`, `email.mime`, Simulation Sandbox | Multi-mode email dispatch and DM staging |
| **Web Dashboard** | Vanilla CSS (Glassmorphism), Vanilla JS, HTML5 | Interactive dashboard with real-time stats and CSV/JSON export |
| **Testing** | Python `unittest` | Automated validation of criteria, counts, and word limits |

---

## 3. Data Sources & Discovery Methodology

- **Target Niche**: **Technology & AI Creators** (with extensible configuration for Fitness, Beauty, Fashion, Fintech, and Gaming).
- **Definition of Micro-Influencer**: Accounts generally possessing **5,000 to 100,000 followers** (or equivalent high audience engagement).
- **Strict Data Authenticity Policy**:
  - **Zero Fabrication**: All 55 test records correspond to real, public software engineers, AI researchers, and tech creators across YouTube, Instagram, GitHub, and Substack.
  - **No Guessed Emails**: If a creator does not publicly disclose a business inquiry email, the field is explicitly marked as `"Not Found"`.
  - **Included Edge Cases**: Intentional inclusion of macro-influencers (>1M followers like FreeCodeCamp, Tech With Tim), nano-creators (<5k followers), dormant accounts, and off-niche profiles to prove the filtering engine actively disqualifies non-qualifying candidates.

---

## 4. Filtering & Classification Logic

Each discovered profile is passed through a deterministic multi-criteria filter in `backend/pipeline/filter_classify.py`:

1. **Follower Count Criteria**:
   - $\text{followers} < 5,000 \implies$ Disqualified (*Nano-influencer below micro threshold*).
   - $\text{followers} > 100,000 \implies$ Disqualified (*Macro-influencer exceeding 100k cap*).
2. **Engagement Rate Criteria**:
   - $\text{engagement\_rate} < 1.5\% \implies$ Disqualified (*Below minimum viable audience responsiveness*).
3. **Category / Niche Relevance**:
   - Matches target category (e.g., Technology, AI, Coding, DevOps). Off-niche creators (e.g. meme tokens, cosmetics) are rejected.
4. **Brand-Fit & Safety**:
   - Detects spam signals, automated text re-uploads, or dormant content.
5. **Output**:
   - Every candidate is tagged with `passed` (`True`/`False`), `filter_status` (`PASSED`/`FAILED`), a `classification_tier` (e.g., *Tier 1: High Engagement Micro-Creator*), and an explicit **qualification or disqualification reason summary**.

---

## 5. Profile Enrichment Process

All shortlisted influencers are processed by `backend/pipeline/enrichment.py` to populate:

- **Mandatory Fields**:
  - `name`: Influencer Name
  - `platform`: Primary platform (YouTube, Instagram, Substack)
  - `profile_url`: Verified channel/profile link
  - `follower_count`: Exact subscriber/follower count
  - `engagement_rate`: Active engagement percentage
  - `category` & `niche`: Category and specialized topic
  - `content_themes`: Categorized list of covered subjects
  - `contact_email`: Verified business contact or strictly `"Not Found"`
- **Optional & Derived Intelligence**:
  - Social handles (Instagram, Website)
  - `audience_age`, `audience_gender`, `audience_geography`
  - `estimated_active_reach`: $\text{followers} \times (\text{engagement\_rate} / 100)$
  - `collab_type`: Tailored collaboration angle (Sponsorship, UGC, Affiliate, Product Placement, Barter)
  - `collaboration_readiness`: `HIGH (Direct Email)` or `MEDIUM (Instagram DM)`

---

## 6. AI Message Personalization & Prompts

The system automatically generates two distinct, tailored outreach messages per shortlisted creator:

### A. Email Collaboration Pitch
- **Target Length**: **Strictly 60–90 words**.
- **Personalization Signals**: Influencer's niche, tone/style, recent video/article title, relevant audience geography, proposed collaboration angle, and EDXSO AI value proposition.
- **Word Count Enforcement**: Automated algorithmic sentence trimmer and validator ensures output strictly conforms to the 60–90 word range.

### B. Instagram DM
- **Target Length**: **Strictly 15–30 words**.
- **Tone**: Conversational, natural, peer-to-peer, referencing specific content.

### System Prompt Engineering Template
```text
You are reaching out to a micro-influencer for a high-value brand partnership.
Brand: EDXSO AI Developer Studio
Brand Value Proposition: cutting-edge AI developer tools and agentic workflows

Influencer Profile:
- Name: {name} | Platform: {platform} | Niche: {niche}
- Recent Content: {recent_post_title} | Tone: {content_tone}
- Audience: {audience_geography} | Collab: {collab_type}

Requirements:
1. Email Collaboration Pitch: Strictly 60 to 90 words. Reference their recent work,
   tone, audience, and propose the specific collaboration angle.
2. Instagram DM: Strictly 15 to 30 words. Natural, casual, referencing their content.
Return JSON with keys: 'subject', 'email_pitch', 'instagram_dm'.
```

*Note: The engine supports live API calls via Google Gemini (`gemini-1.5-flash`), OpenAI (`gpt-4o-mini`), Groq (`llama-3.3-70b`), and includes an offline contextual heuristic AI generator that produces unique, non-templated messages with 100% compliance out of the box.*

---

## 7. Sending Layer & Duplicate Prevention

Implemented in `backend/pipeline/sending_layer.py`:

1. **Email Filtering**: Selects only candidates where `contact_email != "Not Found"` and valid `@` structure.
2. **Instagram DM Workflow**: In compliance with Meta API terms, automated unapproved DM botting is avoided. Instead, Instagram candidates are routed to a **Manual Dispatch Console** with a one-click "Copy DM" button and simulated dispatch tracking.
3. **Idempotency & Duplicate Prevention**:
   - Maintains a persistent hash index in `data/outreach_tracker.json`.
   - Before any dispatch, checks recipient key (`email` or creator identifier).
   - If an outreach was previously recorded, it logs `DUPLICATE_PREVENTED` and skips re-sending.
4. **Execution Modes**:
   - `simulation` (Default): Safe sandbox rendering full MIME email payloads without sending live spam.
   - `smtp`: Live TLS dispatch via Gmail API / SMTP credentials configured in `.env`.

---

## 8. Deliverables & Dataset Formats

All datasets are automatically saved to `./data/` in both JSON and CSV formats:

| Deliverable | JSON File | CSV File | Content Description |
| :--- | :--- | :--- | :--- |
| **Discovered Influencers** | `influencers_discovered.json` | `influencers_discovered.csv` | 55 real influencer profiles with metrics |
| **Filtering Results** | `influencers_filtered.json` | `influencers_filtered.csv` | Pass/Fail decisions, tiers, and detailed reasons |
| **Enriched Dataset** | `influencers_enriched.json` | `influencers_enriched.csv` | Demographics, active reach, collab readiness |
| **Personalized Pitches** | `personalized_outreach.json` | `personalized_outreach.csv` | Email pitches (60-90w) and Instagram DMs (15-30w) |
| **Outreach Tracker** | `outreach_tracker.json` | `outreach_tracker.csv` | Outreach log with timestamps, status, delivery details |

---

## 9. Setup & Quickstart Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- pip

### 1. Installation
```bash
git clone <repo-url>
cd InfluencerOutreach

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Run the Full CLI Pipeline
To run the complete discovery, filtering, enrichment, AI personalization, and sending workflow:
```bash
python run_pipeline.py
```
This executes all 5 stages in seconds, logs colored progress to the terminal, and populates the `./data/` directory.

### 3. Launch the Interactive Web Dashboard
```bash
python backend/app.py
```
Open **`http://127.0.0.1:5000`** in your browser to access the Web UI:
- **Interactive Tables** with search and filter controls
- **Pass/Fail Audit Inspector** showing exact disqualification reasons
- **AI Personalization Studio** with word count badges & one-click DM copy
- **Outreach Tracker** with delivery log inspection and CSV/JSON downloads
- **One-Click Re-run** button to trigger the pipeline live from the UI

---

## 10. Automated Testing

Run the automated test suite covering all assignment criteria:
```bash
python -m unittest discover tests
```

### Tested Test Cases:
- `test_01_discovery_count_and_fields`: Asserts $\ge 50$ real records and mandatory keys.
- `test_02_filtering_logic_micro_range`: Asserts macro (>100k) and nano (<5k) rejection.
- `test_03_filtering_engagement_and_niche`: Asserts low-engagement (<1.5%) and off-niche filtering.
- `test_04_profile_enrichment_mandatory_fields`: Asserts missing email is strictly `"Not Found"`.
- `test_05_personalization_word_count_guardrails`: Asserts email pitch strictly 60–90 words and DM 15–30 words.
- `test_06_sending_layer_duplicate_prevention`: Asserts duplicate outreach is blocked.

---

## 11. Scalability & Limitations

### Extending from 50 to 500+ Influencers:
1. **Asynchronous Scraping**: Integrate `asyncio` / `aiohttp` or Playwright cluster to crawl creator directories concurrently.
2. **Persistent Database**: Transition from file-based JSON storage to PostgreSQL with SQLAlchemy or Supabase for relational querying and ACID transaction safety.
3. **Queue & Rate Limiting**: Introduce Celery or Redis Queue (RQ) with token-bucket rate limiters for LLM API throttling and email warmup (e.g. max 50 emails/day per mailbox).
4. **Email Verification**: Integrate ZeroBounce or Hunter.io API into the enrichment stage to verify MX records and bounce risks.

### Platform Limitations:
- **Meta/Instagram DM Automation**: Meta strictly prohibits unauthorized third-party automated direct messaging outside official Instagram Messaging API for approved business pages. To preserve platform compliance and protect account health, our system demonstrates generated DMs and provides a streamlined manual copy-and-dispatch workflow.
