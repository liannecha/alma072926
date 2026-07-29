# System Design

## Goal

Build an application that lets public prospects submit lead information and lets authenticated internal users review leads and mark them as reached out.

## Initial Scope

- Public lead submission form
- Resume/CV upload
- Persistent lead storage
- Email notifications on submission
- Authenticated internal lead dashboard
- Manual transition from `PENDING` to `REACHED_OUT`

## Intentional Constraints

- Keep the system small enough to finish and verify within the take-home window.
- Prefer local-first dependencies for easy reviewer setup.
- Use abstractions for email and storage so production integrations are clear without requiring complex infrastructure locally.

## Lianne's Backend Notes to revise later
Make status an enum: Pending, Reached Out
Design choice: use an explicit enum instead of a free-form string.
Why: it prevents invalid states like "pending", "contacted", "done", etc. This also makes the state transition clear in the design doc.

I would not store the resume file itself in the database. Store metadata and a file path.
Design choice: local filesystem for resumes during the take-home.
Why: it is easy to run locally, easy for reviewers to inspect, and avoids cloud setup. In the design doc, say that production would likely use S3/GCS with signed URLs.