# ============================================================
# DailyPulseWatch — Email Template (HTML)
# ============================================================

from mailer.content import pollen_level


def build_email(moon, weather, horoscopes, quote, user_email, pollen):

    # -----------------------
    # WEATHER SUMMARY (SAFE)
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
    # COMMUTE LOGIC (SAFE)
    # -----------------------
    if getattr(weather, "unavailable", False):
        commute_line = "Commute conditions unavailable due to missing weather data."
        commute_details_html = ""
    else:
        if weather.freezing and weather.precip_mm == 0:
            commute_line = "Cold temperatures are present, but dry conditions reduce the risk of slick roads."
            ice_risk = "Low"
            ice_text = "Freezing temperatures are present, but without precipitation, black ice is unlikely."
        elif weather.freezing and weather.precip_mm > 0:
            commute_line = "Cold temperatures combined with precipitation may make the commute more hazardous."
            ice_risk = "Elevated"
            ice_text = "Freezing temperatures and moisture mean black ice could form on untreated surfaces."
        else:
            commute_line = "No major weather-related commute concerns."
            ice_risk = "None"
            ice_text = "Temperatures are above freezing."

        commute_details_html = ""
        if weather.freezing:
            precip_in = round(weather.precip_mm * 0.03937, 2)

            commute_details_html = f"""
            <div style="border-top:1px solid #E5E7EB; padding-top:10px; margin-top:10px;">
                <p style="margin:0;">
                    <strong>Precipitation:</strong> {precip_in} in<br/>
                    <strong>Black Ice Risk:</strong> {ice_risk}
                </p>
                <p style="margin-top:8px;">{ice_text}</p>
            </div>
            """

    # -----------------------
    # 🌿 POLLEN SECTION (NEW)
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
            <p style="margin:0;">
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
    if horoscopes:
        items = "".join(
            f"<p style='margin-bottom:12px;'><strong>{sign.title()}</strong><br/>{text}</p>"
            for sign, text in horoscopes.items()
            if text
        )

        horoscope_html = f"""
        <div style="
            margin-top:24px;
            padding:18px;
            border:1px solid #E5E7EB;
            border-radius:14px;
            box-shadow:0 6px 14px rgba(0,0,0,0.08);
        ">
            <h4 style="margin-top:0;">🔮 Optional Horoscope</h4>
            {items}
        </div>
        """

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

            <h2 style="margin-top:0;">🌅 DailyPulseWatch</h2>

            <p style="margin-bottom:20px;">
                Here’s your daily briefing to help you start your day with clarity.
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
                {commute_details_html}
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
                    <a href="https://dailypulsewatch.onrender.com/unsubscribe?email={user_email}"
                       style="color:#2563EB; text-decoration:none;">
                       Unsubscribe
                    </a>
                </p>
            </div>

        </div>

    </body>
    </html>
    """

    return html