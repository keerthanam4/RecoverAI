# RecoverAI — AI Revenue Recovery Control Center

**Razorpay Buildathon 2026 — Track 03: AI Revenue Recovery**

RecoverAI is an AI-powered revenue recovery control center that predicts payment recovery probability, diagnoses failure patterns, selects the safest recovery strategy, and governs execution through deterministic policy controls.

> **AI decides. Policy governs. Execution is bounded.**

---

## Features 🚀

- ML-based recovery probability prediction
- Expected recoverable value estimation
- AI-powered failure diagnosis
- Automated recovery strategy selection
- Policy-based execution authorization
- Bounded Razorpay Payment Link execution
- Human escalation for high-risk cases
- Stop rules for low-probability recovery opportunities
- Idempotent recovery execution
- Execution blocking for incompatible actions
- Complete recovery execution audit trail
- Recovery performance and strategy evaluation

---

## What It Solves 🎯

Payment failures and checkout abandonment create revenue leakage.

RecoverAI determines **what should happen next** for each recovery opportunity instead of applying the same recovery action to every transaction.

The system balances:

- Recovery potential
- Transaction value
- Failure reason
- Customer history
- Retry history
- Checkout abandonment
- Operational risk
- Human-review requirements

---

## Recovery Workflow 🔄

```text
Transaction Data
      ↓
Feature Engineering
      ↓
ML Recovery Prediction
      ↓
Recovery Probability
      ↓
AI Diagnosis
      ↓
AI Decision Engine
      ↓
Policy Evaluation
      ↓
Recovery Strategy
      ↓
Bounded Execution / Human Escalation / Stop
      ↓
Audit Trail
      ↓
Evaluation & Monitoring
```
---

## Recovery Strategies 🎯

RecoverAI can select five recovery outcomes:

| Strategy | Purpose |
|---|---|
| `RETRY` | Retry recoverable payment failures |
| `PAYMENT_LINK` | Create a payment link for abandoned or recoverable payments |
| `REMINDER` | Send a recovery reminder without executing payment recovery |
| `STOP` | Stop recovery attempts when probability or policy conditions indicate low value |
| `ESCALATE` | Route high-risk or high-value cases for human intervention |

---

## Policy & Safety 🛡️

RecoverAI separates **AI recommendation** from **execution authorization**.

```text
AI Recommendation
      ↓
Policy Gate
      ↓
Execution Authorization
      ↓
Bounded Recovery Action
      ↓
Audit Trail

The execution layer does not blindly execute the AI recommendation.

Actions must satisfy deterministic policy constraints, and incompatible execution requests are blocked.

Recommendation ≠ Authorization

This ensures that AI can recommend an action without automatically gaining unrestricted execution authority.
```

---

## Tech Stack

- **Frontend:** React, Vite, JavaScript, CSS
- **Backend:** Python, FastAPI
- **Machine Learning:** Scikit-learn
- **AI Decisioning:** Recovery decision engine with policy-based governance
- **Payments:** Razorpay APIs / Razorpay Payment Links
- **Data & Evaluation:** Transaction dataset and recovery evaluation pipeline

---

## Project Structure

```text
RecoverAI/
├── backend/
│   ├── api.py
│   ├── execute_one_recovery.py
│   ├── payment_link.py
│   ├── razorpay_client.py
│   └── recovery_executor.py
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       ├── index.css
│       └── main.jsx
│
├── data/
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js and npm
- Razorpay test-mode credentials for Payment Link execution

### Installation

#### 1. Clone the repository

```bash
git clone https://github.com/keerthanam4/RecoverAI.git
cd RecoverAI
npm install
cd ..
```

### Environment Configuration

Configure Razorpay test-mode credentials as required by the application.

```env
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
```

### Running the Application

#### Start the backend

```bash
uvicorn backend.api:app --reload
```

#### Start the frontend

```bash
cd frontend
npm run dev
```

The frontend will be available through the Vite development server.

---

## Core Principle

> **AI decides. Policy governs. Execution is bounded.**

Every recovery action is designed to be **predictable, controlled, explainable, and auditable**.
