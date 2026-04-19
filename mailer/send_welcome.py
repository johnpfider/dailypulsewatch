import requests
import os

from mailer.weather_cache import get_cached_weather
from mailer.content import (
    compute_moon,
    todays_quote,
    fetch_pollen,
    pollen_level,
    pollen_context_line,
)
from api.geo import geocode_zip
from mailer.horoscope import get_horoscopes


RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")


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
        # WEATHER (SAFE)
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
        # COMMUTE (SIMPLE)
        # -----------------------
        commute_line = "No major weather-related commute concerns."

        # -----------------------
        # 🌿 POLLEN HTML (WITH CONTEXT)
        # -----------------------
        pollen_html = ""

        if pollen:
            context_line = pollen_context_line(weather)

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

                <p style="margin-top:12px; font-size:13px; color:#4B5563;">
                    {context_line}
                </p>
            </div>
            """

        # -----------------------
        # 🔮 HOROSCOPE
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
        # UNSUBSCRIBE
        # -----------------------
        unsubscribe_link = f"https://dailypulsewatch.onrender.com/unsubscribe?email={email}"

        # -----------------------
        # HTML TEMPLATE
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

                <h2>👋 Welcome to DailyPulseWatch</h2>

                <p>You're officially on the list.</p>

                <p>
                    Starting today, you'll receive a simple daily briefing
                    designed to help you start your day with clarity.
                </p>

                <h4>🌤 Weather</h4>
                <p>{weather_line}</p>

                <h4>🌅 Sun</h4>
                <p>
                    Sunrise: {sunrise}<br/>
                    Sunset: {sunset}
                </p>

                <hr>

                <div style="padding:18px; background:#F9FAFB; border-radius:14px;">
                    <h4>🚗 Commute Weather Watch</h4>
                    <p>{commute_line}</p>
                </div>

                {pollen_html}

                <hr>

                <h4>🌙 Moon</h4>
                <p>
                    <strong>{moon.phase}</strong><br/>
                    <em>{moon.meaning}</em>
                </p>

                {horoscope_html}

                <hr>

                <h4>💬 Quote</h4>
                <p>
                    “{quote.get('text','')}”<br/>
                    — {quote.get('author','')}
                </p>

                <div style="margin-top:28px;">
                    <p><strong>Built by a nurse, for nurses.</strong></p>

                    <p style="color:#6B7280; font-size:12px;">
                        You’re receiving this because you signed up for DailyPulseWatch.
                    </p>

                    <p style="font-size:12px;">
                        <a href="{unsubscribe_link}">
                            Unsubscribe
                        </a>
                    </p>
                </div>

            </div>

        </body>
        </html>
        """

        # -----------------------
        # SEND VIA RESEND
        # -----------------------
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_EMAIL,
                "to": [email],
                "subject": "Welcome to DailyPulseWatch",
                "html": html,
            },
        )

        if response.status_code == 200:
            print(f"✅ Welcome email sent to {email}")
        else:
            print(f"❌ Failed: {response.text}")

    except Exception as e:
        print(f"❌ Failed to send welcome email to {email}: {e}")