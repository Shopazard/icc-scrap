import pymongo
client = pymongo.MongoClient("mongodb+srv://icc:12345@cluster0.tkzctxd.mongodb.net/?retryWrites=true&w=majority")
db = client.Resource.raw

inserted = db.update_many({"synopsis":{"$exists":False}},{"$set":{
    "law_name":   '',
    "law_ul":   '',
    "section_name":   '',
    "section_ul":   '',
    "clause":   '',
    "share_count":  0,
    "bookmark_count":  0,
    "case_strength": 0,
    "citings": [],
    "citings_count": 0,
    "cited": [],
    "cited_count": 0,
    "landmark": False,
    "synopsis":   "NA",
    "court_copy":   "NA",
    "air_journal_copy":   "NA",
    "scc_journal_copy":  "NA",
    "tags": []
}})

db.create_index([("name", pymongo.TEXT),("judgement", pymongo.TEXT),("court", pymongo.TEXT),("law_name", pymongo.TEXT),("synopsis", pymongo.TEXT)], default_language="english")

print("Indexes copied successfully!")

print(inserted.modified_count)