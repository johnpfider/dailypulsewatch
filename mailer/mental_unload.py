import os
import requests


RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
REPLY_TO_EMAIL = os.getenv("REPLY_TO_EMAIL")


def send_mental_unload_email(email):
    html = """
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif; background:#F3F4F6; padding:20px;">

        <div style="
            max-width:640px;
            margin:auto;
            background:#FFFFFF;
            padding:28px;
            border-radius:18px;
            border:1px solid #E5E7EB;
            box-shadow:0 12px 28px rgba(0,0,0,0.12);
        ">

            <h2 style="margin-top:0;">The Healthcare Worker’s Mental Unload</h2>

            <p>
                Before the day gets louder, here’s a simple guided reflection exercise
                to help you clear some mental space.
            </p>

            <p>
                This is not therapy or counseling. It’s just a quiet reset for healthcare
                workers carrying a lot.
            </p>

            <hr style="border:none; border-top:1px solid #E5E7EB; margin:24px 0;">

            <h3>Take a few minutes and answer these honestly:</h3>

            <p><strong>1.</strong> What’s taking up the most space in your mind right now?</p>

            <p><strong>2.</strong> Of everything on that list, what can you actually influence today?</p>

            <p><strong>3.</strong> What’s something you’ve been spending energy on that you can’t really control right now?</p>

            <p><strong>4.</strong> What’s one thing that went right recently, even if it was small?</p>

            <p><strong>5.</strong> What’s the next helpful step you can take?</p>

            <hr style="border:none; border-top:1px solid #E5E7EB; margin:24px 0;">

            <p>
                You don’t have to solve your whole life today.
            </p>

            <p>
                Just notice what’s heavy, what’s yours, what isn’t, and what the next step might be.
            </p>

            <p style="margin-top:24px;">
                If you'd like, hit reply and tell me what came up while doing this exercise.
            </p>

            <p>
                I read every response.
            </p>

            <div style="margin-top:28px;">
                <p><strong>Built by a nurse, for healthcare professionals.</strong></p>

                <p style="color:#6B7280; font-size:12px;">
                    You’re receiving this because you signed up for DailyPulseWatch.
                </p>
            </div>

        </div>

    </body>
    </html>
    """

    email_payload = {
        "from": FROM_EMAIL,
        "to": [email],
        "subject": "Your Healthcare Worker’s Mental Unload",
        "html": html,
    }

    if REPLY_TO_EMAIL:
        email_payload["reply_to"] = REPLY_TO_EMAIL

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=email_payload,
    )

    if response.status_code == 200:
        print(f"✅ Mental Unload email sent to {email}")
    else:
        print(f"❌ Mental Unload email failed for {email}: {response.text}")