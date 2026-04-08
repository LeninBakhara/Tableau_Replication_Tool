import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import config

def send_invite_email(to_email: str, role: str, invite_token: str, invited_by: str):
    invite_url = f"http://localhost:{config.APP_PORT}/invite.html?token={invite_token}"
    role_label = role.capitalize()

    html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 520px; margin: 0 auto; background: #0f1117; color: #e2e8f0; border-radius: 12px; overflow: hidden;">
      <div style="background: #1a1d2e; padding: 32px; text-align: center; border-bottom: 1px solid #2d3748;">
        <h1 style="margin: 0; font-size: 22px; color: #f59e0b; letter-spacing: -0.5px;">Dashboard Cloning Tool</h1>
        <p style="margin: 8px 0 0; color: #94a3b8; font-size: 13px;">by Decision Tree</p>
      </div>
      <div style="padding: 36px 32px;">
        <p style="font-size: 16px; color: #e2e8f0; margin: 0 0 12px;">You've been invited!</p>
        <p style="font-size: 14px; color: #94a3b8; line-height: 1.6; margin: 0 0 24px;">
          <strong style="color:#f59e0b">{invited_by}</strong> has invited you to join the Dashboard Cloning Tool as a <strong style="color:#f59e0b">{role_label}</strong>.
        </p>
        <a href="{invite_url}" style="display: inline-block; background: #f59e0b; color: #0f1117; padding: 13px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; letter-spacing: 0.3px;">
          Accept Invite &amp; Set Password
        </a>
        <p style="font-size: 12px; color: #4a5568; margin: 24px 0 0;">
          This link expires in 48 hours. If you didn't expect this invite, you can ignore this email.
        </p>
      </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"You've been invited to Dashboard Cloning Tool as {role_label}"
    msg["From"] = f"{config.SMTP_FROM_NAME} <{config.SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send invite to {to_email}: {e}")
        return False
