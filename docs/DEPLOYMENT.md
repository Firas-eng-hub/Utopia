# Deploy UtopiaHire

The React frontend runs on Vercel. The FastAPI API runs as a Docker service on
Render alongside PostgreSQL and a persistent disk for resumes. The backend needs
OCR system packages and persistent uploaded files; the Vercel static deployment
alone does not run those services.

No live deployment URL is assigned by these files. Your hosting accounts must be
connected, the services created, and the public checks below passed first.

## 1. Create the backend

1. In Render, create a **Blueprint** from `Firas-eng-hub/Utopia`, branch `main`,
   using the root `render.yaml`.
2. Review the service, database, and disk prices before creating them. The
   blueprint uses a Starter service, a Basic PostgreSQL database, and a 1 GB
   persistent disk. These are paid resources; they are not created by a Git push.
3. Supply `GROQ_API_KEY` securely in Render. This enables AI resume analysis,
   interview feedback, compatibility checks, recommendations, and cover letters.
4. Set `BACKEND_CORS_ORIGINS` to the exact HTTPS frontend origin, without a path
   or trailing slash. If the Vercel project does not exist yet, create/import it
   first to learn its assigned domain, or update this value after step 2 below.
   Separate multiple explicitly trusted origins with commas.
5. Render supplies `DATABASE_URL` from the database and generates `SECRET_KEY`.
   `DEBUG=false` and persistent resume storage are configured in the blueprint.
6. Wait for deployment and verify `GET /ready` returns HTTP 200 and
   `{"status":"ready"}`. Record the backend's actual HTTPS URL.

The container initializes a **new, empty database** transactionally and records
the schema version. Restarting preserves data and does not run the destructive
legacy migrations. Existing databases without the deployment version table are
rejected rather than reset; migrate those separately after making a backup.
The managed database allows internal service access only.

The upload disk is mounted at `/var/data`; the server stores resumes under
`/var/data/resumes`. Keep the disk attached across deploys and configure provider
backups for both the database and uploaded files. Use one API instance with this
disk; multiple replicas require shared object storage.

For live job searches, configure at least one provider in Render:

| Variable | Provider |
| --- | --- |
| `SERPAPI_API_KEY` | SerpAPI Google Jobs |
| `LINKEDIN_RAPIDAPI_KEY` | LinkedIn job-search RapidAPI subscription |
| `JSEARCH_API_KEY` | JSearch RapidAPI subscription |

Optional `GITHUB_TOKEN` and `STACKOVERFLOW_KEY` support footprint API access/rate
limits. These belong on the backend, never in Vercel's `VITE_*` variables. Rotate
any provider keys previously committed to this repository; deleting a key from
current files does not remove it from Git history.

## 2. Deploy the frontend on Vercel

1. Import the existing GitHub repository `Firas-eng-hub/Utopia` into Vercel.
2. Keep **Root Directory** at the repository root. The root `vercel.json` installs
   from `frontend/package-lock.json`, builds the frontend, and serves
   `frontend/dist`. It includes SPA rewrites so refreshing `/login`, `/dashboard`,
   and other application routes works.
3. Set `VITE_API_BASE_URL` in Vercel to the backend's actual HTTPS URL followed by
   `/api/v1`. Example format: `https://YOUR-BACKEND-HOST/api/v1`.
4. Enable that variable for Production and any Preview environments you intend
   to use. The Vercel build rejects missing, insecure, or localhost API URLs.
5. Set Production Branch to `main` and deploy. Later pushes to `main` trigger
   Vercel deployments through its GitHub integration.
6. Add the assigned Vercel HTTPS origin to Render's `BACKEND_CORS_ORIGINS` and
   redeploy the backend. Preview deployments need their exact origins added too;
   do not allow every `*.vercel.app` origin.

Frontend environment values are embedded at build time. Redeploy the frontend
after changing `VITE_API_BASE_URL`. The backend must be publicly reachable over
HTTPS before browser login, uploads, and other API features can work.

## 3. Verify the public deployment

Run the smoke check from a Python environment with `httpx` installed:

```bash
python deploy/smoke.py \
  --api https://YOUR-BACKEND-HOST \
  --frontend https://YOUR-VERCEL-HOST
```

It registers a temporary user, logs in, checks protected APIs, starts an
interview, uploads/parses a sample PDF when the sample file is available, and
deletes the temporary account and resume. It verifies frontend routing and CORS.
It does not call paid AI/job-provider APIs. Complete one real AI interview answer,
one AI resume analysis, one live job search, and one footprint scan in the browser
to verify your keys and provider subscriptions. Do not call the application fully
functional until those operations pass with your hosting configuration.

Once verified, copy the **actual Vercel production URL** into the GitHub
repository's **About → Website** field. This provides the public application link
from GitHub. Do not use a local address or the backend URL as the application link.

## Local container validation

Build with `docker build -f deploy/Dockerfile -t utopiahire-api .` and run against
a new PostgreSQL database with `DATABASE_URL`, `SECRET_KEY`,
`BACKEND_CORS_ORIGINS`, a port mapping for port 8000, and a persistent mount at
`/var/data`. The container honors `PORT` when the host supplies it. Never pass
secrets in committed files or shell commands saved in Git history.
