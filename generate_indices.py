import requests                                                            
  from datetime import datetime, timezone, timedelta                         
  from playwright.sync_api import sync_playwright                            
                                                                             
  API_URL = "https://my-finance-api123-88898ea8eb5b.herokuapp.com/indices"   
                                                                             
  def fetch_indices_data():                                                  
      response = requests.get(API_URL)                                       
      response.raise_for_status()                                            
      return response.json()                                                 
                                                                             
  def format_number_de(value):                                               
      if value is None:                                                      
          return "—"                                                         
      return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X",
   ".")                                                                      
                                                                             
  def format_number_en(value):                                               
      if value is None:                                                      
          return "—"                                                         
      return f"{value:,.2f}"                                                 
                                                                             
  def format_percent(value):                                                 
      if value is None:                                                      
          return "—"                                                         
      sign = "+" if value >= 0 else ""                                       
      return f"{sign}{value:.2f}%"                                           
                                                                             
  def get_arrow(value):                                                      
      if value is None or value == 0:                                        
          return "", "#666666"                                               
      return ("▲", "#00AA00") if value > 0 else ("▼", "#DD0000")             
                                                                             
  def generate_html(data, lang="de"):                                        
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
              <td class="change" style="color: {color_24h};">{arrow_24h}     
  {format_percent(change_24h)}</td>                                          
              <td class="change" style="color: {color_ytd};">{arrow_ytd}     
  {format_percent(change_ytd)}</td>                                          
              <td class="value">{format_num(item.get('week_52_high'))}</td>  
          </tr>"""                                                           
                                                                             
      headers_html = "".join([f"<th>{h}</th>" for h in headers])             
                                                                             
      return f"""<!DOCTYPE html>                                             
  <html>                                                                     
  <head>                                                                     
      <meta charset="UTF-8">                                                 
      <style>                                                                
          * {{ margin: 0; padding: 0; box-sizing: border-box; }}             
          body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
   Roboto, Arial, sans-serif; background: white; padding: 40px; }}           
          .container {{ max-width: 1000px; margin: 0 auto; }}                
          .header {{ margin-bottom: 30px; }}                                 
          h1 {{ font-size: 32px; font-weight: 600; color: #1a1a1a;           
  margin-bottom: 8px; }}                                                     
          .timestamp {{ font-size: 14px; color: #666666; }}                  
          table {{ width: 100%; border-collapse: collapse; background: white;
   box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow:      
  hidden; }}                                                                 
          th {{ background: #f8f9fa; padding: 16px; text-align: left;        
  font-weight: 600; font-size: 14px; color: #495057; text-transform:         
  uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #dee2e6; }}     
          td {{ padding: 16px; border-bottom: 1px solid #f0f0f0; font-size:  
  15px; }}                                                                   
          tr:last-child td {{ border-bottom: none; }}                        
          tr:hover {{ background: #f8f9fa; }}                                
          .index-name {{ font-weight: 600; color: #1a1a1a; }}                
          .value {{ color: #495057; text-align: right; }}                    
          .change {{ text-align: right; font-weight: 500; }}                 
          th:nth-child(1), td:nth-child(1) {{ text-align: left; }}           
      </style>                                                               
  </head>                                                                    
  <body>                                                                     
      <div class="container">                                                
          <div class="header">                                               
              <h1>{"Asiatische Indizes" if lang == "de" else "Asian          
  Indices"}</h1>                                                             
              <div class="timestamp">{timestamp}</div>                       
          </div>                                                             
          <table>                                                            
              <thead><tr>{headers_html}</tr></thead>                         
              <tbody>{rows_html}</tbody>                                     
          </table>                                                           
      </div>                                                                 
  </body>                                                                    
  </html>"""                                                                 
                                                                             
  def generate_image(html_content, output_path):                             
      with sync_playwright() as p:                                           
          browser = p.chromium.launch()                                      
          page = browser.new_page(viewport={"width": 1200, "height": 800})   
          page.set_content(html_content)                                     
          page.wait_for_timeout(1000)                                        
          page.screenshot(path=output_path, full_page=True, scale="device")  
          browser.close()                                                    
                                                                             
  def main():                                                                
      print("Fetching indices data...")                                      
      data = fetch_indices_data()                                            
      print("Generating German version...")                                  
      generate_image(generate_html(data, "de"), "indices_de.png")            
      print("Generating English version...")                                 
      generate_image(generate_html(data, "en"), "indices_en.png")            
      print("Done!")                                                         
                                                                             
  if __name__ == "__main__":                                                 
      main()                        
