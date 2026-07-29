# Coding Agent Usage Notes

This project was built with substantial coding-agent assistance. I used GitHub Copilot Chat in VS Code as the primary coding agent for scaffolding, implementation, and verification, and used Codex/ChatGPT for follow-up guidance, documentation, and review. I kept the product interpretation and final review decisions human-owned.

## Agent-Assisted Areas

- Repository structure: GitHub Copilot Chat helped organize the project as a small monorepo with `apps/api`, `apps/web`, `docs`, and `storage`.
- Backend implementation: GitHub Copilot Chat assisted with the FastAPI app setup, lead routes, SQLAlchemy model, Pydantic schemas, SQLite configuration, bearer-token auth, resume upload storage, local console email service, authenticated resume downloads, and lead deletion workflow.
- Frontend implementation: GitHub Copilot Chat assisted with the Next.js public intake form, internal dashboard, API client, status badges, token entry flow, lead status update interaction, resume download action, and delete action.
- Styling and UX copy: GitHub Copilot Chat assisted with the visual styling, layout, form states, dashboard states, and user-facing copy.
- Tests: GitHub Copilot Chat assisted with pytest coverage for lead creation, upload validation, auth enforcement, authenticated listing, marking a lead as reached out, authenticated resume downloads, and deleting leads.
- Documentation: GitHub Copilot Chat and Codex/ChatGPT assisted with the root README, API README, frontend README, design document, and this attribution note.

## Human-Written / Human-Directed Areas

- I interpreted the assignment requirements and chose the core workflow: a public lead intake form, an authenticated internal dashboard, and a manual `PENDING` to `REACHED_OUT` status transition.
- I made the product decision that automatic confirmation or notification emails should not count as outreach. The status changes only after a user explicitly marks the lead reached out.
- I reviewed the generated implementation, ran the app locally, exercised the API, and decided which tradeoffs were acceptable for a take-home project.
- I selected local-only implementations for SQLite, filesystem resume storage, console email, and bearer-token auth so reviewers can run the app without external services.

## Agent Output I Corrected

One subtle issue I watched for was the difference between an automatic email notification and actual manual outreach. The coding agent initially leaned toward treating lead creation and notification as the main workflow completion point. I clarified that the lead should remain `PENDING` after submission and that only an internal user action should transition it to `REACHED_OUT`. I verified this in the backend status endpoint, the dashboard button behavior, and the tests that assert new leads start as `PENDING` before being manually updated.

## Prompt / Session Log Summary

Representative agent prompts included:

- Ask GitHub Copilot Chat to scaffold a FastAPI backend for lead creation, retrieval, and status update.
- Ask GitHub Copilot Chat to add resume upload validation and local file storage.
- Ask GitHub Copilot Chat to create local console email notifications without requiring third-party credentials.
- Ask GitHub Copilot Chat to build a Next.js intake page and authenticated admin dashboard.
- Ask GitHub Copilot Chat to add authenticated resume downloads and a lead deletion action.
- Ask GitHub Copilot Chat to add tests for the core workflow and document setup steps.
- Ask Codex/ChatGPT to review and refine the AI usage notes so the attribution accurately distinguishes Copilot from Codex/ChatGPT.
