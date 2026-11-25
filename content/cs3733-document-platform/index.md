---
title: Document Management Platform (CS3733)
short_title: CS3733 document platform
summary: A full-stack document platform for The Hanover Insurance Group, built by a 10-person team that I led. I
  built the semantic search, the ML embedding service and the deployment.
icon: 📄
highlights:
- Led a 10-person Agile team
- pgvector semantic search + local ML service
- Docker images and AWS deployment
status: live
area: software
rank: 1
started: 2026-03
ended: 2026-05
role: Team lead (10 people, Agile); full-stack developer
stack:
- React
- TypeScript
- Express 5
- Prisma
- PostgreSQL + pgvector
- Python ML service
- Auth0
- Docker
- AWS
focus:
- fullstack
tags:
- TypeScript
- React
- PostgreSQL
- Python
- Docker
- AWS
- Semantic search
- Team lead
links:
- label: Live site
  url: https://cs3733.stomberg.us/
- label: Repository
  url: https://github.com/CS3733-TeamB-2026/teamB-protoype
timeline:
- date: 2026-03
  text: Team formed; requirements gathered from the client. I take the team lead role.
- date: 2026-04
  text: Data layer and API structure set. Shared database package split from the Express backend.
- date: 2026-04
  text: Semantic search across four entity types using pgvector embeddings of text, metadata and OCR output.
- date: 2026-05
  text: Docker images and AWS deployment on a custom domain; final presentation to the client.
---
CS3733 is WPI's software engineering course, run as a term-long team project for a real client. Our client was **The Hanover Insurance Group**. They wanted a platform to store, preview, search and request work on internal documents. I led the 10-person team and wrote a large share of the backend and infrastructure.

## My parts

- **Team lead.** Ran sprint planning and standups, split the work, and was the main contact for requirements.
- **Semantic search.** A global search across four kinds of records. File text, metadata and OCR output are embedded and stored in PostgreSQL with **pgvector**, and similarity queries for each entity type run in parallel. The embeddings come from a **Python ML service** that runs locally, so documents never go to a third-party API.
- **Data layer.** Wired up the **Prisma** ORM and split a shared `packages/db` package out of the Express app, so the API and scripts use one schema.
- **API structure.** Organized the REST routes and client calls so ten people could work on them without stepping on each other.
- **Previews and extraction.** Extended document previews to more file types; the same text-extraction path feeds both the preview and the search index.
- **Service requests.** The workflow for asking someone to act on a document.
- **Deployment.** Built the **Docker** images and deployed to **AWS** on a custom domain.

## Keeping ten people unblocked

Several of my backend tasks were really coordination work. One shared data package and a clear API layout meant ten people could build features in parallel without redefining the same models.
