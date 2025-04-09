from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np  
import re
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import math

def get_page_content(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(executable_path=r"/usr/local/bin/chromedriver")
    # D:\Pythons\Python3.12\Lib\site-packages\selenium\webdriver\chrome\chromedriver.exe
    # /usr/local/bin/chromedriver
    driver = webdriver.Chrome(service=service, options=options)
    try:
        # Navigate to the URL
        driver.get(url)
        # Wait for the page to load (adjust timeout as needed)
        time.sleep(2)
        # Get the page source
        html_content = driver.page_source
        return html_content
    
    finally:
        # Always close the browser
        driver.quit()
def clean_string(text):
    text = text.replace("\r\n", "\n")  # Replace \r\n with \n
    text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines with a single \n
    text = re.sub(r' +', ' ', text)  # Replace multiple spaces with a single space
    text = "\n".join(line.strip() for line in text.split("\n"))  # Trim spaces around each line
    return text.strip()  # Trim leading/trailing spaces and newlines

def load_existing_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

output_file1 = "thutuhanhchinh.json"
output_file2 = "thutuhanhchinh_error.json"
final_data = load_existing_data(output_file1)
existing_ids = {item["id"] for item in final_data}
final_error = load_existing_data(output_file2)
existing_error_ids = {item['id'] for item in final_error}
url = "https://dichvucong.gov.vn/jsp/rest.jsp"

# Headers
headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "route=1744179329.146.219.582752; JSESSIONID=8643D1A3A83A10857B9CD150BDBD985C; TS0115bee1=01f551f5eeb5ba3a9e37e234391d23b714ea3eb694df7bee626ca7b9682764c1136a0cf1b243369321faf85d5e630e01c54fcc0a8f8fa498f17938cea992b3e14ead2009f1; TSdcf68b45027=085b7f7344ab200039e1a0cb9e86097e452bdad1b0be1dc1044139611cd9069bc6603f6d19ccfa0d0834885552113000969e3fca3420f7712f99fffe247ad422e1be7fc03f7cd605e3c3899e1ba58291163a9198b7fa538550090b517fc4e72b",
    "Origin": "https://dichvucong.gov.vn",
    "Referer": "https://dichvucong.gov.vn/p/home/dvc-tthc-thu-tuc-hanh-chinh.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"'
}

# Data
data = {
    "params": '{"service":"procedure_get_new_procs_service_v2","provider":"dvcquocgia","type":"ref","is_connected":0,"records":10000}'
}

# Make the POST request
response = requests.post(url, headers=headers, data=data)

try:
    json_responses = response.json()
    print(len(json_responses))
    for json_response in json_responses:
        procedure_name = json_response["PROCEDURE_NAME"]
        ID = json_response["ID"]
        if ID in existing_ids:
            print(f"Skipping existing procedure: {ID}")
            continue
        try:
            html_content = get_page_content(f"https://dichvucong.gov.vn/p/home/dvc-tthc-thu-tuc-hanh-chinh-chi-tiet.html?ma_thu_tuc={ID}")
            soup = BeautifulSoup(html_content, 'html.parser')
            form_divs = soup.find_all('span', class_='link')
            forms = []
            for form_div in form_divs:
                onclick_value = form_div.get('onclick')
                if onclick_value and 'downloadMaudon' in onclick_value:
                    value = onclick_value.split("'")[1]
                    text_content = form_div.get_text(strip=True)
                    data = {
                            "title": text_content,
                            "url": f"https://csdl.dichvucong.gov.vn/web/jsp/download_file.jsp?ma={value}",
                    }
                    forms.append(data)
            input_data = {
                "id": ID,
                "title": procedure_name,
                "forms": forms,
            }
            print(input_data)
            final_data.append(input_data)
            save_data(output_file1, final_data)
        except Exception as e:
            print(f"Error processing ID {ID}: {e}")
            error_data = {
                "id": ID,
                "title": procedure_name,
                "error": str(e),
            }
            final_error.append(error_data)
            save_data(output_file2, final_error)
except Exception as e:
    print("Response is not in JSON format")