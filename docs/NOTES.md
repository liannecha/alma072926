# Coding Agent Usage Notes

This project was built with substantial coding-agent assistance. I used the agent as a pair programmer for scaffolding, implementation, documentation, and verification, while keeping the product interpretation and final review decisions human-owned.

## Agent-Assisted Areas

- Repository structure: the agent helped organize the project as a small monorepo with `apps/api`, `apps/web`, `docs`, and `storage`.
- Backend implementation: the agent assisted with the FastAPI app setup, lead routes, SQLAlchemy model, Pydantic schemas, SQLite configuration, bearer-token auth, resume upload storage, and local console email service.
- Frontend implementation: the agent assisted with the Next.js public intake form, internal dashboard, API client, status badges, token entry flow, and lead status update interaction.
- Styling and UX copy: the agent assisted with the visual styling, layout, form states, dashboard states, and user-facing copy.
- Tests: the agent assisted with pytest coverage for lead creation, upload validation, auth enforcement, authenticated listing, and marking a lead as reached out.
- Documentation: the agent assisted with the root README, API README, frontend README, design document, and this attribution note.

## Human-Written / Human-Directed Areas

- I interpreted the assignment requirements and chose the core workflow: a public lead intake form, an authenticated internal dashboard, and a manual `PENDING` to `REACHED_OUT` status transition.
- I made the product decision that automatic confirmation or notification emails should not count as outreach. The status changes only after a user explicitly marks the lead reached out.
- I reviewed the generated implementation, ran the app locally, exercised the API, and decided which tradeoffs were acceptable for a take-home project.
- I selected local-only implementations for SQLite, filesystem resume storage, console email, and bearer-token auth so reviewers can run the app without external services.

## Agent Output I Corrected

One subtle issue I watched for was the difference between an automatic email notification and actual manual outreach. The agent initially leaned toward treating lead creation and notification as the main workflow completion point. I clarified that the lead should remain `PENDING` after submission and that only an internal user action should transition it to `REACHED_OUT`. I verified this in the backend status endpoint, the dashboard button behavior, and the tests that assert new leads start as `PENDING` before being manually updated.

## Prompt / Session Log Summary

Representative agent prompts included:

- Ask the agent to scaffold a FastAPI backend for lead creation, retrieval, and status update.
- Ask the agent to add resume upload validation and local file storage.
- Ask the agent to create local console email notifications without requiring third-party credentials.
- Ask the agent to build a Next.js intake page and authenticated admin dashboard.
- Ask the agent to add tests for the core workflow and document setup steps.
- Ask the agent to review the implementation against the take-home requirements and update docs accordingly.
