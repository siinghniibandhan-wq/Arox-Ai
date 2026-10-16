# AROX — AI Development Assistant

AROX is a cloud-hosted AI coding assistant being built in the `KPMC-Ai` repository. It is designed to use Claude as the default model and OpenAI as an optional second provider, with both API keys stored only in the deployment environment.

## Implemented in the initial scaffold

- FastAPI service with a public `/health` endpoint.
- Authenticated `POST /api/chat` endpoint using a bearer token (`AROX_ACCESS_TOKEN`).
- Claude Messages API and OpenAI Chat Completions API adapters.
- Provider/model configuration through environment variables.
- Render Blueprint configuration in `render.yaml`.
- Starter tests for health and chat access control.

## Run locally

1. Use Python 3.12 or newer.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

3. Set environment variables from `.env.example` in your shell or local environment. Never commit real API keys or tokens.
4. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Check `GET /health`. To call `POST /api/chat`, send `Authorization: Bearer <AROX_ACCESS_TOKEN>` and JSON such as `{"provider":"claude","message":"Help me understand this function"}`.
6. Run tests with `pytest`.

## Render deployment

Connect this repository to Render and deploy using the `render.yaml` Blueprint. Render generates `AROX_ACCESS_TOKEN`; add valid provider keys in the service's Environment settings. API usage is billed separately by each model provider. Review the current model IDs and provider billing before production use.

## Security and boundaries

- Never commit API keys, passwords, tokens, private keys, database URLs, or production data.
- The chat endpoint is disabled until `AROX_ACCESS_TOKEN` is configured and requires a valid bearer token afterward.
- Do not expose this token in browser-side code or public frontend assets.
- Provider calls have a timeout; upstream error details and credentials are not returned to callers.
- GitHub repository inspection/editing, autonomous code execution, multi-agent orchestration, and deployment actions are **not implemented yet**. The current scaffold only provides a protected chat API.
- Keep Financial OS in its own repository and preserve its existing functionality. Do not copy its secrets or production data into KPMC-Ai.
- Require human review before repository writes, merges, deployments, or destructive actions.

## License

No license has been selected. Until a license is added, do not assume this project's code is licensed for reuse by others.
