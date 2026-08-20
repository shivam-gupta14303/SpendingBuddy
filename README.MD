# SpendingBuddy

A personal expense-tracking web app built with Flask. Track income, expenses, and recurring bills from a single dashboard, with a spending breakdown chart, overdue-bill alerts, and a responsive mobile layout.

## Features

- **Dashboard overview** — current balance, income, and total expenses at a glance
- **Editable income** — update your income directly from the dashboard, balance recalculates automatically
- **Expense tracking** — add, view, and delete expenses with category, type, priority, and notes
- **Bills** — add bills, mark them paid (automatically logs a matching expense), or delete them
- **Overdue bill alerts** — a banner appears on the dashboard once a bill's due date has passed and it's still unpaid
- **Reports** — spending totals for today, this month, all-time, and a custom date range, plus a category breakdown
- **Spending breakdown chart** — a CSS-based donut chart with a category legend
- **User accounts** — register/login with username + password, or sign in with Google (OAuth)
- **Mobile responsive** — collapsible sidebar with swipe gestures, stacked card layout for tables, and full-width auth screens on narrow devices

## Tech stack

- **Backend:** Flask, PostgreSQL (via `psycopg2`)
- **Auth:** Werkzeug password hashing, Authlib for Google OAuth
- **Frontend:** Jinja2 templates, vanilla CSS/JS (no frontend framework)
- **Deployment:** Render (Web Service + managed PostgreSQL)
- **Production server:** Gunicorn

## Local setup

### 1. Install dependencies

```bash
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
```

### 2. Set up PostgreSQL locally

Create a database (e.g. named `SpendingBuddy`) using pgAdmin or the `psql` CLI.

### 3. Configure environment variables

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/SpendingBuddy
FLASK_SECRET_KEY=your-generated-secret-key
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

Generate `FLASK_SECRET_KEY` with:
```python
import secrets
print(secrets.token_hex(32))
```

**`.env` should never be committed** — it's already covered in `.gitignore`.

### 4. Google OAuth setup

1. Go to [Google Cloud Console](https://console.cloud.google.com) and create a project.
2. Under **APIs & Services → OAuth consent screen**, configure an External app and add your account as a test user.
3. Under **APIs & Services → Credentials**, create an **OAuth Client ID** (type: Web application).
4. Add to **Authorized redirect URIs**:
   - `http://localhost:5000/login/google/callback`
   - `http://127.0.0.1:5000/login/google/callback`
5. Add to **Authorized JavaScript origins**:
   - `http://localhost:5000`
   - `http://127.0.0.1:5000`
6. Add your production Render URL equivalents once deployed (see below).

### 5. Create the database tables

```bash
python database.py
```

This creates all required tables (`users`, `income`, `expenses`, `bills`, `budget`, `settings`) in PostgreSQL.

### 6. Run the app

```bash
python app.py
```

Visit `http://localhost:5000` (or `http://127.0.0.1:5000`) in your browser.

## Deployment (Render)

1. **Create a PostgreSQL database** on Render (New → PostgreSQL). Copy the **Internal Database URL** for use by the deployed app, and the **External Database URL** for running `database.py` from your local machine against it.
2. **Create the tables on Render's database**: temporarily point your local `.env`'s `DATABASE_URL` at the External Database URL, run `python database.py` once, then switch `.env` back to your local database for continued local development.
3. **Create a Web Service** on Render, connected to this GitHub repo.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. **Set environment variables** in the Web Service's Environment tab (not `.env` — Render doesn't read that file):
   - `DATABASE_URL` → the **Internal** Database URL
   - `FLASK_SECRET_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
5. **Update Google Cloud Console** with your live Render URL:
   - Authorized redirect URI: `https://your-app-name.onrender.com/login/google/callback`
   - Authorized JavaScript origin: `https://your-app-name.onrender.com`

   (No code changes needed here — the app builds its redirect URI dynamically via `url_for(..., _external=True)`.)

## Project structure

```
SpendingBuddy/
├── app.py                  # Flask routes and application logic
├── database.py              # One-time PostgreSQL table setup script
├── requirements.txt
├── .env                      # Local secrets (not committed)
├── .gitignore
├── static/
│   ├── style.css              # Dashboard styling
│   ├── pages.css              # Styling for add-expense, bills, expenses, reports
│   ├── auth.css                # Login/register/account page styling
│   └── account_logo.png
└── templates/
    ├── home.html
    ├── add_expense.html
    ├── expenses.html
    ├── add_bill.html
    ├── bills.html
    ├── reports.html
    ├── login.html
    ├── register.html
    └── account.html
```

## Known limitations / things to revisit

- Google-authenticated users have a `NULL` password — password login won't work for accounts created via Google unless a password is set separately.
- The `income` table exists in the schema but isn't currently used — income is stored as a single editable value in the `settings` table instead.
- Render's free-tier PostgreSQL databases expire after 90 days unless upgraded to a paid plan.
- Render's free-tier Web Services spin down after inactivity, so the first request after idling may be slow to respond.
- Phone number (OTP) login is planned but not yet implemented.

## License

Personal project — no license specified.