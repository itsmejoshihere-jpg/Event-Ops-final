# AI Business Operations Platform — Hackathon Final

A full-stack Flask + SQLite business operations platform that brings all seven Track 1 areas into one connected workspace.

1. Customer support & service operations — AI ticket triage, category/priority detection, owner routing and status tracking.
2. Document & information processing — document capture, AI summaries and key-field detection.
3. Employee productivity — task ownership, deadlines, workload visibility and productivity signals.
4. Workflow automation — AI workflow generation, dependencies, reminders, risk detection and action logging.
5. Sales & business operations — lead/opportunity pipeline, values, probabilities, next actions and follow-ups.
6. Data analysis & decision support — KPIs, cross-functional metrics and AI-generated business insights.
7. Internal enterprise tools — internal requests, approvals, owners, priorities and deadlines.

## Local run

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

### Demo login
- Email: `demo@eventops.ai`
- Password: `demo123`

## GitHub + Vercel deployment

This folder is prepared for Vercel's Python runtime.

1. Create a GitHub repository.
2. Upload all files and folders in this project root to the repository. Do not upload only the ZIP.
3. In Vercel, import that GitHub repository.
4. Vercel will use the included `vercel.json` and `api/index.py`.
5. Deploy and open the generated Vercel URL.

### Database note
The zero-setup demo database uses SQLite. On Vercel, it is placed in `/tmp`, which is temporary serverless storage. This is suitable for a hackathon demo and seeded demo account, but production teams should connect PostgreSQL/Neon for persistent multi-user data.

## AI

The app works without an external AI key using its built-in workflow, triage, document, risk and decision-support engine. The architecture can be extended with an external LLM through environment variables.
