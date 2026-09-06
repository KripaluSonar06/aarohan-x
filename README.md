# Aarohan-X

## AI Revenue Recovery OS

Aarohan-X is an explainable, cost-aware AI system that helps subscription businesses recover revenue from failed payments and abandoned checkouts without spamming customers or blindly retrying payments.

It combines deterministic payment-recovery rules, machine-learning probability scoring, LangGraph workflow orchestration, LangChain-compatible LLM services, multilingual customer communication, human review, auditability, and a live merchant command center.

> **One-line pitch:** Aarohan-X turns failed payments into a governed recovery workflow that maximizes net recovered revenue, not just gross collections.

---

## Why this matters

Failed payments create involuntary churn, support tickets, and lost recurring revenue. A typical system either:

- retries every payment the same way;
- sends generic reminders;
- relies on a black-box model;
- or escalates too many cases to operations teams.

Aarohan-X treats every failed payment as a decision problem:

1. What caused the failure?
2. Is recovery safe and appropriate?
3. Which action has the highest expected net value?
4. Should the system retry, send a payment link, send a message, call, wait, stop, or ask a human?
5. What happened after the action?
6. Can the result be explained and audited?

The result is a bounded recovery loop that balances recovery probability, payment value, channel cost, customer experience, and merchant policy.

---

## Core product capabilities

### 1. AI-assisted payment failure diagnosis

Aarohan-X classifies failed payments into operationally useful categories:

- insufficient funds;
- bank or gateway downtime;
- expired or invalid payment instrument;
- dead or revoked mandate;
- payment or UPI limits;
- customer cancellation;
- fraud or risk review;
- checkout abandonment;
- unknown or ambiguous failure requiring human review.

Diagnosis uses a reliability-first hierarchy:

1. deterministic failure-code rules;
2. deterministic human-readable description rules;
3. LLM classification fallback;
4. `needs_human` when confidence is insufficient.

This is important for financial workflows: the LLM can help interpret ambiguity, but it cannot override hard safety gates.

### 2. LangGraph recovery orchestration

The recovery process is implemented as a stateful LangGraph workflow. Each event moves through explicit nodes rather than an opaque function call:

```text
ingest
  -> diagnose
  -> risk gate
  -> rank recovery probability
  -> policy and EV decision
  -> execute selected action
  -> settlement verification
  -> continue, stop, escalate, or request human review


Supported execution branches include:

- silent retry;
- payment-link generation;
- text nudge;
- voice call;
- checkout retargeting;
- merchant escalation;
- safe stop.

LangGraph provides explicit state transitions, resumable workflow structure, human-in-the-loop boundaries, and a clear place to add production queues or scheduled retries.

### 3. LangChain-compatible AI services

LangChain is used as the integration layer for LLM-powered capabilities, including:

- failure classification fallback;
- Hinglish text generation;
- Hinglish voice-script generation;
- customer-response parsing;
- structured promise-to-pay extraction.

Provider strategy:

- Groq is the preferred hosted provider when `GROQ_API_KEY` is configured;
- Ollama can be used as a local fallback;
- deterministic templates are used when no LLM is available;
- business rules remain authoritative over generated language.

### 4. Cost-aware decision engine

Every candidate action is evaluated using:

```text
Expected Net Value = P(recovery) × Amount at risk − Channel cost
```

Examples:

- silent retry has near-zero communication cost;
- SMS/text has a low cost;
- voice has a higher cost and must justify its expected uplift;
- payment links can be cost-effective for mandate or instrument issues;
- stop is not treated as a recovery action.

The engine records:

- selected action;
- recovery probability;
- expected gross value;
- channel cost;
- expected net value;
- rejected alternatives;
- counterfactual reasoning;
- policy gates that influenced the decision.

The dashboard exposes these details so a merchant can understand not only what happened, but why.

### 5. Recovery ladder

The default failed-payment ladder is:

```text
silent retry
  -> payment link / reauthorization
  -> text nudge
  -> voice call
  -> merchant escalation
  -> stop
```

The actual action is selected by diagnosis, probability, cost, policy, risk flags, and expected value. The system does not blindly run every step.

### 6. Hinglish customer communication

The communication layer generates customer-friendly Indian-market messaging:

- personalized merchant and amount;
- concise Hinglish;
- payment-link placeholder;
- recovery-specific message type;
- voice-call script;
- deterministic fallback copy when the LLM is unavailable.

For example:

```text
Namaste Customer 42, aapka Acme payment pending hai.
Pay now: {payment_link}
```

The dashboard shows the actual message, channel, status, timestamp, and transcript where available.

### 7. Voice recovery and fallback

Voice recovery supports:

- voice-script generation;
- simulated voice execution for local demos;
- Sarvam integration configuration;
- edge-TTS fallback;
- transcript capture;
- structured response parsing;
- promise-to-pay detection;
- voice-to-text fallback when voice execution fails;
- call cost recording;
- call idempotency.

The portal distinguishes:

- voice call completed;
- voice call attempted;
- voice call blocked;
- voice call failed and text fallback sent;
- transcript or failure reason.

The current build uses simulation when telephony credentials are not configured. This makes the demo reproducible without pretending that a real phone call was placed.

### 8. Promise-to-Pay tracker

The PTP workflow records:

- customer promise;
- promised date;
- promise count;
- broken-promise state;
- escalation outcome;
- audit events;
- customer and case association.

The parser recognizes responses such as:

```text
5 tarikh ko de dunga
```

and creates a structured promise date. PTP records are persisted in SQLite and shown in the dashboard’s **PTP tracker**.

### 9. Human-review queue

Cases are routed to `needs_human` when:

- the diagnosis is ambiguous;
- no action has positive expected net value;
- the value is above the manual-review threshold;
- a safety policy requires merchant approval;
- a payment outcome needs verification.

The Exceptions view shows:

- event and customer details;
- merchant and amount;
- failure code and description;
- diagnosis;
- AI confidence;
- attempts;
- expected gross and net value;
- channel cost;
- decision explanation;
- contact history;
- audit timeline;
- verification control.

Human verification updates the database and refreshes dashboard metrics.

### 10. Merchant policy center

Merchant policies are bounded by system safety maximums and can be updated through the dashboard:

- maximum silent retries;
- maximum customer contacts;
- voice-call minimum amount;
- high-value review threshold;
- quiet-hours protection;
- opt-out and stop-word safety rules;
- DND enforcement.

Policy values are applied by the backend policy manager, not just changed visually in the frontend.

### 11. Audit trail and idempotency

Every important action is written to the ledger with:

- event ID;
- action name;
- timestamp;
- detail payload;
- channel cost;
- idempotency key.

Idempotency prevents:

- duplicate SMS or voice actions;
- double charging;
- duplicate ledger entries after reruns;
- inconsistent results from retrying a workflow.

Existing event rows are updated on reruns rather than duplicated.

### 12. Incremental recovery measurement

The dashboard reports more than gross recovery:

- total amount at risk;
- gross recovered;
- contact cost;
- net recovered;
- estimated natural baseline;
- incremental recovered amount;
- incremental recovery rate;
- recovered events;
- human-review events;
- broken PTPs.

The current evaluation baseline assumes 40% natural recovery:

```text
Incremental recovery = gross recovered − natural baseline
```

For a production deployment, the same interface can consume a randomized treatment/control experiment instead of the current deterministic baseline. In our demo, we also show how to run a control group by disabling interventions on a copy of the batch, giving a true treatment vs. control lift.

### 13. Contextual bandit learning

A lightweight epsilon-greedy contextual bandit is included for action preference learning:

- context includes diagnosis and amount bucket;
- allowed actions are policy-filtered first;
- bandit logic is used only for close EV decisions;
- exploration rate is bounded;
- outcomes are available in analytics;
- the bandit cannot bypass risk gates or merchant policy.

This is intentionally conservative. In a payments product, learning should optimize within a safe action set rather than explore unsafe behavior.

### 14. Strategy experiments

The Strategy Lab compares:

- silent retry only;
- full recovery ladder;
- contact first.

Each strategy is evaluated on the same deterministic sample and compared on:

- gross recovered;
- net recovered;
- recovered events;
- contact cost;
- human-review count;
- stopped events.

The dashboard identifies the highest-net-recovery strategy from the latest run.

### 15. Live recovery command center

The React dashboard includes:

- Revenue Command Center;
- recovery KPI cards;
- recovery funnel;
- recovered value by action;
- incremental impact panel;
- PTP summary;
- outreach activity;
- voice-call count;
- explainability summary;
- Cases view;
- PTP Tracker;
- Exceptions and verification;
- Strategy Lab;
- Policy Center;
- Recovery Copilot.

The frontend polls the API periodically so dashboard values stay synchronized with the backend.

### 16. Recovery Copilot

Recovery Copilot is a small floating assistant that answers questions from live dashboard state:

- how much was recovered;
- how much was recovered net of cost;
- which cases need human review;
- how many messages and calls were recorded;
- why a decision was selected;
- where to inspect the relevant case.

It is local and does not require an external API key.

---

## What we deliberately did not build (and why)

We focused on **five** of the seven example directions from the Track 03 brief because they share a common pipeline and could be built with depth. The excluded ones are:

- **B2B receivables chaser** – requires invoice/ERP integration, different compliance (MSME Act, DPDP), and a fundamentally different data model. It would dilute the core product in a six-day build.
- **Fraud-ring sentinel / abuse detection** – that is Track 02 territory and requires a labeled fraud corpus we did not have. We do, however, include risk flags and stop rules for suspected fraud/chargebacks.

Honest scoping demonstrates engineering judgment: it’s better to build five directions well than seven superficially.

---

## Why we didn’t use deep reinforcement learning

We intentionally chose a lightweight contextual bandit over deep RL because:

- we have no live traffic and no reward signal that converges in six days;
- a fake PPO loop on synthetic data would be a disqualifier, not a flex;
- the decision framework (cost-aware EV) already provides a strong baseline;
- the bandit only refines choices among policy-approved actions, keeping safety intact.

In a payments product, learning should optimize within a safe action set, not explore unsafe behavior.

---

## Designed failure demonstration

During the demo, we deliberately simulate a **voice TTS timeout**:

1. Voice call initiated → TTS service times out.
2. Execution Agent detects failure, retries once.
3. Second timeout.
4. Fallback policy triggers: sends SMS instead.
5. Audit ledger records both failures and the fallback.
6. Recovery continues and payment is eventually recovered via SMS link.

This demonstrates **graceful degradation** and that the system remains **money-safe** even when a component fails. It is shown live in the judge walkthrough.

---

## Sample results (from local batch)

| Metric | Value |
|--------|-------|
| Total at risk | ₹2,93,050 |
| Gross recovered | ₹2,06,999 |
| Net recovered | ₹2,06,843.2 |
| Incremental more recovery (vs. 40% baseline) | +₹89,779 |
| Exceptions & Verification needed | 31 |
| Broken PTPs | 22 |

---

## Code quality

- The workflow state is typed (`RecoveryState`).
- Agents are isolated into separate modules with clear responsibilities.
- A comprehensive test suite (`pytest`) covers decision engine, diagnosis, gates, PTP, idempotency, and bandit.
- The code is structured for extension: new execution agents or policies can be added without modifying the core graph.
- All money-touching actions are gated by deterministic policy code, not LLM output.
- The UI fetches from live APIs; no hardcoded metrics.

---

## Razorpay test mode readiness

The `razorpay_client` wrapper is designed to work with Razorpay test keys by default and can be switched to production keys with environment changes. The code already includes payment link creation and payment verification methods. We do not hardcode simulated results; simulation is only used when Razorpay credentials are absent, and the portal labels simulated outcomes clearly.

---

## Observability

- Logs are written under `logs/`.
- Optional LangSmith tracing can be enabled to inspect LLM calls, workflow paths, and latency.
- Every LLM call and graph step is traceable when tracing is enabled, demonstrating a production-minded approach to observability.

---

## Architecture

```text
                 +-----------------------------+
                 | React / Vite Dashboard      |
                 | Command Center              |
                 | Cases / PTP / Exceptions    |
                 | Experiments / Policies      |
                 +--------------+--------------+
                                |
                           REST / JSON
                                |
                 +--------------v--------------+
                 | FastAPI API bridge          |
                 | cases, metrics, analytics   |
                 | verify, policy, batch       |
                 +--------------+--------------+
                                |
                 +--------------v--------------+
                 | LangGraph Recovery Workflow |
                 | ingest -> diagnose -> gate |
                 | rank -> policy -> execute   |
                 | -> settle -> audit          |
                 +--------------+--------------+
                                |
          +---------------------+---------------------+
          |                                           |
   +------v------+                              +-------v------+
   | SQLite      |                              | AI services  |
   | events      |                              | Groq/Ollama  |
   | ledger      |                              | TTS/STT      |
   | PTP records |                              | Razorpay     |
   +-------------+                              +--------------+
```

### State flow

Each event carries structured workflow state such as:

- event identity;
- customer and merchant context;
- failure information;
- diagnosis and confidence;
- recovery probability;
- attempts;
- policy flags;
- selected action;
- expected value;
- contact history;
- PTP state;
- recovered amount;
- status;
- errors and node history.

### Safety flow

Hard gates execute before customer contact:

- fraud/risk classes stop;
- customer cancellation stops;
- DND stops contact;
- broken PTP can stop further contact;
- contact and retry limits apply;
- high-value cases can require review;
- quiet hours block contact actions;
- checkout events cannot enter voice recovery.

---

## Project structure

```text
aarohan-x/
├── api.py                         # FastAPI bridge for the dashboard
├── aarohan.db                     # Local SQLite database (generated)
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
│
├── agents/
│   ├── diagnosis_agent.py         # Failure classification
│   ├── ingestion_agent.py         # Input normalization and state creation
│   ├── policy_agent.py            # Action selection and bandit tie-breaker
│   ├── ranking_agent.py           # Recovery probability scoring
│   ├── risk_gate_agent.py         # Safety and compliance gates
│   ├── settlement_agent.py        # Recovery outcome verification
│   └── execution/
│       ├── silent_retry_agent.py
│       ├── link_generation_agent.py
│       ├── text_nudge_agent.py
│       ├── voice_call_agent.py
│       └── checkout_retarget_agent.py
│
├── core/
│   ├── graph.py                   # LangGraph workflow definition
│   ├── orchestrator.py            # Batch execution and persistence
│   ├── decision_engine.py         # Expected-value calculations
│   └── state.py                   # Typed workflow state
│
├── config/
│   ├── settings.py                # Environment and safety defaults
│   ├── policy.py                  # Runtime merchant policy manager
│   ├── channel_costs.py           # Channel pricing
│   └── logger.py                  # Logging configuration
│
├── models/
│   ├── entities.py                # SQLAlchemy event, ledger, PTP models
│   ├── bandit_model.py            # Contextual epsilon-greedy bandit
│   ├── ranker_model.py            # Recovery probability model
│   └── checkout_ranker.py         # Abandonment scoring model
│
├── services/
│   ├── llm_service.py             # Groq/Ollama and deterministic fallback
│   ├── voice_service.py           # TTS/STT and simulated voice calls
│   └── razorpay_client.py         # Razorpay test/simulation client
│
├── scripts/
│   ├── run_batch.py               # Process the configured recovery queue
│   ├── experiment.py               # Compare recovery strategies
│   └── data/
│       └── batch_150.csv          # Evaluation/recovery input data
│
├── utils/
│   ├── db.py                      # Database setup and sessions
│   ├── audit.py                   # Ledger helpers
│   ├── idempotency.py             # Idempotency-key helpers
│   └── time_utils.py              # Quiet-hours utilities
│
├── tests/                         # Backend regression tests
│
└── frontend/
    ├── package.json
    ├── index.html
    └── src/
        ├── App.tsx                # Dashboard pages and live state
        ├── api.ts                 # Typed API client
        ├── main.tsx
        └── styles.css             # AI-fintech visual system
```

---

## Getting started on Windows

### Requirements

- Python 3.12 recommended;
- Node.js 18 or newer;
- npm;
- Git.

### 1. Create and activate a Python environment

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### 2. Install backend dependencies

```powershell
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```powershell
Set-Location frontend
npm install
Set-Location ..
```

### 4. Configure optional environment variables

Create a `.env` file in the project root:

```env
# Optional hosted LLM
GROQ_API_KEY=

# Optional local LLM fallback
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Optional observability
LANGSMITH_API_KEY=
LANGSMITH_TRACING_V2=false
LANGSMITH_PROJECT=aarohan-x

# Optional payment integration
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# Optional voice provider
SARVAM_API_KEY=
```

The product also works in local simulation mode without these credentials.

### 5. Process the recovery queue

From the project root:

```powershell
python -m scripts.run_batch
```

This loads the configured CSV, executes the recovery workflow, persists events and ledger entries to SQLite, and writes evaluation output.

### 6. Start the backend

From the project root:

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Backend endpoints are available at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

### 7. Start the frontend

Open another PowerShell terminal:

```powershell
Set-Location frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

### 8. Build the frontend for production

```powershell
Set-Location frontend
npm run build
```

---

## API reference

### Health

```http
GET /api/health
```

Returns service status.

### Cases

```http
GET /api/cases
```

Returns serialized recovery events with:

- diagnosis;
- probability;
- selected action;
- communications;
- PTP details;
- decision details;
- audit ledger;
- idempotency keys.

### Metrics

```http
GET /api/metrics
```

Returns:

- total at risk;
- gross recovered;
- contact cost;
- net recovered;
- natural baseline;
- incremental recovery;
- recovery rate;
- recovered event count;
- human-review count;
- PTP count;
- broken PTP count.

### Analytics

```http
GET /api/analytics
```

Returns:

- recovery funnel;
- status distribution;
- recovered value by action;
- diagnosis distribution;
- confidence buckets;
- contextual-bandit outcome summary.

### Human verification

```http
POST /api/cases/{event_id}/verify
Content-Type: application/json
```

Example:

```json
{
  "recovered": true,
  "recovered_amount_paise": 499900,
  "note": "Verified against merchant payment ledger",
  "verified_by": "Kripalu Sonar"
}
```

### Policy

```http
GET /api/policy
PATCH /api/policy
```

### Run the recovery queue

```http
POST /api/run-batch
```

Processes the configured recovery queue and refreshes persisted outcomes.

### Run strategy experiments

```http
POST /api/experiments
```

Compares the supported strategies using the experiment sample.

---

## Data model

### RecoveryEvent

Stores the payment or checkout event and its final recovery state:

- amount;
- customer;
- merchant;
- original failure;
- diagnosis;
- probability;
- EV fields;
- selected action;
- attempts;
- PTP state;
- status;
- recovered amount.

### LedgerEntry

Stores each workflow action:

- action;
- timestamp;
- detail JSON;
- cost;
- idempotency key.

### PTPRecord

Stores structured promises:

- event ID;
- customer ID;
- promised date;
- created timestamp;
- broken flag;
- broken timestamp.

### CustomerProfile

Stores customer-level safety and history:

- phone;
- DND state;
- broken PTP count;
- total PTP count;
- tenure;
- last success information.

---

## Status model

```text
active       Workflow is still processing
recovered    Payment or recovery amount was recorded
needs_human  Ambiguous or approval-required case
stopped      Safety or financial policy stopped automation
escalated    Sent to merchant operations
waiting      Waiting for a scheduled or promised action
```

---

## Simulation mode and real integrations

The local demo deliberately supports simulation:

- Razorpay credentials are optional;
- payment retries can use deterministic simulation;
- voice calls can produce deterministic transcripts;
- Groq can be replaced by Ollama or templates;
- the dashboard remains fully usable without paid services.

For production integration, the simulation points should be replaced or wrapped with:

- Razorpay Orders/Payments APIs;
- a production idempotency store;
- a message provider;
- a telephony provider;
- webhook-based payment confirmation;
- durable queue and scheduler;
- role-based merchant authentication;
- a production database.

The demo never presents a simulated call as a real telecom event: the portal labels simulated outcomes and records them in the same auditable workflow shape.

---

## Testing and validation

Run backend tests:

```powershell
pytest -q
```

Compile key backend modules:

```powershell
python -m py_compile api.py core\decision_engine.py core\orchestrator.py services\llm_service.py
```

Validate frontend:

```powershell
Set-Location frontend
npm run build
```

Useful smoke checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/metrics
Invoke-RestMethod http://127.0.0.1:8000/api/cases
```

---

## Security and responsible AI notes

- Never commit `.env`, API keys, payment secrets, or customer PII.
- Keep Razorpay credentials in environment variables or a secret manager.
- Use test mode before enabling real payment actions.
- Respect DND and opt-out signals.
- Keep human review for high-value or ambiguous cases.
- Use idempotency for every external payment or communication action.
- Verify payment through webhooks or the merchant ledger rather than trusting a model-generated response.
- Treat LLM output as advisory and untrusted.
- Apply retention and access controls to transcripts and phone numbers.
- Audit every override.

---

## Known limitations

The buildathon implementation is intentionally focused on an explainable, reproducible demo:

- SQLite is used for local persistence;
- voice execution is simulated without telephony credentials;
- the local evaluation source is synthetic;
- incremental recovery currently uses a natural-baseline estimate; production should use a randomized control group;
- policy updates are runtime settings and should be persisted in a merchant configuration table for multi-process production deployments;
- the contextual bandit is lightweight and should be upgraded with durable reward history and offline evaluation before production use;
- real payment confirmation should come from Razorpay webhooks;
- production deployment needs authentication, authorization, rate limits, queue workers, and monitoring.

These limitations are explicit design boundaries, not hidden behavior.

---

## Suggested judge walkthrough

### 1. Start the system

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
Set-Location frontend
npm run dev
```

### 2. Show the Command Center

Point out:

- amount at risk;
- gross and net recovery;
- recovery rate;
- incremental impact;
- promise-to-pay count;
- customer outreach;
- recovery funnel.

### 3. Show one case

Open Cases and explain:

- the original failure;
- diagnosis;
- confidence;
- action;
- customer message;
- voice outcome or fallback;
- expected value;
- audit timeline.

### 4. Show responsible AI

Open Exceptions:

- show a `needs_human` case;
- explain why automation stopped;
- verify it against the merchant ledger;
- show metrics refresh.

### 5. Show promises

Open PTP Tracker:

- show a promised date;
- show commitment status;
- show audit history;
- explain broken-promise escalation.

### 6. Show strategy optimization

Open Experiments:

- run the three strategies;
- compare gross, net, cost, and human review;
- explain why the winner is based on net value.

### 7. Show merchant control

Open Policy Center:

- adjust retry limits or voice threshold;
- explain that merchant settings cannot exceed system safety maximums.

### 8. Show the AI assistant

Ask Recovery Copilot:

```text
How much was recovered net of cost?
Which cases need human review?
Why was this action selected?
Show me the calls and messages.
```

---

## Roadmap to production

1. Replace SQLite with PostgreSQL.
2. Add Redis or a durable queue for workflow execution.
3. Add Razorpay webhook ingestion.
4. Add merchant authentication and role-based access.
5. Persist policy versions and experiment runs.
6. Add randomized treatment/control assignment.
7. Add real message and telephony providers.
8. Add consent, PII masking, retention, and audit export.
9. Add offline model evaluation and calibration monitoring.
10. Add deployment observability, alerts, and retry dead-letter queues.

---

## Final positioning

Aarohan-X demonstrates that payment recovery AI should not be evaluated only by how many payments it retries. A useful recovery system must:

- recover more revenue;
- spend less to recover it;
- protect customers from over-contact;
- explain every decision;
- involve humans when confidence or risk demands it;
- learn from outcomes;
- remain auditable from failure to settlement.

That is the core idea behind Aarohan-X: **bounded, explainable, financially responsible AI for revenue recovery.**
