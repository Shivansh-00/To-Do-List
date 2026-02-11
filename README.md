TO-DO-LIST

This repository now includes a working starter backend for the AI Productivity OS vision.

## What is implemented
- FastAPI service with versioned endpoints.
- Task CRUD with nested subtasks support (`parent_task_id`).
- AI endpoints for task breakdown and effort estimation (heuristic placeholders).
- Behavioral insights endpoint (procrastination + burnout proxy metrics).
- Scheduling endpoint with explainable block generation.
- WebSocket endpoint for real-time task events.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Key endpoints
- `GET /health`
- `GET /v1/tasks`
- `POST /v1/tasks`
- `PATCH /v1/tasks/{task_id}`
- `DELETE /v1/tasks/{task_id}`
- `POST /v1/tasks/{task_id}/ai-breakdown`
- `POST /v1/tasks/{task_id}/estimate`
- `GET /v1/insights/behavior`
- `POST /v1/schedule/optimize`
- `WS /v1/realtime`

## Next steps
- Replace heuristic AI service with model serving layer (ONNX/Triton).
- Add PostgreSQL + Redis persistence.
- Add JWT auth, RBAC, and multi-tenant isolation.
- Add CI/CD + deployment manifests.
