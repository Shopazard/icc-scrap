import csv, sys, traceback
from bs4 import BeautifulSoup as bs
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
import requests, time
import random
from user_agent import generate_user_agent



def remove_digits(text):
  result = ""
  for char in text:
    if not char.isdigit():
      result += char
  return result
def get_links():
    with open('acts.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) > 1:
                yield row[1]

def fetch_website(url, user_agent=None, timeout=None):

    user_agent  = generate_user_agent()
    try:
        headers = {'User-Agent': user_agent} if user_agent else {}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status() 

        return response.status_code, response.content

    except requests.exceptions.RequestException as e:
        print(f"Error fetching website: {e}", end="\r")
        return None, None
    
def converter(day, month, year):
    month_int = datetime.strptime(month, "%B").month
    date_object = date(int(year), month_int, int(day))
    return date_object
    

def create_law(akoma_ntoso):

    coverage = akoma_ntoso.find('div', class_='coverpage')
    title = coverage.find('h1').text.replace("\n"," ").strip()
    place = coverage.find('div', class_='place-name').text.replace("\n","").strip()
    act_no = coverage.find('h2').text.replace("\n"," ").strip()
    coverageul = akoma_ntoso.find('ul')
    _,_,day,month,year = coverageul.find('li', class_='commencement-date').text.split()
    pdate = converter(day, month, year)
    preface = akoma_ntoso.find('section', class_='akn-preface')
    desc = str(coverageul) + str(preface)
    payload = {
        "name": title, 
        "place": place,
        "description": str(desc),
        "publish_date": str(pdate),
        "act_no": act_no,
        "created_by": "john-doe-GXXVD"
    }
    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImpvaG4tZG9lLUdYWFZEIn0.FwcFdJoJoawXmQnMIWRv2H-14rWh_GG0YZ0sCDK-EMM'
    }
    url = "https://supaback-dev-2-dot-tensile-splice-408105.el.r.appspot.com/law/"
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        data = response.json()
        ul = data['uniquelink']
        name = data['name']
        print(f"Law created: {name} - {ul}")
        return ul, name
    else:
        print(f"Error creating law: {response.status_code} - {response.text}")
        return None



def create_chapter(name, act, act_ul):
    url = "https://supaback-dev-2-dot-tensile-splice-408105.el.r.appspot.com/law/chapter"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImpvaG4tZG9lLUdYWFZEIn0.FwcFdJoJoawXmQnMIWRv2H-14rWh_GG0YZ0sCDK-EMM'
        }
    payload = {
        "name": name,
        "bare_act_law": act,
        "bare_act_law_ul": act_ul,
        "created_by": "john-doe-GXXVD"
        }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        data = response.json()
        ul = data['uniquelink']
        name = data['name']
        print(f"Chapter created: {name} - {ul}")
        return ul, name
    else:
        print(f"Error creating law: {response.status_code} - {response.text}")
        return None



def create_section(sections, chap, chap_name, law, law_ul):

    print(f"Found {len(sections)} sections", end="\r")
    for index,section in enumerate(sections):
        if not section:
            continue
        if section['class'][0] == "akn-chapter":
            name = section.find('h2').text.replace("\n","  ").strip().replace("Chapter ","").strip()
            name = remove_digits(name)
            act = law
            act_ul = law_ul
            chap, chap_name = create_chapter(name, act, act_ul)
            create_section(section.find_all('section', class_=["akn-section"]), chap, chap_name, law, law_ul)
            continue

        if section['class'][0] == "akn-section":
            sec_name_tag = section.find('h3')
            if sec_name_tag:
                try:
                    sec_link = sec_name_tag.find('a')
                except:
                    traceback.print_exc()
                    print(section)
                    sys.exit()
                if sec_link: sec_link.decompose()
                sec_name = sec_name_tag.text.replace("\n"," ").strip()
                sec_name_tag.decompose()
            else:
                sec_name = ""
            url = "https://supaback-dev-2-dot-tensile-splice-408105.el.r.appspot.com/law/sections"

            payload = {
            "name": sec_name,
            "bare_act_law": law,
            "bare_act_law_ul": law_ul,
            "bare_act_chapter": chap_name,
            "bare_act_chapter_ul": chap,
            "text": str(section),
            "created_by": "john-doe-GXXVD"
            }
            headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImpvaG4tZG9lLUdYWFZEIn0.FwcFdJoJoawXmQnMIWRv2H-14rWh_GG0YZ0sCDK-EMM'
            }
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 201:
                data = response.json()
                name = data['name']
                print(f"{index} New section added: {name}, chapter: {chap_name}, law: {law}", end="\r")
            else:
                print(f"{index} Error creating law: {response.status_code} - {response.text}")
    





def fetch_akoma_ntoso(html):

    soup = bs(html,features="html.parser")
    akoma_ntoso = soup.find('div', class_='akoma-ntoso')
    ul, name = create_law(akoma_ntoso=akoma_ntoso)
    cul, cname = create_chapter(name="unnamed", act=name, act_ul=ul)
    body = akoma_ntoso.find('span', class_='akn-body')
    sections = body.find_all('section', class_=["akn-chapter", "akn-section"])
    create_section(sections, cul, cname, name, ul)

def main_ops(link):
    x,y = fetch_website(link)
    if not y:
        print("this is not a valid link",link)
        return
    fetch_akoma_ntoso(y)

def get_paginated_links(act_type, year):

    all_case_links = []
    for page in range(18):
        _, y = fetch_website(f"https://indiankanoon.org/search/?formInput=doctypes:{act_type}%20fromdate:1-1-{str(year)}%20todate:%2031-12-{str(year)}{'&pagenum='+str(page) if page> 0 else ''}")
        if not y: 
            print(f"Error fetching {act_type} {year} {page}")
            break
        print(f"Scraping {act_type} {year} {page}", end="\r")
        soup = bs(y,features="html.parser")
        div_links = soup.find_all('div', class_ = "result_title")
        if not div_links: break
        case_links = ["https://indiankanoon.org"+p.find('a')['href'] for p in div_links]
        print(f"Found {len(case_links)} cases", end="\r")
        all_case_links.extend(case_links)
    return all_case_links

def get_years_and_acts(link):
    time.sleep(10)
    _,_,act_type,_ = link['href'].split("/")
    ref = "https://indiankanoon.org"+link['href']
    _, new_y = fetch_website(ref)
    new_soup = bs(new_y,features="html.parser")
    new_table = new_soup.find('table')
    new_links = new_table.find_all('a')
    all_acts = []
    all_years = []
    all_links = []
    for nl in new_links[::-1]:
        _,_,act_type,year,_ = nl['href'].split("/")
        all_acts.append((act_type))
        all_years.append((year))
        pg_links = get_paginated_links(act_type, year)
        all_links.extend(pg_links)
    return all_links


def get_all_links():
    _, y = fetch_website("https://indiankanoon.org/browselaws/")
    soup = bs(y,features="html.parser")
    table = soup.find('table')
    links = table.find_all('a')
    results = []
    for index, link in enumerate(links):
        if index == 1: continue
        results.extend(get_years_and_acts(link))
    print(results[:3], type(results), len(results))
    return results



if __name__ == "__main__":
    links = get_all_links()
    with ThreadPoolExecutor() as executor:
        results = executor.map(main_ops, links)
    list(results)