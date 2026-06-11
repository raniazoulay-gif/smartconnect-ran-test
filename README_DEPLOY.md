# Deploy to Railway

## Initial Setup
1. Push code to GitHub
2. Create new Railway project -> Deploy from GitHub repo
3. Add PostgreSQL database in Railway dashboard
4. Set environment variables in Railway dashboard:
   - `DATABASE_URL` — set automatically by Railway PostgreSQL addon
   - `ADMIN_SECRET` — secret token for admin API (also set as GitHub Actions secret)
   - `SECRET_KEY` — random string for signed cookies (e.g. 32+ chars)
   - `AGENT_GILI_PASSWORD` — password for agent גילי
   - `AGENT_ELI_PASSWORD` — password for agent אלי
   - `AGENT_SHIREL_PASSWORD` — password for agent שיראל
   - `MANAGER_PASSWORD` — password for manager
5. Run migration once: in Railway shell -> `python migrate_to_postgres.py`

## Adding/Removing Stores
- Upload new Excel file via `/import` endpoint (or run import_data.py)
- Or directly edit via the admin interface

## Updating the App
```
git add .
git commit -m "update"
git push
```
Railway auto-deploys in ~2 minutes.
