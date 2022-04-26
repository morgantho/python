#!/usr/bin/env python3
import requests, json
from bs4 import BeautifulSoup

file = 'sample.json'

with open(file) as f: 
    data = json.load(f)

def get_entry(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    if 'tumblr' in url:
        txt = soup.find("div", class_="body-text").get_text()
        #print(txt)
        return txt

    elif 'blogspot' in url:
        txt = soup.find("div", class_="post-body").get_text()
        #print(txt)
        return txt


def wyas_extract(data):
    dt = dict()
    id_date = data['id']
    wyas = data['wyasLink'][0]
    dt['date'] = id_date.replace(',','-')
    dt['wyas_link'] = wyas['link']
    dt['type'] = wyas['type']
    return dt

def tr_extract(data):
    dt = dict()
    dt['link'] = data['link'][0]
    dt['credit'] = data['credit']
    dt['type'] = data['type']
    return dt

for d in data:
    w = wyas_extract(d)
    if 'AW' in w.get('type'):
        print("AW JOURNAL WYAS")
        break
    print(w.get('date'))

    for x in d['Tr']:
        t = tr_extract(x)
        print(t.get('credit'))
        if t.get('credit') == 'ISAW':
            print("AW JOURNAL INFO TR")
            break
        elif "insearchofannwalker.com" in t.get('link'):
            print("AW JOURNAL INFO")
            break
        body = get_entry(t.get('link'))
        body = body.replace('\n', '')
        entry = body


    es = {'date': w.get('date'), 'WYAS': w.get('wyas_link'), 'credit': t.get('credit'), 'type': t.get('type'), 'entry': entry }
    es_json = json.dumps(es)
    print("PRINTING ES STUFF-----------")
    print(es_json)