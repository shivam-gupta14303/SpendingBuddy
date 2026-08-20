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

- **Backend:** Flask, SQLite (via `sqlite3`)
- **Auth:** Werkzeug password hashing, Authlib for Google OAuth
- **Frontend:** Jinja2 templates, vanilla CSS/JS (no frontend framework)

## Setup

### 1. Clone and install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create the database

Run your database setup script once to create `spendingbuddy.db` and all required tables:

```bash
python database.py
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

**Note:** `.env` should never be committed to version control — add it to `.gitignore`.

### 4. Google OAuth setup

1. Go to [Google Cloud Console](https://console.cloud.google.com) and create a project.
2. Under **APIs & Services → OAuth consent screen**, configure an External app and add your own account as a test user.
3. Under **APIs & Services → Credentials**, create an **OAuth Client ID** (type: Web application).
4. Add the following to **Authorized redirect URIs**:
   - `http://localhost:5000/login/google/callback`
   - `http://127.0.0.1:5000/login/google/callback`
5. Add the following to **Authorized JavaScript origins**:
   - `http://localhost:5000`
   - `http://127.0.0.1:5000`
6. When deploying, add your production equivalents (`https://yourdomain.com/login/google/callback`, etc.) alongside the local ones.

### 5. Run the app

```bash
python app.py
```

Visit `http://localhost:5000` (or `http://127.0.0.1:5000`) in your browser.

## Project structure

```
SpendingBuddy/
├── app.py                  # Flask routes and application logic
├── database.py              # One-time database/table setup script
├── requirements.txt
├── .env                      # Google OAuth credentials (not committed)
├── spendingbuddy.db          # SQLite database (created after running database.py)
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
- `app.secret_key` is currently hardcoded in `app.py`; move this to an environment variable before deploying to production.
- The `income` table exists in the schema but isn't currently used — income is stored as a single editable value in the `settings` table instead.
- Phone number (OTP) login is planned but not yet implemented.

## License

Personal project — no license specified.