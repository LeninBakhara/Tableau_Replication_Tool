import os, json, shutil
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from config import config
from database import (
    init_db, get_user_by_email, get_all_users, create_user, update_user_role,
    remove_user, update_last_login, verify_password, create_invite,
    get_invite_by_token, mark_invite_used, get_all_invites, log_clone,
    get_history, update_credentials
)
from auth import create_token, get_current_user, require_admin, require_superadmin, generate_invite_token, invite_expires_at
from email_service import send_invite_email
from redshift import test_connection, get_table_columns, table_exists
from twbx import patch_twbx, extract_datasource_info

# ── App setup ────────────────────────────────────────────
app = FastAPI(title="Dashboard Cloning Tool", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')
TEMPLATES_DIR = config.get_templates_dir()
OUTPUTS_DIR = config.get_outputs_dir()
CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'config')
DASHBOARDS_JSON = os.path.join(CONFIG_DIR, 'dashboards.json')

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.on_event("startup")
def startup():
    init_db()
    # Copy uploaded twbx to templates dir if not already there
    src = "/mnt/user-data/uploads/Blue_Bottle_Coffee-_Executive_Summary.twbx"
    dst = os.path.join(TEMPLATES_DIR, "Blue_Bottle_Coffee-_Executive_Summary.twbx")
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy(src, dst)
        print("[STARTUP] Copied template .twbx to templates/")

# ── Frontend routes ───────────────────────────────────────
@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/login.html")
def login_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/app.html")
def app_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.html"))

@app.get("/admin.html")
def admin_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))

@app.get("/invite.html")
def invite_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "invite.html"))

# ── Auth ─────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user["status"] != "active":
        raise HTTPException(status_code=403, detail="Account is inactive")
    update_last_login(req.email)
    token = create_token(req.email, user["role"])
    return {"token": token, "user": {"email": user["email"], "name": user["name"], "role": user["role"]}}

@app.get("/api/auth/me")
def me(user=Depends(get_current_user)):
    return {"email": user["email"], "name": user["name"], "role": user["role"]}

# ── Invites ───────────────────────────────────────────────
class InviteRequest(BaseModel):
    email: str
    role: str  # 'user' or 'admin'

@app.post("/api/admin/invite")
def invite_user(req: InviteRequest, user=Depends(get_current_user)):
    require_admin(user)
    # Only superadmin can invite admins
    if req.role == "admin" and user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Only super admin can invite admins")
    if req.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    existing = get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    token = generate_invite_token()
    expires = invite_expires_at()
    create_invite(req.email, req.role, token, user["email"], expires)
    email_sent = send_invite_email(req.email, req.role, token, user["email"])
    return {"success": True, "email_sent": email_sent, "invite_token": token}

class AcceptInviteRequest(BaseModel):
    token: str
    name: str
    password: str

@app.post("/api/auth/accept-invite")
def accept_invite(req: AcceptInviteRequest):
    invite = get_invite_by_token(req.token)
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or expired invite link")
    if datetime.fromisoformat(invite["expires_at"]) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite link has expired")
    existing = get_user_by_email(invite["email"])
    if existing:
        raise HTTPException(status_code=400, detail="Account already exists")
    create_user(invite["email"], req.password, req.name, invite["role"])
    mark_invite_used(req.token)
    user = get_user_by_email(invite["email"])
    token = create_token(invite["email"], invite["role"])
    return {"token": token, "user": {"email": user["email"], "name": user["name"], "role": user["role"]}}

@app.get("/api/auth/invite-info")
def invite_info(token: str):
    invite = get_invite_by_token(token)
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or expired invite")
    if datetime.fromisoformat(invite["expires_at"]) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite link has expired")
    return {"email": invite["email"], "role": invite["role"]}

# ── Users (Admin) ─────────────────────────────────────────
@app.get("/api/admin/users")
def list_users(user=Depends(get_current_user)):
    require_admin(user)
    users = get_all_users()
    invites = get_all_invites()
    # Mark pending invites as users too
    active_emails = {u["email"] for u in users}
    pending = [i for i in invites if i["email"] not in active_emails and not i["used"]]
    return {"users": users, "pending_invites": pending}

class UpdateRoleRequest(BaseModel):
    email: str
    role: str

@app.put("/api/admin/users/role")
def change_role(req: UpdateRoleRequest, user=Depends(get_current_user)):
    require_superadmin(user)
    if req.email == config.SUPER_ADMIN_EMAIL:
        raise HTTPException(status_code=400, detail="Cannot change super admin role")
    if req.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    update_user_role(req.email, req.role)
    return {"success": True}

@app.delete("/api/admin/users/{email}")
def delete_user(email: str, user=Depends(get_current_user)):
    require_admin(user)
    if email == config.SUPER_ADMIN_EMAIL:
        raise HTTPException(status_code=400, detail="Cannot remove super admin")
    remove_user(email)
    return {"success": True}

# ── Dashboards ────────────────────────────────────────────
def load_dashboards():
    with open(DASHBOARDS_JSON) as f:
        return json.load(f)["dashboards"]

def save_dashboards(dashboards):
    with open(DASHBOARDS_JSON, 'w') as f:
        json.dump({"dashboards": dashboards}, f, indent=2)

@app.get("/api/dashboards")
def list_dashboards(user=Depends(get_current_user)):
    return load_dashboards()

@app.post("/api/admin/dashboards/upload")
async def upload_dashboard(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    require_admin(user)
    if not file.filename.endswith('.twbx'):
        raise HTTPException(status_code=400, detail="Only .twbx files are accepted")
    dest = os.path.join(TEMPLATES_DIR, file.filename)
    content = await file.read()
    with open(dest, 'wb') as f:
        f.write(content)

    # Auto-extract datasource info
    try:
        ds_info = extract_datasource_info(dest)
    except Exception:
        ds_info = []

    # Register in dashboards.json
    dashboards = load_dashboards()
    safe_id = file.filename.replace('.twbx', '').replace(' ', '_').lower()
    dashboards.append({
        "id": safe_id,
        "name": file.filename.replace('.twbx', '').replace('_', ' '),
        "description": "",
        "template_file": file.filename,
        "created_at": datetime.now().strftime('%Y-%m-%d'),
        "datasources": ds_info
    })
    save_dashboards(dashboards)
    return {"success": True, "id": safe_id, "datasources": ds_info}

@app.delete("/api/admin/dashboards/{dashboard_id}")
def delete_dashboard(dashboard_id: str, user=Depends(get_current_user)):
    require_admin(user)
    dashboards = load_dashboards()
    db = next((d for d in dashboards if d["id"] == dashboard_id), None)
    if not db:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    # Remove file
    fpath = os.path.join(TEMPLATES_DIR, db["template_file"])
    if os.path.exists(fpath):
        os.remove(fpath)
    dashboards = [d for d in dashboards if d["id"] != dashboard_id]
    save_dashboards(dashboards)
    return {"success": True}

# ── Redshift ───────────────────────────────────────────────
@app.get("/api/redshift/test")
def test_redshift(user=Depends(get_current_user)):
    return test_connection()

@app.get("/api/redshift/columns")
def get_columns(table: str, schema: str = None, user=Depends(get_current_user)):
    if not table_exists(table, schema):
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found in schema '{schema or config.REDSHIFT_SCHEMA}'")
    return get_table_columns(table, schema)

# ── Clone Pipeline ─────────────────────────────────────────
class CloneRequest(BaseModel):
    dashboard_id: str
    client_name: str
    datasource_table_mapping: dict  # { "datasource_caption": "new_table_name" }
    new_schema: Optional[str] = None

@app.post("/api/clone")
def clone_dashboard(req: CloneRequest, user=Depends(get_current_user)):
    dashboards = load_dashboards()
    db = next((d for d in dashboards if d["id"] == req.dashboard_id), None)
    if not db:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    template_path = os.path.join(TEMPLATES_DIR, db["template_file"])
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template file not found on disk")

    new_schema = req.new_schema or config.REDSHIFT_SCHEMA
    ds_mappings = []

    for ds in db.get("datasources", []):
        caption = ds["caption"]
        new_table = req.datasource_table_mapping.get(caption)
        if not new_table:
            continue

        # Get client table columns
        try:
            client_cols = get_table_columns(new_table, new_schema)
            client_col_names = {c["name"] for c in client_cols}
        except Exception as e:
            log_clone(user["email"], req.client_name, db["name"], str(req.datasource_table_mapping), None, "error", str(e))
            raise HTTPException(status_code=400, detail=f"Could not read table '{new_table}': {str(e)}")

        # Build column mapping: old template col -> new client col
        col_mapping = {}
        for orig_col in ds.get("columns", []):
            if orig_col in client_col_names:
                col_mapping[orig_col] = orig_col  # same name, no change needed
            # else: column missing in new table, leave as-is (will show NULL or error)

        ds_mappings.append({
            "datasource_caption": caption,
            "old_table": ds["table"],
            "new_table": new_table,
            "old_schema": ds["schema"],
            "new_schema": new_schema,
            "column_mapping": col_mapping
        })

    # Patch the twbx
    result = patch_twbx(template_path, req.client_name, ds_mappings, OUTPUTS_DIR)

    if result["success"]:
        log_clone(user["email"], req.client_name, db["name"], json.dumps(req.datasource_table_mapping), result["output_file"])
        return {"success": True, "output_file": result["output_file"]}
    else:
        log_clone(user["email"], req.client_name, db["name"], json.dumps(req.datasource_table_mapping), None, "error", result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

@app.get("/api/download/{filename}")
def download_file(filename: str, user=Depends(get_current_user)):
    filepath = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.exists(filepath) or not filename.endswith('.twbx'):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type="application/octet-stream", filename=filename)

# ── History ────────────────────────────────────────────────
@app.get("/api/history")
def history(user=Depends(get_current_user)):
    return get_history(user["email"], user["role"])

# ── Credentials (Admin) ────────────────────────────────────
class CredentialsUpdate(BaseModel):
    section: str  # 'redshift' or 'tableau'
    values: dict

@app.put("/api/admin/credentials")
def update_creds(req: CredentialsUpdate, user=Depends(get_current_user)):
    require_superadmin(user)
    allowed_redshift = {"REDSHIFT_HOST", "REDSHIFT_PORT", "REDSHIFT_DB", "REDSHIFT_USER", "REDSHIFT_PASSWORD", "REDSHIFT_SCHEMA"}
    allowed_tableau = {"TABLEAU_URL", "TABLEAU_PAT_NAME", "TABLEAU_PAT_SECRET", "TABLEAU_SITE"}
    allowed = allowed_redshift if req.section == "redshift" else allowed_tableau
    safe = {k: v for k, v in req.values.items() if k in allowed}
    if not safe:
        raise HTTPException(status_code=400, detail="No valid keys to update")
    update_credentials(req.section, safe)
    return {"success": True}

@app.get("/api/admin/credentials")
def get_creds(user=Depends(get_current_user)):
    require_superadmin(user)
    return {
        "redshift": {
            "REDSHIFT_HOST": config.REDSHIFT_HOST,
            "REDSHIFT_PORT": config.REDSHIFT_PORT,
            "REDSHIFT_DB": config.REDSHIFT_DB,
            "REDSHIFT_USER": config.REDSHIFT_USER,
            "REDSHIFT_PASSWORD": "••••••••",
            "REDSHIFT_SCHEMA": config.REDSHIFT_SCHEMA
        },
        "tableau": {
            "TABLEAU_URL": config.TABLEAU_URL,
            "TABLEAU_PAT_NAME": config.TABLEAU_PAT_NAME,
            "TABLEAU_PAT_SECRET": "••••••••",
            "TABLEAU_SITE": config.TABLEAU_SITE
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.APP_HOST, port=config.APP_PORT, reload=True)
