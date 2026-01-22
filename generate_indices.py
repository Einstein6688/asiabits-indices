import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright
import base64

# Lark Credentials (from environment variables or fallback to defaults)
LARK_APP_ID = os.environ.get("LARK_APP_ID", "cli_a9e5e0e4ad38de19")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "ME2g5rYepm8gP0xRduXqAhU62OKgnWmw")
LARK_CHAT_ID = os.environ.get("LARK_CHAT_ID", "oc_f4614007f39a5151ab32ece70013f87e")

# API Endpoint
API_URL = "https://my-finance-api123-88898ea8eb5b.herokuapp.com/indices"

def get_lark_tenant_access_token():
    """Get Lark tenant access token"""
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["tenant_access_token"]

def fetch_indices_data():
    """Fetch indices data from API"""
    response = requests.get(API_URL)
    response.raise_for_status()
    return response.json()

def format_number_de(value):
    """Format number for German locale (1.234,56)"""
    if value is None:
        return "—"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_number_en(value):
    """Format number for English locale (1,234.56)"""
    if value is None:
        return "—"
    return f"{value:,.2f}"

def format_percent(value):
    """Format percentage with + or - sign"""
    if value is None:
        return "—"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"

def get_arrow(value):
    """Get arrow symbol and color based on value"""
    if value is None or value == 0:
        return "", "#666666"
    return ("▲", "#00AA00") if value > 0 else ("▼", "#DD0000")

def generate_html(data, lang="de"):
    """Generate HTML for the indices table"""
    
    # FIXED TIMESTAMP: Always show 6:00 AM Shanghai time
    shanghai_tz = timezone(timedelta(hours=8))
    now = datetime.now(shanghai_tz)
    fixed_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
    
    if lang == "de":
        timestamp = fixed_time.strftime("%d.%m.%Y, %H:%M Uhr")
        format_num = format_number_de
        headers = ["Index", "Kurs", "24h %", "YTD %", "52W-High"]
    else:
        timestamp = fixed_time.strftime("%d.%m.%Y, %I:%M %p")
        format_num = format_number_en
        headers = ["Index", "Current", "24h %", "YTD %", "52W-High"]
    
    # Build table rows
    rows_html = ""
    for item in data:
        change_24h = item.get("change_pct")
        change_ytd = item.get("ytd_pct")

        arrow_24h, color_24h = get_arrow(change_24h)
        arrow_ytd, color_ytd = get_arrow(change_ytd)

        rows_html += f"""
        <tr>
            <td class="index-name">{item['index']}</td>
            <td class="value">{format_num(item.get('current_price'))}</td>
            <td class="change" style="color: {color_24h};">
                {arrow_24h} {format_percent(change_24h)}
            </td>
            <td class="change" style="color: {color_ytd};">
                {arrow_ytd} {format_percent(change_ytd)}
            </td>
            <td class="value">{format_num(item.get('week_52_high'))}</td>
        </tr>
        """
    
    # Build header row
    headers_html = "".join([f"<th>{h}</th>" for h in headers])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: white;
                padding: 40px;
            }}
            
            .container {{
                max-width: 1000px;
                margin: 0 auto;
            }}
            
            .header {{
                margin-bottom: 30px;
            }}
            
            h1 {{
                font-size: 32px;
                font-weight: 600;
                color: #1a1a1a;
                margin-bottom: 8px;
            }}
            
            .timestamp {{
                font-size: 14px;
                color: #666666;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }}
            
            th {{
                background: #f8f9fa;
                padding: 16px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
                color: #495057;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 2px solid #dee2e6;
            }}
            
            td {{
                padding: 16px;
                border-bottom: 1px solid #f0f0f0;
                font-size: 15px;
            }}
            
            tr:last-child td {{
                border-bottom: none;
            }}
            
            tr:hover {{
                background: #f8f9fa;
            }}
            
            .index-name {{
                font-weight: 600;
                color: #1a1a1a;
            }}
            
            .value {{
                color: #495057;
                text-align: right;
            }}
            
            .change {{
                text-align: right;
                font-weight: 500;
            }}
            
            th:nth-child(1),
            td:nth-child(1) {{
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{"Asiatische Indizes" if lang == "de" else "Asian Indices"}</h1>
                <div class="timestamp">{timestamp}</div>
            </div>
            <table>
                <thead>
                    <tr>{headers_html}</tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_image(html_content, output_path):
    """Generate PNG image from HTML using Playwright"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.set_content(html_content)
        
        # Wait for content to render
        page.wait_for_timeout(1000)
        
        # Take screenshot
        page.screenshot(path=output_path, full_page=True, scale="device")
        browser.close()

def upload_image_to_lark(token, image_path):
    """Upload image to Lark and get image_key"""
    url = "https://open.larksuite.com/open-apis/im/v1/images"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(image_path, 'rb') as f:
        files = {
            'image': (image_path, f, 'image/png')
        }
        data = {
            'image_type': 'message'
        }
        response = requests.post(url, headers=headers, files=files, data=data)
    
    response.raise_for_status()
    return response.json()["data"]["image_key"]

def send_message_to_lark(token, chat_id, image_key, lang="de"):
    """Send message with image to Lark chat"""
    url = "https://open.larksuite.com/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    text = "Tägliche Indizes-Übersicht 📊" if lang == "de" else "Daily Indices Overview 📊"
    
    params = {
        "receive_id_type": "chat_id"
    }
    
    data = {
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps({
            "zh_cn": {
                "title": text,
                "content": [
                    [
                        {
                            "tag": "img",
                            "image_key": image_key
                        }
                    ]
                ]
            }
        })
    }
    
    response = requests.post(url, headers=headers, params=params, json=data)
    if response.status_code != 200:
        print(f"Lark API Error: {response.status_code}")
        print(f"Response: {response.text}")
    response.raise_for_status()
    return response.json()

def main():
    """Main function"""
    print("🚀 Starting indices chart generation...")
    
    # Fetch data
    print("📊 Fetching indices data...")
    data = fetch_indices_data()
    
    # Get Lark token
    print("🔑 Getting Lark access token...")
    token = get_lark_tenant_access_token()
    
    # Generate and send German version
    print("🇩🇪 Generating German version...")
    html_de = generate_html(data, lang="de")
    generate_image(html_de, "indices_de.png")
    
    print("📤 Uploading German image to Lark...")
    image_key_de = upload_image_to_lark(token, "indices_de.png")
    
    print("💬 Sending German message to Lark...")
    send_message_to_lark(token, LARK_CHAT_ID, image_key_de, lang="de")
    
    # Wait a bit before sending English version
    time.sleep(2)
    
    # Generate and send English version
    print("🇬🇧 Generating English version...")
    html_en = generate_html(data, lang="en")
    generate_image(html_en, "indices_en.png")
    
    print("📤 Uploading English image to Lark...")
    image_key_en = upload_image_to_lark(token, "indices_en.png")
    
    print("💬 Sending English message to Lark...")
    send_message_to_lark(token, LARK_CHAT_ID, image_key_en, lang="en")
    
    print("✅ Done! Both charts sent to Lark successfully.")

if __name__ == "__main__":
    main()
