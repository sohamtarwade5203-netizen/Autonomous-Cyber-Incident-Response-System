# System Architecture

This document provides a comprehensive overview of the Cyber Incident Response AI system architecture.

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        SIEM[SIEM Alerts]
        EDR[EDR Telemetry]
        LOGS[System Logs]
    end
    
    subgraph "Ingestion Layer"
        API[FastAPI REST API]
        ES[Elasticsearch]
        PARSER[Log Parser]
    end
    
    subgraph "Processing Pipeline"
        NORM[Normalization]
        FEAT[Feature Extraction<br/>tsfresh]
        ANOM[Anomaly Detection<br/>PyOD IsolationForest]
        UEBA[UEBA Correlation]
        RANK[Fidelity Ranking]
    end
    
    subgraph "AI Engine"
        AGENT[LangGraph Agent]
        DECISION[Decision Engine]
        LLM[Local LLM<br/>Ollama/Llama3]
        PLAYBOOK[Playbook Generator]
    end
    
    subgraph "Storage"
        DB[(SQLite Database)]
        FILES[Output Files]
    end
    
    subgraph "Interfaces"
        REST[REST API]
        METRICS[Prometheus Metrics]
    end
    
    SIEM --> API
    EDR --> API
    LOGS --> PARSER
    PARSER --> API
    
    API --> ES
    API --> NORM
    
    NORM --> FEAT
    FEAT --> ANOM
    ANOM --> UEBA
    UEBA --> RANK
    
    RANK --> AGENT
    AGENT --> DECISION
    DECISION --> LLM
    LLM --> PLAYBOOK
    
    PLAYBOOK --> DB
    PLAYBOOK --> FILES
    
    DB --> REST
    FILES --> REST
    REST --> METRICS
    
    style LLM fill:#f9f,stroke:#333,stroke-width:4px
    style AGENT fill:#bbf,stroke:#333,stroke-width:2px
    style ES fill:#ff9,stroke:#333,stroke-width:2px
```

---

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant ES as Elasticsearch
    participant Pipeline
    participant Agent as LangGraph Agent
    participant LLM as Ollama
    participant DB as Database
    
    Client->>API: POST /alerts/ingest
    API->>ES: Bulk index alerts
    API->>Pipeline: Process alerts
    
    Pipeline->>Pipeline: Normalize data
    Pipeline->>Pipeline: Extract features (tsfresh)
    Pipeline->>Pipeline: Detect anomalies (PyOD)
    Pipeline->>Pipeline: Correlate (UEBA)
    Pipeline->>Pipeline: Rank fidelity
    
    Pipeline->>Agent: High-fidelity incident
    Agent->>Agent: Analyze severity
    Agent->>Agent: Assess threat
    Agent->>Agent: Make decision
    
    Agent->>LLM: Generate playbook
    LLM-->>Agent: Playbook text
    
    Agent->>Agent: Validate playbook
    Agent->>DB: Store incident + playbook
    
    DB-->>API: Incident data
    API-->>Client: Response with incident_id
    
    Client->>API: GET /incidents/{id}/playbook
    API->>DB: Query playbook
    DB-->>API: Playbook data
    API-->>Client: Playbook JSON
```

---

## Component Architecture

```mermaid
graph LR
    subgraph "API Layer"
        MAIN[api/main.py]
        MODELS[api/models.py]
        AUTH[api/auth.py]
    end
    
    subgraph "Agent Layer"
        INCIDENT[agents/incident_agent.py]
        DECISION[agents/decision_engine.py]
        TOOLS[agents/tools.py]
        STATE[agents/state.py]
    end
    
    subgraph "Data Layer"
        DBMODELS[database/models.py]
        SESSION[database/session.py]
        ELASTIC[ingestion/elastic_connector.py]
    end
    
    subgraph "ML Layer"
        TSFRESH[ml/tsfresh_extractor.py]
        ANOMALY[scripts/anomaly_detection.py]
        UEBA[scripts/ueba_correlation.py]
        FIDELITY[scripts/fidelity_ranking.py]
    end
    
    MAIN --> INCIDENT
    MAIN --> DBMODELS
    MAIN --> ELASTIC
    
    INCIDENT --> DECISION
    INCIDENT --> TOOLS
    INCIDENT --> STATE
    
    ANOMALY --> TSFRESH
    UEBA --> ANOMALY
    FIDELITY --> UEBA
    
    INCIDENT --> FIDELITY
    
    SESSION --> DBMODELS
    MAIN --> SESSION
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose Environment"
        subgraph "API Container"
            FASTAPI[FastAPI Application<br/>Port 8000]
            PYTHON[Python 3.11]
        end
        
        subgraph "Elasticsearch Container"
            ES[Elasticsearch 8.11<br/>Port 9200]
            ESDATA[(ES Data Volume)]
        end
        
        subgraph "Ollama Container"
            OLLAMA[Ollama Service<br/>Port 11434]
            LLAMA3[Llama3 Model]
            OLLAMADATA[(Model Volume)]
        end
        
        subgraph "Monitoring Container"
            PROM[Prometheus<br/>Port 9090]
            PROMDATA[(Metrics Volume)]
        end
    end
    
    FASTAPI <--> ES
    FASTAPI <--> OLLAMA
    FASTAPI --> PROM
    
    ES --> ESDATA
    OLLAMA --> OLLAMADATA
    PROM --> PROMDATA
    
    style FASTAPI fill:#0f0,stroke:#333,stroke-width:2px
    style ES fill:#ff9,stroke:#333,stroke-width:2px
    style OLLAMA fill:#f9f,stroke:#333,stroke-width:2px
```

---

## Security Architecture

```mermaid
graph TB
    subgraph "External Boundary"
        FIREWALL[Firewall<br/>Localhost Only]
    end
    
    subgraph "Application Layer"
        API[FastAPI<br/>127.0.0.1:8000]
        AUTH[JWT Authentication]
        RATELIMIT[Rate Limiting]
    end
    
    subgraph "Processing Layer"
        VALIDATE[Input Validation]
        SANITIZE[Data Sanitization]
        AUDIT[Audit Logging]
    end
    
    subgraph "Data Layer"
        ENCRYPT[Encryption at Rest]
        DB[(SQLite Database)]
        ES[(Elasticsearch)]
    end
    
    subgraph "AI Layer"
        LOCAL[Local LLM Only<br/>No External Calls]
        OFFLINE[Offline Operation]
    end
    
    FIREWALL --> API
    API --> AUTH
    AUTH --> RATELIMIT
    RATELIMIT --> VALIDATE
    VALIDATE --> SANITIZE
    SANITIZE --> AUDIT
    
    AUDIT --> ENCRYPT
    ENCRYPT --> DB
    ENCRYPT --> ES
    
    SANITIZE --> LOCAL
    LOCAL --> OFFLINE
    
    style FIREWALL fill:#f00,stroke:#333,stroke-width:4px
    style AUTH fill:#0f0,stroke:#333,stroke-width:2px
    style LOCAL fill:#0ff,stroke:#333,stroke-width:2px
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API** | FastAPI | REST API endpoints |
| **Orchestration** | LangGraph | Agentic workflow |
| **LLM** | Ollama (Llama3) | Local playbook generation |
| **ML** | PyOD, tsfresh | Anomaly detection, feature extraction |
| **Search** | Elasticsearch | Log storage and search |
| **Database** | SQLite/PostgreSQL | Persistent storage |
| **Monitoring** | Prometheus | Metrics collection |
| **Testing** | pytest | Unit and integration tests |
| **Containerization** | Docker Compose | Service orchestration |

---

## Key Design Principles

1. **Offline-First**: All processing happens locally, no external API calls
2. **Explainability**: Full audit trail and reasoning traces
3. **Modularity**: Clean separation of concerns
4. **Scalability**: Designed for high-volume alert processing
5. **Security**: Defense-in-depth with multiple security layers
6. **Testability**: Comprehensive test coverage
