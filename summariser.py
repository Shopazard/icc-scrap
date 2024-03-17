import vertexai, pymongo
from datetime import datetime
from vertexai.language_models import TextGenerationModel
from google.api_core.exceptions import InvalidArgument
GCLOUD_PROJECT = "tensile-splice-408105"

client = pymongo.MongoClient("mongodb+srv://icc:12345@cluster0.tkzctxd.mongodb.net/?retryWrites=true&w=majority")
db = client.Resource.raw



def get_build_context(data):

    vertexai.init(project=GCLOUD_PROJECT, location="asia-southeast1")
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 4000,
        "temperature": 0.8,
        "top_p": 1
    }
    model = TextGenerationModel.from_pretrained("text-bison-32k@002")
    response = model.predict(
        f"""
            Summarise the following legal text {data}, Create a list of tags for legal concepts from the text
        """,
        **parameters
    )
    return response.text.replace("```html","").replace("```","")


t1 = datetime.now()
for x in range(1):
    case = [y for y in db.find({}).skip(x).limit(1)][0]
    try:
        tags = get_build_context(case['judgement'])
    except InvalidArgument as e:
        continue
    print(list(tags.replace("\n","").strip().split("-"))[1:])

    # xx = db.find_one_and_update({"uniquelink": case['uniquelink']},{"$set": {"tags": tags}})
    print(x, case['name'], "Completed", end="\r")
t2 = datetime.now()
print(t2-t1, (t2-t1)/5)
