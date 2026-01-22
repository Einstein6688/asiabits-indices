import requests
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

API_URL = "https://my-finance-api123-88898ea8eb5b.herokuapp.com/indices"

# Country codes for each index
COUNTRY_CODES = {
    "Shanghai": "CN",
    "CSI 300": "CN",
    "STI": "SG",
    "Singapore": "SG",
    "KOSPI": "KR",
    "Nikkei": "JP",
    "Hang Seng": "HK",
}

def fetch_indices_data():
    response = requests.get(API_URL)
    response.raise_for_status()
    return response.json()

def format_number(value):
    if value is None:
        return "—"
    return f"{value:,.2f}"

def format_percent(value):
    if value is None:
        return "—"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"

def get_color(value):
    if value is None or value == 0:
        return "#666666"
    return "#22c55e" if value > 0 else "#ef4444"

def get_arrow(value):
    if value is None or value == 0:
        return ""
    return "▲" if value > 0 else "▼"

def generate_html(data):
    shanghai_tz = timezone(timedelta(hours=8))
    now = datetime.now(shanghai_tz)
    timestamp = now.strftime("%d.%m.%Y, %I:%M %p")

    rows_html = ""
    for item in data:
        index_name = item.get('index', '')
        country_code = COUNTRY_CODES.get(index_name, "")
        current = item.get('current_price')
        change_24h = item.get('change_pct')
        change_ytd = item.get('ytd_pct')
        high_52w = item.get('week_52_high')

        color_24h = get_color(change_24h)
        color_ytd = get_color(change_ytd)
        arrow_24h = get_arrow(change_24h)
        arrow_ytd = get_arrow(change_ytd)

        rows_html += f"""
        <tr>
            <td class="index-cell">
                <span class="country-code">{country_code}</span>
                <span class="index-name">{index_name}</span>
            </td>
            <td class="value">{format_number(current)}</td>
            <td class="change" style="color: {color_24h};">{arrow_24h} {format_percent(change_24h)}</td>
            <td class="change" style="color: {color_ytd};">{arrow_ytd} {format_percent(change_ytd)}</td>
            <td class="value">{format_number(high_52w)}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 24px;
            border-bottom: 1px solid #eee;
        }}
        .title-section {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .orange-bar {{
            width: 4px;
            height: 24px;
            background: #f97316;
            border-radius: 2px;
        }}
        .title {{
            font-size: 18px;
            font-weight: 700;
            color: #f97316;
            letter-spacing: 1px;
        }}
        .subtitle {{
            font-size: 14px;
            color: #9ca3af;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            padding: 16px 24px;
            text-align: left;
            font-weight: 500;
            font-size: 13px;
            color: #6b7280;
            border-bottom: 1px solid #f0f0f0;
        }}
        th:not(:first-child) {{
            text-align: right;
        }}
        td {{
            padding: 20px 24px;
            border-bottom: 1px solid #f5f5f5;
            font-size: 15px;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        .index-cell {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .country-code {{
            background: #f3f4f6;
            color: #6b7280;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .index-name {{
            font-weight: 600;
            color: #1f2937;
        }}
        .value {{
            color: #374151;
            text-align: right;
            font-weight: 500;
        }}
        .change {{
            text-align: right;
            font-weight: 600;
        }}
        .footer {{
            padding: 16px 24px;
            border-top: 1px solid #f0f0f0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .orange-dot {{
            width: 8px;
            height: 8px;
            background: #f97316;
            border-radius: 50%;
        }}
        .footer-text {{
            font-size: 13px;
            color: #6b7280;
        }}
        .footer-date {{
            font-weight: 600;
            color: #374151;
        }}
        .footer-tz {{
            color: #9ca3af;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title-section">
                <div class="orange-bar"></div>
                <span class="title">INDICES</span>
            </div>
            <span class="subtitle">Market snapshot</span>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Index</th>
                    <th>Current</th>
                    <th>24 h</th>
                    <th>YTD</th>
                    <th>52W-H</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        <div class="footer">
            <div class="orange-dot"></div>
            <span class="footer-text">Last updated on</span>
            <span class="footer-date">{timestamp}</span>
            <span class="footer-tz">(GMT+8)</span>
        </div>
    </div>
</body>
</html>"""

def generate_image(html_content, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 700})
        page.set_content(html_content)
        page.wait_for_timeout(1000)
        element = page.query_selector('.container')
        element.screenshot(path=output_path)
        browser.close()

def main():
    print("Fetching indices data...")
    data = fetch_indices_data()
    print("Generating chart...")
    html = generate_html(data)
    generate_image(html, "indices_de.png")
    generate_image(html, "indices_en.png")
    print("Done!")

if __name__ == "__main__":
    main()
