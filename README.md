# KPMC AI

KPMC AI is a chat-only workspace with a protected FastAPI backend and a React/Vite frontend. Each AI platform is presented as a separate tab; the API reports each integration's configured state and supported features.

## API scope

- Public `GET /health` endpoint.
- Authenticated `GET /api/providers` endpoint lists provider tabs, configuration state, and chat-only feature metadata without exposing credentials.
- Authenticated `POST /api/chat` endpoint supports provider selection.
- Provider adapters for FreeLLMAPI and OmniRoute OpenAI-compatible gateways.
- Optional direct Claude and OpenAI chat adapters.
- A separate, opt-in GodMode-compatible gateway slot. GodMode is a chat interface/project and is **not automatically an API gateway**; configure `GODMODE_BASE_URL` only when a compatible endpoint has been independently deployed and verified.
- Free-first routing in `auto` mode, with fallback to configured routes if an upstream fails.

## Environment configuration

Set these in the backend service environment. Never commit real API keys or tokens.

- `AROX_ACCESS_TOKEN`: required bearer token for protected API routes.
- `FREELLMAPI_BASE_URL`, `FREELLMAPI_API_KEY`, `FREELLMAPI_MODEL`
- `OMNIROUTE_BASE_URL`, `OMNIROUTE_API_KEY`, `OMNIROUTE_MODEL`
- `GODMODE_BASE_URL`, `GODMODE_API_KEY`, `GODMODE_MODEL` (optional; compatible endpoint required)
- `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (optional; usage may be paid)
- `OPENAI_API_KEY`, `OPENAI_MODEL` (optional; usage may be paid)

Copy `.env.example` for local development and replace placeholders locally. Do not put provider credentials in frontend code.

## Run locally

1. Use Python 3.12 or newer.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

3. Set environment variables from `.env.example` in your shell or local environment.
4. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Check `GET /health`. For protected routes, send `Authorization: Bearer <AROX_ACCESS_TOKEN>`.
6. Run tests with `pytest`.

## Deployment notes

The frontend can be hosted separately from the backend. Configure CORS for the exact deployed frontend origin. Do not embed a long-lived shared bearer token in public browser code; production use should add a user/session-based authentication layer.

## Security and boundaries

- Keep API keys, passwords, tokens, private keys, database URLs, and production data out of Git.
- Protected endpoints return no provider secrets.
- Free-tier availability, limits, and upstream terms vary by provider.
- This API is chat-only: no trading, financial analysis, autonomous agents, repository writes, or code execution are exposed.
- Keep Financial OS in its own repository and preserve its existing functionality. Do not copy its secrets or production data into KPMC AI.
- Require human review before repository writes, merges, deployments, or destructive actions.

## License

No license has been selected for KPMC AI. Until a license is added, do not assume this project's code is licensed for reuse by others.
