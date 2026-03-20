# Architecture

## Overview

- Next.js frontend calls internal API routes (`/app/api/*`).
- Next.js API routes proxy to FastAPI backend (`/api/v1/*`).
- FastAPI orchestrates:
  - Agno agent for reasoning
  - Hindsight for retain/recall/reflect long-term memory
  - Recommendation service (10 jobs/day)
  - Voice service (ElevenLabs TTS/STT)
   - Supabase REST repositories with JWT-based RLS enforcement

## Core Flows

1. **Chat Flow**
   - Frontend sends `{ user_id, message }` to Next.js proxy.
   - Backend retains memory, recalls context, reflects observations.
   - Agno agent generates actionable mentorship.
   - Recommendation service refreshes daily job list.

2. **Dashboard Flow**
   - Frontend fetches skills, projects, applications summary, and 10 recommendations.

3. **Daily Schedule Flow**
   - Backend scheduler computes recommendations for known users every day.

## Scalability Notes

- Move scheduler to dedicated worker process in production.
- Add Redis queue for background jobs and retries.
