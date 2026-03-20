# Local Development

## Backend

- File: [apps/api/app/main.py](apps/api/app/main.py)
- Health endpoint: `GET /health`
- API prefix: `/api/v1`

## Frontend

- File: [apps/web/app/page.tsx](apps/web/app/page.tsx)
- Proxies:
  - [apps/web/app/api/chat/route.ts](apps/web/app/api/chat/route.ts)
  - [apps/web/app/api/dashboard/[userId]/route.ts](apps/web/app/api/dashboard/[userId]/route.ts)

## Environment

Copy examples:
- `apps/api/.env.example -> apps/api/.env`
- `apps/web/.env.example -> apps/web/.env.local`
