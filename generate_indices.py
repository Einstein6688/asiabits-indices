#!/usr/bin/env python3
"""
asiabits Indices Tool (GitHub Actions version)
Fetches market data from API and generates DE/EN PNG images
Sends images directly to Lark group via App API
"""

import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Check if playwright is available
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# Configuration
API_URL = "https://my-finance-api123-88898ea8eb5b.herokuapp.com/indices"
OUTPUT_DIR = Path("./output")

# Lark App Configuration (from environment variables or defaults)
LARK_APP_ID = os.environ.get("LARK_APP_ID", "cli_a9e5e0e4ad38de19")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "ME2g5rYepm8gP0xRduXqAhU62OKgnWmw")
LARK_CHAT_ID = None  # Will be auto-detected

# Shanghai timezone (UTC+8)
SHANGHAI_TZ = timezone(timedelta(hours=8))

# Index mapping: API name -> (Display name, Country code)
INDEX_MAP = {
    "Shanghai": ("Shanghai", "CN"),
    "CSI 300": ("CSI 300", "CN"),
    "Singapore": ("STI", "SG"),
    "KOSPI": ("KOSPI", "KR"),
    "Nikkei": ("Nikkei", "JP"),
    "Hang Seng": ("Hang Seng", "HK"),
}

# ============ Lark API Functions ============

def get_tenant_access_token():
    """Get Lark tenant access token"""
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())
        if result.get('code') == 0:
            return result.get('tenant_access_token')
        else:
            raise Exception(f"Failed to get token: {result}")

def get_bot_chats(token):
    """Get list of chats the bot is in"""
    url = "https://open.larksuite.com/open-apis/im/v1/chats?page_size=100"
    
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())
        if result.get('code') == 0:
            return result.get('data', {}).get('items', [])
        else:
            raise Exception(f"Failed to get chats: {result}")

def upload_image_to_lark(token, image_path):
    """Upload image to Lark and get image_key"""
    url = "https://open.larksuite.com/open-apis/im/v1/images"
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    body = []
    body.append(f'--{boundary}'.encode())
    body.append(b'Content-Disposition: form-data; name="image_type"')
    body.append(b'')
    body.append(b'message')
    
    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="image"; filename="{Path(image_path).name}"'.encode())
    body.append(b'Content-Type: image/png')
    body.append(b'')
    body.append(image_data)
    
    body.append(f'--{boundary}--'.encode())
    
    body_bytes = b'\r\n'.join(body)
    
    req = urllib.request.Request(url, data=body_bytes, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    })
    
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
        if result.get('code') == 0:
            return result.get('data', {}).get('image_key')
        else:
            raise Exception(f"Failed to upload image: {result}")

def send_image_to_chat(token, chat_id, image_key):
    """Send image to Lark chat"""
    url = f"https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=chat_id"
    
    content = json.dumps({"image_key": image_key})
    
    data = json.dumps({
        "receive_id": chat_id,
        "msg_type": "image",
        "content": content
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())
        if result.get('code') == 0:
            return True
        else:
            raise Exception(f"Failed to send image: {result}")

def send_text_to_chat(token, chat_id, text):
    """Send text message to Lark chat"""
    url = f"https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=chat_id"
    
    content = json.dumps({"text": text})
    
    data = json.dumps({
        "receive_id": chat_id,
        "msg_type": "text",
        "content": content
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode())
        if result.get('code') == 0:
            return True
        else:
            raise Exception(f"Failed to send text: {result}")

# ============ Data & Rendering Functions ============

def fetch_data():
    """Fetch indices data from API"""
    req = urllib.request.Request(API_URL)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode())

def format_number_de(num):
    formatted = f"{num:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted

def format_number_en(num):
    return f"{num:,.2f}"

def format_percent_de(pct):
    if pct >= 0:
        return f'<span style="color:#0f9d58;">▲ +{abs(pct):.2f}%</span>'.replace(".", ",")
    else:
        return f'<span style="color:#e03a3c;">▼ –{abs(pct):.2f}%</span>'.replace(".", ",")

def format_percent_en(pct):
    if pct >= 0:
        return f'<span style="color:#0f9d58;">▲ +{abs(pct):.2f}%</span>'
    else:
        return f'<span style="color:#e03a3c;">▼ −{abs(pct):.2f}%</span>'

def generate_html(data, lang="de"):
    now_shanghai = datetime.now(SHANGHAI_TZ)
    
    if lang == "de":
        title = "Indizes"
        subtitle = "Marktüberblick"
        col_price = "Kurs"
        col_24h = "24 h"
        col_ytd = "YTD"
        col_52w = "52W-H"
        timestamp = f'Zuletzt aktualisiert am <b style="color:#4d596a;">{now_shanghai.strftime("%d.%m.%Y, %H:%M")} Uhr</b> (GMT+8)'
        format_num = format_number_de
        format_pct = format_percent_de
    else:
        title = "Indices"
        subtitle = "Market snapshot"
        col_price = "Current"
        col_24h = "24 h"
        col_ytd = "YTD"
        col_52w = "52W-H"
        timestamp = f'Last updated on <b style="color:#4d596a;">{now_shanghai.strftime("%d.%m.%Y, %I:%M %p")}</b> (GMT+8)'
        format_num = format_number_en
        format_pct = format_percent_en
    
    rows_html = ""
    for i, item in enumerate(data):
        api_name = item["index"]
        if api_name not in INDEX_MAP:
            continue
            
        display_name, country = INDEX_MAP[api_name]
        bg_color = "#fff" if i % 2 == 0 else "#fcfcfd"
        
        rows_html += f'''
    <tr style="background:{bg_color};border-top:1px solid #f2f3f5;">
      <td style="padding:12px 14px;">
        <span style="display:inline-block;min-width:28px;padding:2px 6px;border-radius:10px;background:#f1f3f6;font-weight:700;font-size:11px;color:#3a4451;text-align:center;line-height:1.2;">{country}</span><span style="font-weight:600;color:#111826;margin-left:4px;">{display_name}</span>
      </td>
      <td style="padding:12px 8px;text-align:right;white-space:nowrap;">{format_num(item["current_price"])}</td>
      <td style="padding:12px 8px;text-align:right;white-space:nowrap;">{format_pct(item["change_pct"])}</td>
      <td style="padding:12px 8px;text-align:right;white-space:nowrap;">{format_pct(item["ytd_pct"])}</td>
      <td style="padding:12px 14px;text-align:right;white-space:nowrap;">{format_num(item["week_52_high"])}</td>
    </tr>'''
    
    html = f'''
<div id="asiabits-card" style="max-width:480px;margin:14px auto;border:1px solid #e8ecef;border-radius:14px;background:#fff;box-shadow:0 2px 4px rgba(0,0,0,.03);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;overflow:hidden;">
  <div style="max-width:480px;margin:0 auto;background:#fff;overflow:hidden;">
    <div style="display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid #f2f3f5;background:#fcfcfd;">
      <div style="width:4px;height:18px;background:#D26C13;border-radius:4px;"></div>
      <div style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#D26C13;font-weight:700;">{title}</div>
      <div style="margin-left:auto;font-size:11px;color:#7a8594;">{subtitle}</div>
    </div>
    <table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead>
        <tr style="background:#fafbfc;">
          <th style="text-align:left;padding:8px 14px;color:#7a8594;font-weight:600;">Index</th>
          <th style="text-align:right;padding:8px;color:#7a8594;font-weight:600;">{col_price}</th>
          <th style="text-align:right;padding:8px;color:#7a8594;font-weight:600;">{col_24h}</th>
          <th style="text-align:right;padding:8px;color:#7a8594;font-weight:600;">{col_ytd}</th>
          <th style="text-align:right;padding:8px 14px;color:#7a8594;font-weight:600;">{col_52w}</th>
        </tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
    <div style="padding:10px 14px;border-top:1px solid #f2f3f5;background:#fcfcfd;font-size:11px;color:#7a8594;display:flex;align-items:center;gap:6px;">
      <div style="width:6px;height:6px;background:#D26C13;border-radius:50%;"></div>
      {timestamp}
    </div>
  </div>
</div>
'''
    return html

def html_to_png(html_body, out_path, scale=3):
    if not HAS_PLAYWRIGHT:
        raise Exception("Playwright not installed")
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        </style>
      </head>
      <body style="margin:0;padding:20px;background:#f5f6f8;">
        {html_body}
      </body>
    </html>
    """
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=scale)
        page.set_content(full_html, wait_until="networkidle")
        
        card = page.locator("#asiabits-card")
        card.screenshot(path=out_path, type="png")
        
        browser.close()
    
    return out_path

# ============ Main Function ============

def main():
    global LARK_CHAT_ID
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get Lark token
    print("🔐 Getting Lark access token...")
    try:
        token = get_tenant_access_token()
        print("✅ Token obtained")
    except Exception as e:
        print(f"❌ Failed to get Lark token: {e}")
        token = None
    
    # Find chat ID
    if token and not LARK_CHAT_ID:
        print("🔍 Finding bot chats...")
        try:
            chats = get_bot_chats(token)
            if chats:
                print(f"📋 Found {len(chats)} chat(s):")
                for chat in chats:
                    print(f"   - {chat.get('name', 'Unknown')}: {chat.get('chat_id')}")
                LARK_CHAT_ID = chats[0].get('chat_id')
                print(f"✅ Using chat: {chats[0].get('name')}")
            else:
                print("⚠️ No chats found.")
        except Exception as e:
            print(f"❌ Failed to get chats: {e}")
    
    # Fetch market data
    print("🔄 Fetching market data...")
    data = fetch_data()
    print(f"✅ Got {len(data)} indices")
    
    now_shanghai = datetime.now(SHANGHAI_TZ)
    today = now_shanghai.strftime("%Y%m%d")
    
    # Generate images
    print("🇩🇪 Generating German image...")
    html_de = generate_html(data, lang="de")
    file_de = OUTPUT_DIR / f"indices_DE_{today}.png"
    html_to_png(html_de, str(file_de))
    print(f"✅ Saved {file_de}")
    
    print("🇬🇧 Generating English image...")
    html_en = generate_html(data, lang="en")
    file_en = OUTPUT_DIR / f"indices_EN_{today}.png"
    html_to_png(html_en, str(file_en))
    print(f"✅ Saved {file_en}")
    
    # Send to Lark
    if token and LARK_CHAT_ID:
        print("📤 Sending images to Lark...")
        try:
            date_str = now_shanghai.strftime("%d.%m.%Y")
            send_text_to_chat(token, LARK_CHAT_ID, f"📊 asiabits Indices - {date_str}")
            
            print("   Uploading DE image...")
            image_key_de = upload_image_to_lark(token, str(file_de))
            send_image_to_chat(token, LARK_CHAT_ID, image_key_de)
            print("   ✅ DE image sent")
            
            print("   Uploading EN image...")
            image_key_en = upload_image_to_lark(token, str(file_en))
            send_image_to_chat(token, LARK_CHAT_ID, image_key_en)
            print("   ✅ EN image sent")
            
            print("✅ All images sent to Lark!")
        except Exception as e:
            print(f"❌ Failed to send to Lark: {e}")
    
    print(f"\n🎉 Done!")
    return str(file_de), str(file_en)

if __name__ == "__main__":
    main()
