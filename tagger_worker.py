import vertexai, pymongo
from datetime import datetime
from vertexai.language_models import TextGenerationModel
from google.api_core.exceptions import InvalidArgument
from urllib.parse import quote_plus
import dotenv
import os
import json
import sys
import time

dotenv.load_dotenv()

MONGO_USER_NAME=os.getenv('MONGO_USER_NAME')
MONGO_USER_PWD=os.getenv('MONGO_USER_PWD')
GCLOUD_PROJECT = os.getenv('PROJECT_NAME')

uri = f'mongodb+srv://{MONGO_USER_NAME}:{quote_plus(MONGO_USER_PWD)}@cluster0.otdmcnh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = pymongo.MongoClient(uri)
db = client.Resource.raw

def get_build_context(prompt):
    vertexai.init(project=GCLOUD_PROJECT, location="asia-southeast1")
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 4000,
        "temperature": 0.8,
        "top_p": 1
    }
    model = TextGenerationModel.from_pretrained("text-bison-32k@002")
    response = model.predict(
        prompt,
        **parameters
    )
    return response.text.replace("```html","").replace("```","")

def gen_tagger(data):
    return get_build_context(f"""
            what are the legal propositions from the text {data}?
    """)


completed = open(sys.argv[1], 'a')
start = int(sys.argv[2]) if len(sys.argv) >= 3 else 0 

def read_prev_log():
    entries = []
    lines = open(sys.argv[1], 'r').read().splitlines()
    for line in lines:
        if line.strip() == '': continue
        entries.append(json.loads(line))
    return entries

def get_set(entries, type: str) -> list[str]:
    return list(map(lambda e: e[1], filter(lambda e: e[0] == type, entries)))

def tagger(limit: int = -1, start: int = 0):
    prev_entries = read_prev_log()
    erred_entries = get_set(prev_entries, 'ERR')
    print(erred_entries)
    query = {'$or': [{'tags': {'$eq': []}}, {'tags': {'$exists': False}}, {'tags': {'$eq': ''}}, {'tags': {'$eq': 'NA'}}, {'tags': {'$eq': 'Not available'}}]}
    t1 = datetime.now()
    x = 0
    num_erred, num_failed, num_completed = len(erred_entries), 0, 0
    last = ''
    while limit == -1 or x < limit:
        case = [y for y in db.find(query).skip(start + num_erred + num_failed).limit(1)][0]
        if str(case['_id']) == last:
            # num_erred += 1
            continue
        last = ''
        try:
            tags = gen_tagger(case['judgement'])
        except InvalidArgument as e:
            print(e)
            status = 'ERR'
            num_erred += 1
        except Exception as e:
            print('Encountered err.. going to sleep...', e)
            time.sleep(30)
            status = 'TIMEOUT'
            continue
        else:
            res = db.update_one({"uniquelink": case['uniquelink']},{"$set": {"tags": tags}})
            if res.modified_count == res.matched_count:
                last = str(case['_id'])
                status = 'OK'
                num_completed += 1
            else:
                status = 'FAIL'
                num_failed += 1
        entry = (status, str(case['_id']), case['uniquelink'])
        print(x, entry)
        estr = json.dumps(entry)
        completed.write(f"{estr}\n")
        x += 1
    t2 = datetime.now()
    print(t2-t1, (t2-t1)/5)
    print (f"ok: {num_completed}, failed: {num_failed}, err: {num_erred}")

try:
    tagger(start=start)
except Exception as e:
    print(e)
completed.close()
