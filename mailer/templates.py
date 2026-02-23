# ============================================================
# DailyPulseWatch — Email Template
# ============================================================

def build_email(moon, weather, horoscopes, quote):

    weather_line = (
        f"High of {weather.high_f}°F, low of {weather.low_f}°F. "
        "Mostly clear with no precipitation expected."
        if weather.precip_mm == 0
        else
        f"High of {weather.high_f}°F, low of {weather.low_f}°F. Precipitation expected."
    )

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
        commute_details_html = f"""
          <div style="border-top:1px solid #E5E7EB; padding-top:10px;">
            <p style="margin:0;">
              <strong>Precipitation:</strong> {weather.precip_mm} mm<br/>
              <strong>Black Ice Risk:</strong> {ice_risk}
            </p>
            <p style="margin-top:8px;">{ice_text}</p>
          </div>
        """

    horoscope_html = ""
    if horoscopes:
        items = "".join(
            f"<p><strong>{sign}</strong><br/>{text}</p>"
            for sign, text in horoscopes.items()
            if text
        )
        horoscope_html = f"""
        <div style="margin-top:20px; padding:18px; border:1px solid #E5E7EB;
        border-radius:14px; box-shadow:0 4px 10px rgba(0,0,0,0.06);">
          <h3>Optional Horoscope</h3>
          {items}
        </div>
        """

    html = f"""
    <html>
    <body style="font-family:Arial,Helvetica,sans-serif; background:#F3F4F6; padding:20px;">
      <div style="max-width:640px; margin:auto; background:#FFFFFF; padding:24px;
      border-radius:16px; border:1px solid #E5E7EB;
      box-shadow:0 10px 24px rgba(0,0,0,0.08);">

        <h2>Daily Pulse Watch</h2>
        <p>Here’s your daily heads-up to help you prepare for the day ahead.</p>

        <h3>Weather (Next 24 Hours)</h3>
        <p>{weather_line}</p>

        <div style="margin-top:16px; padding:18px; background:#F9FAFB;
        border:1px solid #E5E7EB; border-radius:14px;">
          <h3 style="margin-top:0;">Commute Weather Watch</h3>
          <p>{commute_line}</p>
          {commute_details_html}
        </div>

        <h3>Moon</h3>
        <p><strong>{moon.phase}</strong><br/><em>{moon.meaning}</em></p>

        {horoscope_html}

        <h3>Today’s Encouragement</h3>
        <blockquote style="font-style:italic;">
          “{quote['text']}”
          <br/>— {quote['author']}
        </blockquote>

        <hr/>
        <p style="font-size:12px;">To unsubscribe, reply STOP.</p>

      </div>
    </body>
    </html>
    """

    return html