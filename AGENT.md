# AGENTS.md

## Mission
Replace the original Streamlit frontend of `video-subtitle-app` with the new Stitch-style frontend, without changing the app’s core subtitle-generation functionality.

## Non-negotiables
- Preserve all original business capabilities.
- Do not ship a static frontend mock; wire the frontend to real backend APIs.
- Prefer reusing the existing Python subtitle/video pipeline instead of rewriting it.
- Keep the system locally runnable.
- Keep docs, env examples, and tests in sync with code changes.

## Preferred architecture
- Frontend: React + TypeScript + Vite
- Backend: FastAPI
- Clear separation of routes, services, schemas, config, and file/task management

## Required flows
- Upload video
- Choose model/options
- Submit subtitle job
- Poll job status
- Download SRT
- Download processed video if available
- Surface readable errors

## Deliverables
- Working frontend/backend integration
- Updated README
- `.env.example`
- `ARCHITECTURE.md`
- `SPEC.md`
- `TEST_PLAN.md`
- Basic backend tests
- Local run scripts

## Working style
- First audit the repository and propose a plan.
- Then implement the minimum runnable path.
- Then improve docs/tests/error handling.
- Do not claim completion for anything still mocked or stubbed.

## Output style
For each substantial step:
1. What you are doing
2. What you found
3. Files to change
4. Code/diff
5. Current status, next step, risks