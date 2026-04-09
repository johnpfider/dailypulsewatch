from mailer.weather_cache import get_cached_weather
from mailer.content import compute_moon, todays_quote, fetch_pollen, pollen_level
from api.geo import geocode_zip
from mailer.horoscope import get_horoscopes
import boto3
import os


# =========================
# AWS SES CLIENT
# =========================
ses = boto3.client(
    "ses",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


def send_welcome_email(email, zip_code, horoscope):

    try:
        # -----------------------
        # DATA
        # -----------------------
        weather = get_cached_weather(zip_code)

        lat, lon = geocode_zip(zip_code)
        pollen = fetch_pollen(lat, lon)

        moon = compute_moon()
        quote = todays_quote()

        horoscope_map = {}
        if horoscope:
            horoscope_map = get_horoscopes({horoscope.lower()})

        # -----------------------
        # WEATHER SAFETY
        # -----------------------
        if getattr(weather, "unavailable", False):
            weather_line = "Weather data is temporarily unavailable."
            sunrise = "—"
            sunset = "—"
        else:
            weather_line = f"High: {weather.high_f}°F<br/>Low: {weather.low_f}°F"
            sunrise = weather.sunrise
            sunset = weather.sunset

        # -----------------------
        # COMMUTE (simple version)
        # -----------------------
        commute_line = "No major weather-related commute concerns."

        # -----------------------
        # POLLEN HTML
        # -----------------------
        pollen_html = ""

        if pollen and any([
            pollen.alder,
            pollen.birch,
            pollen.grass,
            pollen.ragweed
        ]):
            pollen_html = f"""
            <div style="
                margin-top:20px;
                padding:18px;
                border:1px solid #E5E7EB;
                border-radius:14px;
                background:#F9FAFB;
            ">
                <h4 style="margin-top:0;">🌿 Pollen Levels</h4>
                <p>
                    Alder: {pollen_level(pollen.alder)}<br/>
                    Birch: {pollen_level(pollen.birch)}<br/>
                    Grass: {pollen_level(pollen.grass)}<br/>
                    Ragweed: {pollen_level(pollen.ragweed)}
                </p>
            </div>
            """

        # -----------------------
        # HOROSCOPE BLOCK
        # -----------------------
        horoscope_html = ""
        if horoscope and horoscope_map:
            sign = horoscope.lower()

            horoscope_html = f"""
            <div style="
                margin-top:24px;
                padding:18px;
                border:1px solid #E5E7EB;
                border-radius:14px;
                box-shadow:0 6px 14px rgba(0,0,0,0.08);
            ">
                <h4 style="margin-top:0;">🔮 Optional Horoscope</h4>
                <p><strong>{horoscope.title()}</strong><br/>{horoscope_map.get(sign, "")}</p>
            </div>
            """

        # -----------------------
        # UNSUBSCRIBE LINK
        # -----------------------
        unsubscribe_link = f"https://dailypulsewatch.onrender.com/unsubscribe?email={email}"

        # -----------------------
        # HTML
        # -----------------------
        html = f"""
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

                <h2 style="margin-top:0;">👋 Welcome to DailyPulseWatch</h2>

                <p>
                    You're officially on the list.
                </p>

                <p style="margin-bottom:20px;">
                    Starting today, you'll receive a simple daily briefing designed to help you start your day with clarity.
                </p>

                <h4 style="margin-top:20px;">🌤 Weather</h4>
                <p>{weather_line}</p>

                <h4 style="margin-top:20px;">🌅 Sun</h4>
                <p>
                    Sunrise: {sunrise}<br/>
                    Sunset: {sunset}
                </p>

                <hr style="border:none; border-top:1px solid #E5E7EB; margin:20px 0;">

                <div style="
                    margin-top:10px;
                    padding:18px;
                    background:#F9FAFB;
                    border:1px solid #E5E7EB;
                    border-radius:14px;
                ">
                    <h4 style="margin-top:0;">🚗 Commute Weather Watch</h4>
                    <p>{commute_line}</p>
                </div>

                {pollen_html}

                <hr style="border:none; border-top:1px solid #E5E7EB; margin:20px 0;">

                <h4>🌙 Moon</h4>
                <p>
                    <strong>{moon.phase}</strong><br/>
                    <em>{moon.meaning}</em>
                </p>

                {horoscope_html}

                <hr style="border:none; border-top:1px solid #E5E7EB; margin:20px 0;">

                <h4>💬 Quote</h4>
                <p>
                    “{quote.get('text','')}”<br/>
                    — {quote.get('author','')}
                </p>

                <!-- FOOTER -->
                <div style="margin-top:28px;">
                    <p><strong>Built by a nurse, for nurses.</strong></p>

                    <p style="color:#6B7280; font-size:12px;">
                        You’re receiving this because you signed up for DailyPulseWatch.
                    </p>

                    <p style="margin-top:10px; font-size:12px;">
                        <a href="{unsubscribe_link}"
                           style="color:#2563EB; text-decoration:none;">
                           Unsubscribe
                        </a>
                    </p>
                </div>

            </div>

        </body>
        </html>
        """

        # -----------------------
        # SEND EMAIL
        # -----------------------
        ses.send_email(
            Source=os.getenv("FROM_EMAIL"),
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": "Welcome to DailyPulseWatch"},
                "Body": {
                    "Html": {"Data": html}
                },
            },
        )

        print(f"✅ Welcome email sent to {email}")

    except Exception as e:
        print(f"❌ Failed to send welcome email to {email}: {e}")