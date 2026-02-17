# Shared State Architecture Plan: The "Blackboard" System

This document details the design for the **Shared State** architecture where agents do not call each other directly but instead read from and write to a central database (the "Blackboard").

## 1. Core Concept
The "State" is the single source of truth.
- **Orchestrator**: Acts as the project manager. It watches the state and assigns tasks.
- **Agents**: Act as workers. They pick up tasks, do the work, and update the state.

## 2. Database Schema (The "Blackboard")
We will use **PostgreSQL** with `JSONB` columns for flexibility.

### A. `Contract` Table (The Master Record)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Unique ID for the document review session. |
| `user_id` | UUID | Owner of the document. |
| `filename` | String | Original filename. |
| `upload_path` | String | Path to the PDF/DOCX in storage (S3/Local). |
| `status` | Enum | `UPLOADED`, `EXTRACTING`, `ANALYZING_RISK`, `NEGOTIATING`, `COMPLETED`, `FAILED`. |
| `created_at` | DateTime | Timestamp. |

### B. `ExtractedClauses` Table (Output of Agent 1)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key. |
| `contract_id` | UUID | FK to Contract. |
| `parties` | JSONB | `{"party_a": "Google", "party_b": "User"}` |
| `clauses` | JSONB | The structured list of all clauses found. |
| `summary` | Text | High-level summary of the contract. |

### C. `RiskAnalysis` Table (Output of Agent 2)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key. |
| `contract_id` | UUID | FK to Contract. |
| `risk_score` | Integer | 0-100 score. |
| `flagged_risks` | JSONB | List of risks with severity and explanations. |
| `missing_clauses` | JSONB | List of standard clauses that were not found. |

### D. `NegotiationPlan` Table (Output of Agent 3)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key. |
| `contract_id` | UUID | FK to Contract. |
| `strategy` | JSONB | The negotiation strategy and batna. |
| `redlines` | JSONB | Specific text changes proposed. |

---

## 3. The Workflow (State Machine)

The system moves through these states. The **Orchestrator** (or a simple Event Listener) triggers the transitions.

### Phase 1: Ingestion
1.  **User** uploads a file.
2.  **API** saves file to object storage.
3.  **API** creates `Contract` record with `status="UPLOADED"`.
4.  **API** publishes event: `EVENT: CONTRACT_UPLOADED`.

### Phase 2: Extraction (triggered by `CONTRACT_UPLOADED`)
1.  **Clause Extraction Worker** listens for `CONTRACT_UPLOADED`.
2.  Worker fetches file, runs LLM extraction.
3.  Worker saves data to `ExtractedClauses` table.
4.  Worker updates `Contract.status="EXTRACTED"`.
5.  Worker publishes event: `EVENT: CLAUSES_READY`.

### Phase 3: Risk Analysis (triggered by `CLAUSES_READY`)
1.  **Risk Worker** listens for `CLAUSES_READY`.
2.  Worker reads `ExtractedClauses` from DB.
3.  Worker runs Risk Analysis LLM.
4.  Worker saves data to `RiskAnalysis` table.
5.  Worker updates `Contract.status="RISK_ANALYZED"`.
6.  Worker publishes event: `EVENT: RISKS_READY`.

---

## 4. API Interface (How Front-End sees it)

The Frontend does not wait for the agents. It polls the "Contract" status or opens a WebSocket.

**GET /contracts/{id}/status**
```json
{
  "status": "ANALYZING_RISK",
  "progress": 66,
  "current_step": "Checking Indemnity Clauses..."
}
```

**GET /contracts/{id}/result**
```json
{
  "contract_id": "123",
  "extracted_data": { ... }, // Populated if status > EXTRACTED
  "risk_report": { ... },    // Populated if status > RISK_ANALYZED
  "negotiation": { ... }     // Populated if status > NEGOTIATING
}
```

## 5. Implementation Roadmap

1.  **Setup Database**: Creates the tables defined above.
2.  **Refactor Agents**: Change agents to accept a `contract_id` as input, read from DB, and write to DB (instead of taking big JSON strings as arguments).
3.  **Event Bus**: Use Redis Pub/Sub or just simple database polling for the "Glue".
