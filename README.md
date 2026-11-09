# Conference-helpdesk
An AI-powered conference assistant that answers attendee questions about sessions, schedules, speakers, and venues. Users can have continuous conversations and generate a personalized summary of their interactions at the end.

# Tech

System 1: Conference Data Ingestion System
Collect and index conference information.
<img width="508" height="922" alt="mermaid-diagram (1)" src="https://github.com/user-attachments/assets/f0b54a6a-3a28-4210-b6c0-5b959372647c" />

Purpose: Automatically collect conference schedules, sessions, speakers, venues, FAQs and other information, then index it in Elasticsearch.

System 2: Conference Helpdesk AI
Answer attendee questions and generate summaries.
<img width="1166" height="1552" alt="mermaid-diagram (2)" src="https://github.com/user-attachments/assets/4fb679df-f307-483c-b850-571e5ed0cb8c" />

Purpose: Allow attendees to ask questions in natural language, receive answers based on indexed conference information, and get a summary of their conversation at the end.

# Usage

The two systems are independent subpackages:

- `conference_helpdesk.crawler` — System 1: scrape sources, index into Elasticsearch.
- `conference_helpdesk.agent` — System 2: web helpdesk backed by Elastic Agent Builder.

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
#   set ES_URL + ES_API_KEY (your Elasticsearch cluster)
#   set KIBANA_URL           (the Kibana endpoint of the same cluster)

# 3. Crawl + index conference data (System 1)
PYTHONPATH=src python -m conference_helpdesk.crawler ingest
PYTHONPATH=src python -m conference_helpdesk.crawler stats

# 4. Run the web helpdesk (System 2)
PYTHONPATH=src python -m conference_helpdesk.agent serve   # http://127.0.0.1:8000
```

The helpdesk's LLM is handled entirely by **Elastic Agent Builder** (its Converse
API), so no Anthropic/OpenAI key is required — the agent reuses `ES_API_KEY` and
searches the indexed conference data to ground its answers.
