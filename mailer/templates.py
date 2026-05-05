# ============================================================
# DailyPulseWatch — Email Template (HTML)
# ============================================================

from mailer.content import pollen_level, allergy_risk, pollen_context_line


def build_email(moon, weather, horoscopes, quote, user_email, pollen, headlines=None):

    headlines = headlines or []

    # -----------------------
    # WEATHER SUMMARY (SAFE + GMAIL-FRIENDLY)
    # -----------------------
    if getattr(weather, "unavailable", False):
        weather_line = "Weather data is temporarily unavailable."
        sun_line = "Sunrise: —<br/>Sunset: —"
    else:
        today_condition = getattr(weather, "condition", "Weather conditions unavailable")
        tomorrow_condition = getattr(weather, "tomorrow_condition", "Weather conditions unavailable")

        weather_line = f"""
        <strong>Today:</strong> {today_condition}<br/>
        High: {weather.high_f}°F | Low: {weather.low_f}°F
        """

        if getattr(weather, "tomorrow_high_f", None) is not None:
            weather_line += f"""
            <br/><strong>Tomorrow:</strong> {tomorrow_condition}<br/>
            High: {weather.tomorrow_high_f}°F | Low: {weather.tomorrow_low_f}°F
            """

        sun_line = f"""
        <strong>Today:</strong> Sunrise {weather.sunrise} | Sunset {weather.sunset}
        """

        if getattr(weather, "tomorrow_sunrise", None):
            sun_line += f"""
            <br/><strong>Tomorrow:</strong> Sunrise {weather.tomorrow_sunrise} | Sunset {weather.tomorrow_sunset}
            """

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
            <p style="margin:10px 0 0 0; padding-top:10px; border-top:1px solid #E5E7EB;">
                <strong>Precipitation:</strong> {precip_in} in<br/>
                <strong>Black Ice Risk:</strong> {ice_risk}<br/>
                {ice_text}
            </p>
            """

    # -----------------------
    # POLLEN SECTION
    # -----------------------
    pollen_html = ""

    if pollen:
        risk = allergy_risk(pollen)
        context_line = pollen_context_line(weather)

        pollen_html = f"""
        <div style="margin-top:18px; padding:16px; border:1px solid #E5E7EB; border-radius:14px; background:#F9FAFB;">
            <h4 style="margin:0 0 10px 0;">🌿 Pollen Levels</h4>
            <p style="margin:0 0 10px 0;"><strong>Allergy Risk:</strong> {risk}</p>
            <p style="margin:0;">
                Alder: {pollen_level(getattr(pollen, 'alder', 0))}<br/>
                Birch: {pollen_level(getattr(pollen, 'birch', 0))}<br/>
                Grass: {pollen_level(getattr(pollen, 'grass', 0))}<br/>
                Ragweed: {pollen_level(getattr(pollen, 'ragweed', 0))}
            </p>
            <p style="margin:10px 0 0 0; font-size:13px; color:#4B5563;">{context_line}</p>
        </div>
        """

    # -----------------------
    # HEADLINES SECTION
    # -----------------------
    headlines_html = ""

    if headlines:
        items = ""

        for h in headlines:
            items += f"""
            <p style="margin:0 0 12px 0;">
                <strong style="color:#374151;">{h.source}</strong><br/>
                <a href="{h.link}" style="color:#2563EB; text-decoration:none;">{h.title}</a>
            </p>
            """

        headlines_html = f"""
        <div style="margin-top:20px; padding:16px; border:1px solid #E5E7EB; border-radius:14px; background:#FFFFFF;">
            <h4 style="margin:0 0 10px 0;">📰 Today’s Headlines</h4>
            <p style="margin:0 0 12px 0; color:#4B5563; font-size:13px;">
                A quick skim of general and healthcare headlines.
            </p>
            {items}
        </div>
        """

    # -----------------------
    # HOROSCOPE BLOCK
    # -----------------------
    horoscope_html = ""

    if horoscopes:
        items = "".join(
            f"<p style='margin:0 0 12px 0;'><strong>{sign.title()}</strong><br/>{text}</p>"
            for sign, text in horoscopes.items()
            if text
        )

        horoscope_html = f"""
        <div style="margin-top:20px; padding:16px; border:1px solid #E5E7EB; border-radius:14px;">
            <h4 style="margin:0 0 10px 0;">🔮 Optional Horoscope</h4>
            {items}
        </div>
        """

    # -----------------------
    # HTML TEMPLATE
    # -----------------------
    html = f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif; background:#F3F4F6; padding:20px;">

        <div style="max-width:640px; margin:auto; background:#FFFFFF; padding:28px; border-radius:18px; border:1px solid #E5E7EB;">

            <h2 style="margin:0 0 16px 0;">🌅 DailyPulseWatch</h2>

            <p style="margin:0 0 20px 0;">
                Here’s your daily briefing to help you start your day with clarity.
            </p>

            <h4 style="margin:20px 0 8px 0;">🌤 Weather</h4>
            <p style="margin:0;">{weather_line}</p>

            <h4 style="margin:20px 0 8px 0;">🌅 Sun</h4>
            <p style="margin:0;">{sun_line}</p>

            <hr style="border:none; border-top:1px solid #E5E7EB; margin:20px 0;">

            <div style="padding:16px; background:#F9FAFB; border:1px solid #E5E7EB; border-radius:14px;">
                <h4 style="margin:0 0 10px 0;">🚗 Commute Weather Watch</h4>
                <p style="margin:0;">{commute_line}</p>
                {commute_details_html}
            </div>

            {pollen_html}

            {headlines_html}

            <hr style="border:none; border-top:1px solid #E5E7EB; margin:20px 0;">

            <h4 style="margin:0 0 8px 0;">🌙 Moon</h4>
            <p style="margin:0;">
                <strong>{moon.phase}</strong><br/>
                <em>{moon.meaning}</em>
            </p>

            {horoscope_html}

            <hr style="border:none; border-top:1px solid #E5E7EB; margin:20px 0;">

            <h4 style="margin:0 0 8px 0;">💬 Quote</h4>
            <p style="margin:0;">
                “{quote.get('text','')}”<br/>
                — {quote.get('author','')}
            </p>

            <div style="margin-top:24px;">
                <p style="margin:0 0 10px 0;"><strong>Built by a nurse, for nurses.</strong></p>

                <p style="color:#6B7280; font-size:12px; margin:0 0 10px 0;">
                    You’re receiving this because you signed up for DailyPulseWatch.
                </p>

                <p style="font-size:12px; margin:0;">
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