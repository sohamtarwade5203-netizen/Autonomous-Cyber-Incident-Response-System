# Deployment Guide

Complete guide for deploying the Cyber Incident Response AI system.

---

## Prerequisites

### System Requirements
- **OS**: Windows 10/11, Linux, or macOS
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 20GB free space
- **CPU**: 4 cores minimum

### Software Requirements
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- Git

---

## Quick Start (Docker)

### 1. Clone Repository

```bash
git clone <repository-url>
cd Cyber-Incident-Response-AI
```

### 2. Start All Services

```bash
docker-compose up -d
```

This will start:
- FastAPI (port 8000)
- Elasticsearch (port 9200)
- Ollama with Llama3 model (port 11434)

### 3. Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Check API health
curl http://localhost:8000/health

# Check Elasticsearch
curl http://localhost:9200/_cluster/health

# Check Ollama
docker exec cyber-ir-ollama ollama list
```

### 4. Run Demo Pipeline

```bash
# Enter API container
docker exec -it cyber-ir-api bash

# Run pipeline
python main.py
```

---

## Manual Deployment (Without Docker)

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Elasticsearch

**Windows**:
```powershell
# Download from https://www.elastic.co/downloads/elasticsearch
# Extract and run
.\bin\elasticsearch.bat
```

**Linux/Mac**:
```bash
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.11.0-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.11.0-linux-x86_64.tar.gz
cd elasticsearch-8.11.0
./bin/elasticsearch
```

### 3. Install Ollama

**Windows**:
```powershell
# Download from https://ollama.ai/download
# Run installer
# Pull model
ollama pull llama3
```

**Linux/Mac**:
```bash
curl https://ollama.ai/install.sh | sh
ollama pull llama3
```

### 4. Initialize Database

```bash
python -c "from database import init_database; init_database()"
```

### 5. Start API Server

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

---

## Configuration

### Environment Variables

Create `.env` file:

```env
# Database
DATABASE_URL=sqlite:///./cyber_ir.db

# Elasticsearch
ELASTICSEARCH_HOSTS=http://localhost:9200

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# API
API_HOST=127.0.0.1
API_PORT=8000
```

### Config File

Edit `config/config.yaml`:

```yaml
elasticsearch:
  hosts: ["http://localhost:9200"]
  enabled: true

database:
  url: "sqlite:///./cyber_ir.db"

ollama:
  model: "llama3"
  base_url: "http://localhost:11434"
```

---

## Running the Pipeline

### Full Pipeline

```bash
python main.py
```

### Individual Steps

```bash
# 1. Load logs
python scripts/load_logs.py

# 2. Anomaly detection
python scripts/anomaly_detection.py

# 3. UEBA correlation
python scripts/ueba_correlation.py

# 4. Fidelity ranking
python scripts/fidelity_ranking.py

# 5. Playbook generation
python scripts/playbook_generator.py
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v --cov=. --cov-report=html
```

### Run Specific Test Suites

```bash
# API tests
pytest tests/test_api.py -v

# Pipeline tests
pytest tests/test_pipeline.py -v

# Security tests
pytest tests/test_security.py -v
```

---

## Monitoring

### Prometheus Metrics

Start with monitoring profile:

```bash
docker-compose --profile monitoring up -d
```

Access Prometheus: http://localhost:9090

### Available Metrics

- `cyber_ir_alerts_total` - Total alerts ingested
- `cyber_ir_incidents_total` - Total incidents created
- `cyber_ir_playbooks_generated` - Total playbooks generated
- `cyber_ir_api_request_duration_seconds` - API response times

---

## Troubleshooting

### Elasticsearch Won't Start

```bash
# Check logs
docker logs cyber-ir-elasticsearch

# Common issue: Insufficient memory
# Solution: Reduce heap size in docker-compose.yml
ES_JAVA_OPTS=-Xms256m -Xmx256m
```

### Ollama Model Not Found

```bash
# Pull model manually
docker exec cyber-ir-ollama ollama pull llama3

# Verify
docker exec cyber-ir-ollama ollama list
```

### API Returns 500 Errors

```bash
# Check logs
docker logs cyber-ir-api

# Common issue: Database not initialized
docker exec cyber-ir-api python -c "from database import init_database; init_database()"
```

### Pipeline Fails

```bash
# Check data files exist
ls data/raw_logs/

# Required files:
# - siem_ddos_alerts.parquet
# - siem_portscan_alerts.parquet
# - siem_benign_traffic.parquet
```

---

## Production Deployment

### Security Hardening

1. **Enable API Authentication**:
```python
# In api/main.py
from api.auth import require_auth

@app.post("/alerts/ingest", dependencies=[Depends(require_auth)])
```

2. **Use PostgreSQL Instead of SQLite**:
```yaml
database:
  url: "postgresql://user:pass@localhost:5432/cyber_ir"
```

3. **Enable TLS**:
```bash
uvicorn api.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### Performance Tuning

1. **Increase Worker Processes**:
```bash
uvicorn api.main:app --workers 4
```

2. **Optimize Elasticsearch**:
```yaml
ES_JAVA_OPTS=-Xms2g -Xmx2g
```

3. **Enable Caching**:
```python
# Add Redis for caching
CACHE_URL=redis://localhost:6379
```

---

## Backup and Recovery

### Backup Database

```bash
# SQLite
cp cyber_ir.db cyber_ir.db.backup

# PostgreSQL
pg_dump cyber_ir > backup.sql
```

### Backup Elasticsearch

```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/backup"
  }
}
'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      replicas: 3
    
  elasticsearch:
    deploy:
      replicas: 3
```

### Load Balancing

Use nginx or HAProxy:

```nginx
upstream api_backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review troubleshooting section
3. Check GitHub issues
4. Contact: support@example.com
