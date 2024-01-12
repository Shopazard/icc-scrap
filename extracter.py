from wsgi import gen_html_string
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta, date
from vertexai.language_models import CodeGenerationModel
from json import JSONDecodeError
import os, threading, queue, traceback, csv
import vertexai, json, re, random, string, pymongo



def get_all_files():
    print("Walking through Files")
    all_files = []
    for dirname, _, filenames in os.walk('./cases/'):
        for filename in filenames:
            all_files.append(os.path.join(dirname, filename))
    print(f"Total Files Found: {len(all_files)}")
    return all_files

def get_html_from_pdf_file(filepath,queue):
    html = ""
    try:
        with open(filepath, 'rb') as fp:
            tt1 = datetime.now()
            html = gen_html_string(fp=fp)
            head = html_head_extracter(html['html'])
            tt2 = datetime.now()
            queue.put(({'filename':filepath,**head}, tt2-tt1))
            return {'filename':filepath,**head}
    except Exception as e:
        # traceback.print_exc()
        print(f"File corrupted {filepath}, -- {str(e)}")
        return None
    

def html_head_extracter(html):

    soup = bs(html,features="html.parser")

    f10 = soup.find_all('span')[:10]
    l1 = soup.find_all('span')[-1:]
    f10.extend(l1)
    text_array = []
    if f10:
        for x in f10:
            length = len(x.get_text().split())
            if length <  30 and length > 1:
                text_array.append(x.get_text().replace("\n"," ").replace(","," "))

    head = "_:::_".join([x for x in text_array])
    infos = vertex_extracter(head)
    infos['name'] = infos.pop('case_name')
    infos['decision'] = infos.pop('order')
    date = infos.pop('date')
    infos['end_date'] = date(date['day'], date['month'],date['year'])
    infos['judgement_status']= "upheld"
    infos['judgement'] = html
    p = re.compile("[^a-zA-Z0-9 -]")
    ul = "-".join(p.sub(" ",infos['name'].lower()).split())
    strn = string.ascii_uppercase
    flux = ''.join(random.choice(strn) for i in range(5))
    infos['uniquelink'] = ul+"-"+flux
    infos['created_by'] = 'system-ai'
    infos['created_at'] = datetime.now()

    return infos


def vertex_extracter(headnote):

    schema_op = {
        "properties" : {
            "case_name": {"type":"string"},
            "complaining_party" : {"type":"string"},
            "complaining_party_type" : {
                "type":"string",
                "enum": ["plaintiff", "petitioner", "applicant", "complainant", "appellant", "plaintiff & another", "plaintiff & others", "petitioner & another", "petitioner & others", "applicant & another", "applicant & others", "complainant & another", "complainant & others","appellant & another", "appellant & others"],
                },
            "defending_party" : {"type":"string"},
            "defending_party_type" : {
                "type":"string",
                "enum": ["defendant", "respondent", "opposite party", "accused", "defendant & another", "defendant & others", "respondent & another", "respondent & others", "opposite party & another", "opposite party & others"],
                },
            "judges": {
                "type" : "array",
                "items": "string"
            },
            "court" : "string",
            "date" : {
                "type":"object",
                "properties":{
                    "day": "integer",
                    "month": "integer",
                    "year": "interger"
                }
            },
            "order": {"type":"string"}
        }
    }

    vertexai.init(project="tensile-splice-408105", location="us-central1")
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 1024,
        "temperature": 0.9
    }
    model = CodeGenerationModel.from_pretrained("code-bison")
    response = model.predict(
        prefix = f"""
                consider this legal headnote {headnote} and provide the following case information as required in the following schema {schema_op} in json format.
            """,
        **parameters
    )
    res = response.text.replace("`json","").replace("`","").replace("\'",'"').strip()
    start_index = res.find("{")
    end_index = res.rfind("}")
    try:
        res = res[start_index:end_index+1]
        new_res = json.loads(res)
    except JSONDecodeError:
        res2 = res[:-1].strip().rstrip(",") + "}"
        try:
            new_res = json.loads(res2)
        except Exception as e:
            traceback.print_exc()
            print(res2)
    return new_res

def manager():
    t1 = datetime.now()
    files = get_all_files()


    ## threading the pdf_to_html_conversion
    q = queue.Queue()
    
    threads = []
    for i,file in enumerate(files):
        print(f'Processing {i}/{len(files)} -- File: "{file}"', end="\r")
        thread = threading.Thread(target=get_html_from_pdf_file, args=(file,q), daemon=True)
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    print()
    t2 = datetime.now()
    html_extracts = []
    count = 1
    time_deltas = []
    while not q.empty():
        html_details, time_delta = q.get()
        count += 1
        time_deltas.append(time_delta)
        if html_details: html_extracts.append(html_details)
    
    client = pymongo.MongoClient("mongodb+srv://icc:12345@cluster0.tkzctxd.mongodb.net/?retryWrites=true&w=majority")
    db = client.Resource.raw
    inserted = db.insert_many(html_extracts)
    print(inserted.inserted_ids)
    timesum = sum(time_deltas, timedelta())

    print("Total files extracted:",len(html_extracts))
    print(f'Total Time: {datetime.now() - t1}, Total Operations Time: {timesum}, Average case time: {timesum/count}, Threaded operation Time: {t2- t1}')
    
    
def to_csv(html_extracts):
    with open('pdf_heads.csv','w') as fp:
        csvd = csv.writer(fp)
        csvd.writerow(['filename','head','name','day','month','year','complaining_party', 'defending_party','judges','court','order'])
        csvd.writerows(html_extracts)


manager()



def head_to_info(text_array):
    head = "_:::_".join([x for x in text_array])
    order = text_array[-1]
    name = ''
    complaining_party = ''
    defending_party = ''
    judges = ''
    day = ''
    month = ''
    year = ''
    for sentence in text_array:
        if "v." in sentence: 
            name = sentence
            complaining_party, defending_party = name.split('v.') 
        if "d/-" in sentence.lower():
            date_blob = sentence[sentence.lower().find('d/-')+2:]
            try:
                day, month, year = [int(x) for x in date_blob[2:].replace("-"," ").replace("*","").replace(".","").replace("("," ").split(" ") if x.isdigit()]
            except: 
                print(sentence)
    return [head,name, day, month, year, complaining_party, defending_party, '','',order]