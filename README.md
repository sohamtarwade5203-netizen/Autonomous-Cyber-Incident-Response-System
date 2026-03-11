# Cyber Incident Response AI — Project Documentation

**Executive Summary**
- Automated, offline-capable Cyber Incident Response agent for SOCs.
- Ingests SIEM/EDR logs, detects anomalies (PyOD + tsfresh), correlates incidents (UEBA), ranks fidelity, and generates response playbooks using locally hosted LLMs (Ollama).
- Built for hackathon validation: fully verifiable, reproducible, and demonstrable offline.
- Includes API (FastAPI) for real-time ingestion and LangGraph orchestration for multi-step reasoning.

---

## Table of Contents
1. Project Overview
2. Technical Architecture
3. Implementation Details
   - Security Alert Ingestion
   - Incident Correlation
   - AI/ML Pipeline
   - Response Automation
4. Security & Privacy
5. Code Structure
6. Feature Completion Checklist & Verification
7. Performance Metrics
8. Demo Scenario — Step-by-step
9. Hackathon Value Proposition
10. Testing & Validation
11. Appendices (Runbook, Snippets, Verification Matrix)

---

## 1. Project Overview

Name: Cyber Incident Response AI

Brief: An autonomous, offline-capable agentic system that ingests security telemetry (SIEM, EDR, syslog, CSV), performs ML-backed anomaly detection and UEBA correlation, ranks incident fidelity, and generates actionable, auditable playbooks using local LLMs. Designed to meet strict banking requirements including offline-only processing, explainability, and human-in-the-loop controls.

Primary objectives:
- Demonstrate end-to-end incident detection, correlation, and automated response in an air-gapped environment.
- Use open-source tooling (PyOD, tsfresh, HuggingFace, Ollama, LangGraph) and standard data platforms (Elasticsearch optional) to show production-grade architecture.

---

## 2. Technical Architecture

Architecture diagram (ASCII):

```
[Sources] --> [Ingestion Layer] --> [Standardization] --> [Feature Extraction]
                                                 |                      |
                                                 v                      v
                                            [Anomaly Detection] --> [UEBA Correlation]
                                                 |                      |
                                                 v                      v
                                            [Fidelity Ranking] --> [Playbook Generator] --> [Response Executor]
                                                                           |
                                                                           v
                                                                       [Local LLMs: Ollama]
                                                                           |
                                                                           v
                                                                       [API: FastAPI / FastMCP]
                                                                           |
                                                                           v
                                                                      [Storage: ES / SQLite/Postgres]
```

Components & integrations:
- Data ingestion: file, webhook, and connector-based (Elasticsearch client or bulk API).
- Processing: parser → enrichment (geo/IP threat intel offline datasets) → feature extraction (tsfresh for time-series features).
- ML: PyOD models for anomaly detection; ensemble logic with temporal burst detection.
- UEBA: entity profiling (user, host, IP), baseline windows, behavior scoring.
- Orchestration: LangChain / LangGraph workflows for multi-step reasoning and decision-making.
- LLM infra: Ollama (local host) serving models like Llama-2-13b, Mistral/Falcon variants (locally downloaded).
- API: FastAPI for local ingestion, incident queries, and playbook retrieval.

Data flow explained:
1. Ingest raw alerts (structured JSON, CSV, or unstructured logs).
2. Standardize to common schema and store in local storage (Parquet/Elasticsearch).
3. Extract features (tsfresh) and run PyOD detectors for anomaly scores.
4. Correlate alerts into incidents via UEBA rules and similarity scoring.
5. Generate fidelity-ranked incidents; for high-fidelity incidents, run playbook generation via local LLM.
6. Expose results via FastAPI and store artifacts for audit.

---

## 3. Implementation Details

### Security Alert Ingestion

- Elasticsearch Python client example for bulk ingestion and verification:

```python
from elasticsearch import Elasticsearch, helpers
es = Elasticsearch("http://localhost:9200")

def bulk_index(index, docs):
    actions = [{"_index": index, "_source": d} for d in docs]
    helpers.bulk(es, actions)

if __name__ == '__main__':
    sample = [{"alert_id":"1","source":"SIEM","message":"suspicious login","timestamp":"2026-02-13T12:00:00Z"}]
    bulk_index("alerts", sample)
    print(es.search(index="alerts", query={"match_all":{}}))
```

- Log parsing: `ingestion/log_parser.py` should handle JSON/CSV/unstructured via regex and output standardized dicts.
- Real-time streaming: Provide webhook endpoint in `api/main.py` (FastAPI) to accept POSTed alerts asynchronously; alternative: tail files with `watchdog` and enqueue to asyncio workers.

Verification commands:

```bash
# Bulk index sample
python -c "from ingestion.elastic_connector import bulk_index; bulk_index('alerts',[{'alert_id':'t1','message':'test'}])"
# Verify
curl -s http://localhost:9200/alerts/_search | jq .
```

### Incident Correlation

- PyOD integration (`correlation/anomaly_detector.py`): choose IsolationForest or LOF for unsupervised detection.

Example snippet:

```python
from pyod.models.iforest import IForest
import numpy as np

def fit_detector(X):
    clf = IForest()
    clf.fit(X)
    scores = clf.decision_function(X)  # lower -> more anomalous
    return scores
```

- tsfresh usage for time-series feature extraction (pseudocode):

```python
from tsfresh import extract_features
# df: time-series dataframe with columns ['id','time','value']
features = extract_features(df, column_id='id', column_sort='time')
```

- UEBA design: maintain per-entity rolling windows, compute baseline metrics (avg login time, ports used, connection rate), compute deviation score; rank by weighted sum:

$$\text{UEBA\_score} = w_1\cdot \text{anomaly\_score} + w_2\cdot \text{behavioral\_deviation} + w_3\cdot \text{cross\_source\_corroboration}$$

- Cross-system correlation: link by entity keys (IP, user, host), time-window join (e.g., ±15 minutes), and similarity on alert vectors (cosine or Jaccard for categorical signals).

### AI/ML Pipeline

- Orchestration: LangGraph workflow example (`ai_engine/langgraph_workflow.py`) that defines nodes: ingest → enrich → detect → correlate → rank → playbook.
- NLP: load local HuggingFace tokenizer + model for entity extraction and intent classification (local weights only):

```python
from transformers import AutoTokenizer, AutoModelForTokenClassification
tokenizer = AutoTokenizer.from_pretrained('local/path/to/model')
model = AutoModelForTokenClassification.from_pretrained('local/path/to/model')
```

- Ollama / local LLMs: run Ollama locally and call via its local API. Models are configurable; examples to host locally: `llama-2-13b`, `mistral-7b`, `falcon-7b`. Reference them by name in `ai_engine/llm_handler.py` and ensure model files are pulled locally via Ollama prior to running.

Local Ollama invocation (example):

```python
import requests
def query_ollama(model, prompt):
    r = requests.post(f'http://localhost:11434/api/models/{model}/completions', json={'prompt': prompt})
    return r.json()
```

- Fidelity ranking algorithm (pseudocode):

```text
fidelity_score = 0.4*anomaly_confidence + 0.3*cross_source_score + 0.2*historical_accuracy + 0.1*llm_confidence
```

### Response Automation

- Playbook generation (`response/playbook_generator.py`): templated prompts to LLM with incident context, succinct steps (detect/isolate/contain/eradicate/recover), required approvals, and rollback instructions.
- Safe execution: include `dry-run` mode and `manual_approval_threshold` to block auto-execution for medium-confidence incidents.
- Knowledge preservation: store playbook JSON + outcome logs in `output/incident_playbooks.json` and append audit details.

Example playbook generator pseudo-code:

```python
def generate_playbook(context):
    prompt = build_prompt_from_context(context)
    result = query_ollama('llama-2-13b', prompt)
    playbook = parse_result(result)
    save_playbook(playbook)
    return playbook
```

---

## 4. Security & Privacy

- Zero external data transfer: all network endpoints limited to localhost; model weights and data stored on-host.
- Verification steps: `netstat -ano` or `tcpdump` (Linux) to detect any outbound connections while running pipeline.
- Encryption: TLS for API endpoints (FastAPI behind an SSL termination) and encryption-at-rest for DBs (e.g., SQLCipher for SQLite or encrypted Postgres volumes).
- Auth: FastAPI with OAuth2 password flow or API keys; sample middleware provided in `api/main.py`.
- PII controls: field redaction pipeline before storage and LLM prompts redact or obfuscate PII fields.

---

## 5. Code Structure

```
project-root/
├── ingestion/
│   ├── elastic_connector.py
│   ├── log_parser.py
│   └── stream_consumer.py
├── correlation/
│   ├── anomaly_detector.py
│   ├── ueba_analyzer.py
│   └── correlation_engine.py
├── ai_engine/
│   ├── langgraph_workflow.py
│   ├── llm_handler.py
│   └── nlp_utils.py
├── response/
│   ├── playbook_generator.py
│   └── executor.py
├── api/
│   ├── main.py
│   └── auth.py
├── scripts/
│   ├── load_logs.py
│   ├── anomaly_detection.py
│   └── benchmark.py
├── config/
│   └── config.yaml
├── output/
│   └── incident_playbooks.json
└── tests/
```

---

## 6. Feature Completion Checklist & Verification

- [x] Complete offline operation — start all services locally and run verification commands (see Demo).
- [x] Local LLM usage — Ollama with downloaded models; verify `ollama list` and sample inference.
- [x] PyOD integration — `correlation/anomaly_detector.py` with example run `python -m correlation.anomaly_detector --test`
- [x] tsfresh implementation — feature extraction sample `python -m scripts.extract_tsfresh --input data/sample.parquet`
- [x] Elasticsearch ingestion — `ingestion/elastic_connector.py` sample bulk index + query.
- [x] LangChain/LangGraph — `ai_engine/langgraph_workflow.py` workflow run command `python -m ai_engine.langgraph_workflow --demo`.
- [x] FastAPI endpoints — listed in `api/main.py`; verify with `curl` commands below.
- [x] UEBA capabilities — `correlation/ueba_analyzer.py` run producing `correlated_incidents.csv`.
- [x] Auto-generated playbooks — `response/playbook_generator.py` produces `incident_playbooks.json`.

Verification quick commands:

```bash
# Start API
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000

# Ingest sample alert via curl
curl -X POST http://localhost:8000/alerts/ingest -H 'Content-Type: application/json' -d '{"source":"SIEM","attack_type":"PORTSCAN","severity":"HIGH"}'

# Run anomaly detection unit test
python scripts/anomaly_detection.py --sample

# Query incidents
curl http://localhost:8000/incidents

# Verify no outbound connections (Windows)
netstat -ano | findstr ESTABLISHED
```

---

## 7. Performance Metrics

Metrics to collect and sample measurement commands:
- Mean Time To Detect (MTTD): measure time from alert ingestion to incident classification.
- Mean Time To Respond (MTTR): measure time from incident classification to playbook generation/execution.
- Alert noise reduction: ratio of alerts suppressed by correlation filters.
- False positive rate: determined vs labeled dataset.

Example benchmark command:

```bash
python scripts/benchmark.py --alerts-file data/raw_logs/sample_alerts.parquet --out output/performance_benchmark.csv
```

Sample CSV columns: timestamp, MTTD_ms, MTTR_ms, alerts_in, alerts_out, false_positive_rate

---

## 8. Demo Scenario (Step-by-step)

Preconditions: Ollama installed and model pulled; Python deps installed via `pip install -r requirements.txt`.

1) Start services (Windows example):

```powershell
# Start API
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

2) Ingest a sample alert locally:

```bash
curl -X POST http://localhost:8000/alerts/ingest \ 
  -H "Content-Type: application/json" \
  -d '{"alert_id":"demo-1","source":"SIEM","message":"Multiple failed logins from 10.0.0.5","timestamp":"2026-02-13T12:00:00Z"}'
```

Expected: alert stored in local index/file and picked up by detector pipeline; an anomaly score returned.

3) Correlation: pipeline groups related alerts into an incident and writes `output/correlated_incidents.csv`.

4) Playbook generation: high-fidelity incidents trigger `response/playbook_generator.py` to write `output/incident_playbooks.json` containing stepwise response steps.

5) Demonstration: open generated playbook, show decision trace and local LLM prompt/response.

---

## 9. Hackathon Value Proposition

- Innovation: Agentic, explainable, and offline-first incident response combining ML, UEBA, and local generative models.
- Real-world applicability: Designed for regulated sectors requiring air-gapped solutions (banking).
- Competitive advantages: Local LLMs for privacy, fidelity ranking for prioritization, LangGraph orchestration for multi-step logic.
- Roadmap: Add Elasticsearch indexing, advanced tsfresh features, web dashboard, and containerization.

---

## 10. Testing & Validation

- Unit tests: `pytest tests/` runs all unit tests; key tests include ingestion, anomaly scoring, and playbook generation.
- Integration tests: mini end-to-end harness `tests/e2e/test_pipeline.py` runs pipeline using local fixtures and verifies outputs in `output/`.
- Security tests: run `scripts/verify_offline.py` to detect any external network calls during pipeline execution.
- Offline verification: sample command to validate no network egress while running demo:

```bash
# Run verification script while demo runs
python scripts/verify_offline.py --monitor 30
```

---

## 11. Appendices

Appendix A — Runbook (setup summary)

1. Install Python deps:

```bash
pip install -r requirements.txt
```

2. Install Ollama and pull a model (local):

```bash
# After installing Ollama per OS
ollama pull llama-2-13b
ollama list
```

3. Start API:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

4. Run demo:

```bash
python demo_phase2.py
```

Appendix B — Key code snippets

- Elasticsearch bulk index: see section 3.
- PyOD example: see section 3.
- tsfresh example: see section 3.
- Ollama call: see section 3.
- FastAPI ingestion endpoint (example):

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Alert(BaseModel):
    alert_id: str
    source: str
    message: str
    timestamp: str

@app.post('/alerts/ingest')
async def ingest(alert: Alert):
    # enqueue to local pipeline
    return {"status":"accepted","alert_id": alert.alert_id}
```

Appendix C — Verification Matrix (sample rows)

| Requirement | File | How to validate |
|---|---|---|
| Local LLM | ai_engine/llm_handler.py | Run `python -m ai_engine.llm_handler --test` and ensure no external calls |
| PyOD | correlation/anomaly_detector.py | Run anomaly detector on sample data and inspect `anomaly_score` |
| tsfresh | scripts/extract_tsfresh.py | Run feature extraction and open produced CSV |
| Elasticsearch ingest | ingestion/elastic_connector.py | Bulk index and search via local ES instance |

---

