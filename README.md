# AROX — AI Development Assistant

AROX is a cloud-hosted AI coding assistant being built in the `KPMC-Ai` repository. Gemini is the default provider, configured for the Gemini API free tier where available. Claude and OpenAI remain optional providers and may incur separate API charges.

## Implemented in the initial scaffold

- FastAPI service with a public `/health` endpoint.
- Authenticated `POST /api/chat` endpoint using a bearer token (`AROX_ACCESS_TOKEN`).
- Gemini `generateContent` API adapter, plus optional Claude and OpenAI adapters.
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

3. Set `AROX_ACCESS_TOKEN` and `GEMINI_API_KEY` from `.env.example` in your shell or local environment. Never commit real API keys or tokens.
4. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Check `GET /health`. To call `POST /api/chat`, send `Authorization: Bearer <AROX_ACCESS_TOKEN>` and JSON such as `{"provider":"gemini","message":"Help me understand this function"}`.
6. Run tests with `pytest`.

## Gemini setup and cost controls

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/apikey) and store it as the server-side `GEMINI_API_KEY` environment variable. Do not put the key in frontend code or commit it to Git.

The default model is `gemini-3.8-flash`. Google’s free tier has eligibility, quota, and rate limits that can change; it is not an unlimited or guaranteed free service. Check [official Gemini API pricing and free-tier details](https://ai.google.dev/gemini-api/docs/pricing) and [usage limits](https://ai.google.dev/gemini-api/docs/rate-limits) before deployment. Do not link a paid billing account unless you explicitly choose to do so. Google states that data submitted on the free tier may be used to improve its products, so avoid sending secrets or sensitive user data.

Render's free hosting plan may also have availability or resource limits. Hosting costs and AI API usage are separate.

## Security and boundaries

- Never commit API keys, passwords, tokens, private keys, database URLs, or production data.
- The chat endpoint is disabled until `AROX_ACCESS_TOKEN` is configured and requires a valid bearer token afterward.
- Do not expose this token or any provider key in browser-side code or public frontend assets.
- Provider calls have a timeout; upstream error details and credentials are not returned to callers.
- GitHub repository inspection/editing, autonomous code execution, multi-agent orchestration, and deployment actions are **not implemented yet**. The current scaffold only provides a protected chat API.
- Keep Financial OS in its own repository and preserve its existing functionality. Do not copy its secrets or production data into KPMC-Ai.
- Require human review before repository writes, merges, deployments, or destructive actions.

## License

No license has been selected. Until a license is added, do not assume this project's code is licensed for reuse by others.
