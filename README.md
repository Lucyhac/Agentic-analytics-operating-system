# InsightForge AI Analytics

A production-minded AI-powered conversational data analytics platform. This first milestone includes a clean monorepo, a FastAPI backend for CSV/Excel ingestion and profiling, and a modern React upload experience ready for dashboard and chatbot expansion.

## Architecture

```text
frontend/          React, Tailwind, Framer Motion, Recharts-ready UI
backend/           FastAPI API, Pandas profiling, modular services
backend/api/       HTTP routes
backend/services/  Data processing and business logic
backend/ai/        Future LLM orchestration layer
backend/database/  SQLite now, PostgreSQL-ready later
backend/uploads/   Temporary uploaded datasets
```

## Why This Stack

- **React + Tailwind + Framer Motion**: fast, reusable SaaS UI with polished interactions.
- **FastAPI**: async-friendly Python API with automatic OpenAPI docs and strong validation.
- **Pandas + NumPy**: industry-standard tabular analysis toolkit.
- **SQLite first**: simple local persistence with a clean path to PostgreSQL.
- **OpenAI/Claude-ready AI layer**: chatbot execution will route through safe, structured operations rather than raw Python execution.

## Current Milestone

- Upload CSV, XLS, and XLSX files.
- Validate file extension and size.
- Persist uploads temporarily.
- Detect numeric, categorical, date, and boolean columns.
- Calculate shape, missing values, duplicates, statistics, top categories, date ranges, correlations, KPI candidates, and chart recommendations.
- Render a polished upload page with profile preview and next-step dashboard cards.
- Run an autonomous data-agent workflow with LangGraph.
- Classify natural-language commands into cleaning, modification, analytics, visualization, forecasting, insights, or unknown.
- Convert commands into structured safe actions instead of raw Python execution.
- Execute whitelisted Pandas tools for cleaning, transformations, analysis, chart creation, and insight generation.
- Refresh the dataset profile and dashboard state after mutating actions.

## Agent Architecture

The backend agent follows a safe tool-calling pattern:

```text
User prompt
  -> classify_intent node
  -> plan_actions node
  -> execute_tools node
  -> summarize node
  -> refreshed profile + charts + insights
```

The AI agent never executes arbitrary code. It plans structured actions such as:

```json
{
  "action": "modify_column",
  "column": "revenue",
  "operation": "add",
  "value": 5
}
```

Then the backend validates the action and runs a whitelisted dataframe tool.

Current tools:

- `drop_missing`
- `fill_missing`
- `drop_duplicates`
- `rename_column`
- `modify_column`
- `filter_rows`
- `normalize_column`
- `remove_outliers`
- `calculate_metric`
- `groupby_metric`
- `correlation`
- `generate_chart`
- `generate_insights`

Example prompts:

- `Remove duplicate records`
- `Replace missing values with average revenue`
- `Add 5 to sales column`
- `Filter rows where profit > 1000`
- `Show top 10 city by revenue`
- `Create revenue by city bar chart`
- `Find correlations between columns`

## Local Setup

### Backend

```bash
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Use Python 3.12 for local development and Render deployment. Pandas wheels may not be available for newer experimental local interpreters.

For backend endpoint tests, install the dev extras:

```bash
pip install -r requirements-dev.txt
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Create `frontend/.env` from `frontend/.env.example` if your backend URL changes.

## API

- `GET /health` checks service health.
- `POST /api/datasets/upload` uploads and profiles a dataset.
- `POST /api/agent/invoke` runs the LangGraph data agent against the active dataset.

## Roadmap

1. Add LLM-backed structured planning with OpenAI or Claude while keeping the same safe action schema.
2. Add LangGraph checkpoint persistence for long-running conversation memory.
3. Add dataset transformation history, undo, and branchable analysis sessions.
4. Add forecasting tools with confidence intervals.
5. Export cleaned datasets, chart images, and PDF reports.
6. SQLite metadata persistence and PostgreSQL migration.
