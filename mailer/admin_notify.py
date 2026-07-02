import html
import os

import requests


def notify_admin_new_subscriber(email, zip_code, horoscope, status):
    admin_email = os.getenv("ADMIN_NOTIFY_EMAIL")
    resend_api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL")

    if not admin_email:
        print("ADMIN_NOTIFY_EMAIL not set; skipping admin notification")
        return

    if not resend_api_key or not from_email:
        print("Resend configuration missing; skipping admin notification")
        return

    safe_email = html.escape(email)
    safe_zip = html.escape(zip_code)
    safe_horoscope = html.escape(horoscope or "None")
    safe_status = html.escape(status)

    payload = {
        "from": from_email,
        "to": [admin_email],
        "subject": f"DailyPulseWatch subscriber: {email}",
        "html": f"""
        <h2>DailyPulseWatch Subscriber Notification</h2>
        <p><strong>Status:</strong> {safe_status}</p>
        <p><strong>Email:</strong> {safe_email}</p>
        <p><strong>ZIP code:</strong> {safe_zip}</p>
        <p><strong>Horoscope:</strong> {safe_horoscope}</p>
        """,
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        if response.ok:
            print(f"Admin subscriber notification sent to {admin_email}")
        else:
            print(
                "Admin subscriber notification failed: "
                f"{response.status_code} {response.text}"
            )

    except requests.RequestException as exc:
        print(f"Admin subscriber notification error: {exc}")