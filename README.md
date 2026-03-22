# AI Career Mentor Agent

Production-style full-stack scaffold for a memory-aware career mentor:
- **Frontend**: Next.js App Router + Tailwind (chat + dashboard)
- **Backend**: FastAPI + Agno agent layer + Hindsight memory adapter
- **Voice**: ElevenLabs TTS/STT adapter
- **Data/Auth**: Supabase REST + Supabase JWT verification (RLS-aware)

## Current Capabilities

- First-time onboarding prompt (optional/skippable) for profile setup
- Profile fields persisted in Supabase (`LinkedIn`, `GitHub`, resume metadata)
- Resume upload as **PDF** (text extraction stored as `resume_text` for memory/recommendation context)
- Hindsight memory retain/recall/reflect used in chat and recommendation flow
- Firecrawl-enriched job analysis (when configured) for role-fit and skill-gap hints on dashboard

## Folder Structure

- [apps/api](apps/api) — FastAPI backend and agent orchestration
- [apps/web](apps/web) — Next.js frontend UI and proxy routes
- [infra/supabase/migrations](infra/supabase/migrations) — SQL migrations
- [docs](docs) — architecture and deployment notes

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Supabase project (URL, anon key, service role key)

### 1) Backend

```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Set the following in `apps/api/.env`:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (required for scheduler/admin writes)
- `SUPABASE_JWT_AUDIENCE` (defaults to `authenticated`)

Optional service keys:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (defaults to `gpt-4.1-mini`)
- `OPENAI_BASE_URL` (set for OpenAI-compatible providers, e.g. Groq: `https://api.groq.com/openai/v1`)
- `HINDSIGHT_API_KEY`
- `HINDSIGHT_BANK_ID` (optional override if your existing Hindsight memories use a non-user-id bank, e.g. `adesh-profile`)
- `ELEVENLABS_API_KEY`
- `FIRECRAWL_API_KEY` (enables job-page scraping for expected-vs-missing skill analysis)
- `FIRECRAWL_BASE_URL` (defaults to `https://api.firecrawl.dev/v2`)

### 1.1) Supabase migrations

Run both SQL migrations in your Supabase project:

- [infra/supabase/migrations/001_init.sql](infra/supabase/migrations/001_init.sql)
- [infra/supabase/migrations/002_profile_onboarding.sql](infra/supabase/migrations/002_profile_onboarding.sql)

`002_profile_onboarding.sql` adds onboarding/profile columns including:
- `linkedin_url`, `github_url`
- `resume_text` (extracted from uploaded PDF)
- `resume_file_name`, `resume_uploaded_at`
- `onboarding_completed_at`

### 2) Frontend

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

Set the following in `apps/web/.env.local`:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `BACKEND_URL` (defaults to `http://localhost:8000`)

Open [http://localhost:3000](http://localhost:3000)

## Notes

- Resume PDF file binaries are not stored in DB by default; extracted text + metadata are stored in `user_profiles`.
- If `FIRECRAWL_API_KEY` is not set, recommendations fall back to title/profile-based matching without scrape enrichment.
- Do not commit real API keys in `.env.example` or source control; use placeholder values only.
