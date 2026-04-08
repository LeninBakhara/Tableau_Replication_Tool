# Dashboard Cloning Tool

Internal tool by Decision Tree to clone Tableau dashboards for new clients automatically.

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/your-org/dashboard-cloning-tool.git
cd dashboard-cloning-tool
```

### 2. Set up credentials
```bash
cp .env.example .env
# Edit .env with your Redshift, Tableau, SMTP credentials
```

### 3. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Add your master template
Place your `.twbx` master template file into the `templates/` folder.

### 5. Run the app
```bash
cd backend
python main.py
```

Open http://localhost:8000 in your browser.

---

## Default Login
- **Email:** `lenin.bakhara@decision-tree.com`  
- **Password:** `Admin@1234` *(change this after first login)*

## Roles
| Role | Access |
|---|---|
| **Super Admin** | Everything — credentials, invite admins, full history |
| **Admin** | Templates, invite users, full history |
| **User** | Clone dashboards, own history only |

## Project Structure
```
dashboard-cloning-tool/
├── backend/
│   ├── main.py          # FastAPI app + all routes
│   ├── auth.py          # JWT auth
│   ├── database.py      # SQLite user management
│   ├── redshift.py      # Redshift connection
│   ├── twbx.py          # .twbx file patching
│   ├── email_service.py # Invite emails
│   ├── config.py        # Config loader
│   └── requirements.txt
├── frontend/
│   ├── login.html       # Login page
│   ├── invite.html      # Accept invite
│   ├── app.html         # Analyst tool
│   └── admin.html       # Admin panel
├── templates/           # Master .twbx files (gitignored)
├── outputs/             # Generated .twbx files (gitignored)
├── config/
│   └── dashboards.json  # Dashboard registry
├── database/            # SQLite DB (gitignored)
├── .env                 # Credentials (gitignored)
├── .env.example         # Template for others
└── README.md
```

## Security Notes
- `.env` is gitignored — never commit it
- `.twbx` files are gitignored
- Rotate your PAT secret and Redshift password after sharing this repo
- Change the default admin password after first login
