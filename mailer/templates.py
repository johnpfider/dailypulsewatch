# ============================================================
# DailyPulseWatch — Email Template (HTML)
# ============================================================

def build_email(moon, weather, horoscopes, quote):

    # -----------------------
    # WEATHER SUMMARY
    # -----------------------
    weather_line = (
        f"High: {weather.high_f}°F<br/>Low: {weather.low_f}°F"
    )

    # -----------------------
    # COMMUTE LOGIC
    # -----------------------
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
    # HOROSCOPE BLOCK
    # -----------------------
    horoscope_html = ""
    if horoscopes:
        items = "".join(
            f"<p><strong>{sign.title()}</strong><br/>{text}</p>"
            for sign, text in horoscopes.items()
            if text
        )

        horoscope_html = f"""
        <div style="
            margin-top:20px;
            padding:18px;
            border:1px solid #E5E7EB;
            border-radius:14px;
            box-shadow:0 4px 10px rgba(0,0,0,0.06);
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
            padding:24px;
            border-radius:16px;
            border:1px solid #E5E7EB;
            box-shadow:0 10px 24px rgba(0,0,0,0.08);
        ">

            <h2 style="margin-top:0;">🌅 DailyPulseWatch</h2>

            <p>
                Here’s your daily briefing to help you start your day with clarity.
            </p>

            <!-- WEATHER -->
            <h4>🌤 Weather</h4>
            <p>{weather_line}</p>

            <!-- SUN -->
            <h4>🌅 Sun</h4>
            <p>
                Sunrise: {weather.sunrise}<br/>
                Sunset: {weather.sunset}
            </p>

            <!-- COMMUTE -->
            <div style="
                margin-top:16px;
                padding:18px;
                background:#F9FAFB;
                border:1px solid #E5E7EB;
                border-radius:14px;
            ">
                <h4 style="margin-top:0;">🚗 Commute Weather Watch</h4>
                <p>{commute_line}</p>
                {commute_details_html}
            </div>

            <!-- MOON -->
            <h4 style="margin-top:20px;">🌙 Moon</h4>
            <p>
                <strong>{moon.phase}</strong><br/>
                <em>{moon.meaning}</em>
            </p>

            <!-- HOROSCOPE -->
            {horoscope_html}

            <!-- QUOTE -->
            <h4 style="margin-top:20px;">💬 Quote</h4>
            <p>
                “{quote.get('text','')}”<br/>
                — {quote.get('author','')}
            </p>

            <!-- FOOTER -->
            <div style="margin-top:24px;">
                <p><strong>Built by a nurse, for nurses.</strong></p>
                <p style="color:#6B7280; font-size:12px;">
                    You’re receiving this because you signed up for DailyPulseWatch.
                </p>
            </div>

        </div>

    </body>
    </html>
    """

    return html