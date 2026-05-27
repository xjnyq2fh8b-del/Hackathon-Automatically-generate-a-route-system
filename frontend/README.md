# Frontend Workspace Rules

This folder contains the web demo for the AI local route planning Agent.

## Structure

- `index.html`: single-page desktop web demo entry.
- `src/styles.css`: visual system and responsive layout.
- `src/app.js`: state, mock service layer, route planning, replanning, and UI rendering.
- `server.mjs`: tiny local static server for previewing the demo.
- `package.json`: local scripts only; no secrets or runtime API keys.

## Product Boundaries

- The first version is a desktop-first web decision workspace for the Hangzhou West Lake immediate route planning scenario.
- The UI must center on route generation and route adjustment, not a marketing landing page or a generic travel guide.
- Mock data must be described as estimated labels or demo data, especially waiting risk, ambience, photo quality, and crowd level.
- AMap and LLM integration should replace service-layer functions later, without changing the user-facing flow.

## Cleanup Rules

- Keep generated build artifacts, screenshots, and throwaway exports out of this folder unless they are explicitly needed for delivery.
- Do not commit API keys, tokens, `.env` values, or private credentials.
- Keep demo data small and scenario-specific; avoid growing this into a generic city database.
