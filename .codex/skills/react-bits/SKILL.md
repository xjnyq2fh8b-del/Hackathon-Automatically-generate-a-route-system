---
name: react-bits
description: Use the project-local React Bits reference when improving the route planning Agent frontend with animated React UI, route cards, timeline interactions, transition feedback, and polished but purposeful interface motion.
---

# React Bits

Use this skill when the user asks for frontend UI, interaction polish, animation, visual components, or prototype improvements for this route planning Agent.

## Source

- Local reference repo: `react-bits/`
- Project usage note: `docs/react-bits-skill.md`
- Upstream repo: `https://github.com/DavidHDev/react-bits`

## Product Boundary

Only use React Bits to improve route planning usability:

- route timelines
- POI step cards
- route comparison panels
- constraint controls
- loading or replanning feedback
- map/path-adjacent motion

Do not use it to create decorative UI that does not improve route quality, explainability, or executability.

## Workflow

1. Inspect the current `frontend/` structure before changing code.
2. Check `react-bits/src/` for a relevant component or pattern.
3. Adapt the idea into route-planning-specific component names and copy only the code needed.
4. Keep dependencies minimal; do not introduce broad frontend architecture changes unless the user has approved the plan.
5. Verify the local frontend after changes.

## Naming

Prefer business names such as:

- `RouteTimeline`
- `PoiStepCard`
- `ConstraintPanel`
- `ReplanStatus`
- `RouteOptionCompare`

Avoid generic showcase names when code is migrated into this project.
