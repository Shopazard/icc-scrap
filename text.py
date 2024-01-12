from pymongo import MongoClient
from bs4 import BeautifulSoup as bs
import csv
client = MongoClient("mongodb+srv://icc:12345@cluster0.tkzctxd.mongodb.net/?retryWrites=true&w=majority")
jdb = client.Resource.judgements
count = jdb.count_documents({})
print(count)



def soupify(text: str):
  soup = bs(text,features="html.parser")
  f10 = soup.find_all('span')[:10]
  l1 = soup.find_all('span')[-1:]
  f10.extend(l1)
  text_array = []
  if f10:
    for x in f10:
        length = len(x.get_text().split())
        if length <  30 and length > 1:
            text_array.append(x.get_text().replace("\n"," ").replace(","," "))

  text_array = "_:::_".join([x for x in text_array])
  return text_array

LIMIT = 3727
SKIP = 5273


with open(f'icc_{SKIP}_to_{SKIP+LIMIT}.csv', 'w', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)  
    fields = ['text','name', 'complaining_party', 'complaining_party_type', 'defending_party', 'defending_party_type', 'judges','court','end_date', 'decision','judgement_status']
    csvwriter.writerow(fields)  
    for i,x in enumerate(jdb.find({}).skip(SKIP).limit(LIMIT)): 
        print(f'{SKIP + i} of {SKIP + LIMIT}',end='\r')
        if 'judgement' in x and x['judgement']:
            extract = soupify(x['judgement'])
            if extract:
                soups_10 = [extract, 
                            x['name'].strip(), 
                            x['complaining_party'].strip(),
                            x['complaining_party_type'].strip(),
                            x['defending_party'].strip() if x['defending_party'] else 'null/none' ,
                            x['defending_party_type'].strip() if x['defending_party_type'] else 'null/none',
                            "|".join(p.strip() for p in x['judges']),
                            x['court'].strip(),
                            str(x['end_date']).strip(),
                            x['decision'].strip(),
                            x['judgement_status'].strip()] 
                csvwriter.writerow(soups_10)


