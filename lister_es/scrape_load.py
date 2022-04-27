#!/usr/bin/env python3
#pip install elasticsearch==7.13.0 elasticsearch-dsl
import requests, json, argparse, elasticsearch, re, os, sys
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch

output = 'completed.txt'

parser = argparse.ArgumentParser()
parser.add_argument('--file', required=True)
parser.add_argument('--start', required=True, help="Year-Month to read from file", metavar="1834-01")
parser.add_argument('--end', required=True, help="Year-Month to stop at", metavar="1834-02")
args = parser.parse_args()

# open data file
with open(args.file) as f: 
    data = json.load(f)

def get_entry(url):
    '''Get entry text from url'''

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    if 'tumblr' in url:
        try:
            txt = soup.find("div", class_="body-text").get_text()
            return txt
        except:
            u = url
        
            if 'tumblr' in u:
                try:
                    txt = soup.find("article", class_="text").get_text()
                    return txt
                except:
                    u2 = u
                
                    if 'tumblr' in u2:
                        try:
                            txt =soup.find("div", class_="template-post-content-body").get_text() 
                            return txt
                        except:
                            print(f'ERROR_URL: {url}')

    if 'blogspot' in url:
        try:
            txt = soup.find("div", class_="post-body").get_text()
            return txt
        except:
            print(f'ERROR_URL: {url}')
        

def wyas_extract(data):
    '''Extract WYAS list data from file'''

    dt = dict()
    id_date = data['id']
    wyas = data['wyasLink'][0]
    dt['date'] = id_date.replace(',','-')
    dt['wyas_link'] = wyas['link']
    dt['type'] = wyas['type']
    return dt

def tr_extract(data):
    '''Extract TR list data from file'''

    dt = dict()
    dt['link'] = data['link'][0]
    dt['credit'] = data['credit']
    dt['type'] = data['type']
    return dt

def es_connect():
    '''Connect to Bonsai Elasticsearch'''

    print("Connecting to Bonsai")
    bonsai = os.environ['BONSAI_URL']
    auth = re.search('https\:\/\/(.*)\@', bonsai).group(1).split(':')
    host = bonsai.replace(f'https://%s:%s@' % (auth[0], auth[1]), '')
    port=443

    # Connect to cluster over SSL using auth for best security:
    es_header = [{
        'host': host,
        'port': port,
        'use_ssl': True,
        'http_auth': (auth[0],auth[1])
    }]

    # Instantiate the new Elasticsearch connection:
    es = Elasticsearch(es_header)
    return es

def es_push(es_obj,id,record):
    '''Push to Elasticsearch index'''

    try:
        outcome = es_obj.index(index="lister", id=id, body=record)
    except Exception as ex:
        print('Error in indexing data')
        print(str(ex))
   
def extract_push(es_obj):
    count = 0
    
    for d in data:
        w = wyas_extract(d)
        date = w.get('date')
    
        if args.start in date:

            for x in d['Tr']:
                if x['link']:
                    t = tr_extract(x)
                    count += 1
                    
                    # skipping these sources as the formatting is difficult to work with
                    if t.get('credit') == 'ISAW':
                        break
                    elif "insearchofannwalker.com" in t.get('link'):
                        break
                    elif "drive.google.com" in t.get('link'):
                        break
                    elif "annelisternorway.com" in t.get('link'):
                        break

                    body = get_entry(t.get('link'))
                    entry = body.replace('\n', ' ').replace('\t', '').replace('\r', '').encode("ascii", "ignore").decode()

                    es_doc = {'date': w.get('date'), 'WYAS': w.get('wyas_link'), 'credit': t.get('credit'), 'type': t.get('type'), 'entry': entry, 'transcript': t.get('link') }
                    es_json = json.dumps(es_doc)
            
                    id = f'{date}.{count}'
                    print(f"ES PUSH FOR {id}" )
                    #print(es_json)
                    es_push(es_obj,id,es_json)
    
        elif args.end in date:
            with open(output, 'a') as o:
                o.write(f'\nCompleted up to {date}')
            sys.exit(f'Stopping at {args.end}')


def main():
    es = es_connect()
    extract_push(es)

if __name__ == "__main__":
    main()