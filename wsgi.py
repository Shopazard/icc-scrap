#!/Users/aritrog/Documents/chatpe/Misc Code/pdfenv/bin/python
import json
from bs4 import BeautifulSoup as bs
from flask_cors import CORS
import openai

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter




FUNCTIONS = [
            {
                "name": "find_case_details",
                "description": "this functions takes various case details like date, court, judge, partiesjudgement decision, etc",
                "parameters": {
                        "type": "object",
                        "properties": {
                            "case_name": {
                                "type": "string",
                                "description": "takes the name of the case",
                            },
                            "court_name": {
                                "type": "string",
                                "description": "takes the name of the court",
                            },
                            "case_number": {
                                "type": "string",
                                "description": "takes the number of the case",
                            },
                            "judges": {
                                "type": "string",
                                "description": "takes the name of the judges",
                            },
                            "complaining_party": {
                                "type": "string",
                                "description": "takes the name of the complaining party",
                            },
                            "defending_party": {
                                "type": "string",
                                "description": "takes the name of the defending party",
                            },
                            "complaining_party_type": {
                                "type": "string",
                                "enum": ["plaintiff", "petitioner", "applicant", "complainant", "appellant", "plaintiff & another", "plaintiff & others", "petitioner & another", "petitioner & others", "applicant & another", "applicant & others", "complainant & another", "complainant & others","appellant & another", "appellant & others"],
                                "description": "takes the type of the complaining party",
                            },
                            "defending_party_type": {
                                "type": "string",
                                "enum": ["defendant", "respondent", "opposite party", "accused", "defendant & another", "defendant & others", "respondent & another", "respondent & others", "opposite party & another", "opposite party & others"],
                                "description": "takes the type of the defending party",
                            },
                            "date": {
                                "type":"string",
                                "description": "case date in 'dd-mm-yyyy' format"
                            },
                            "judgement_decision": {
                                "type":"string",
                                "enum": ["Petition Allowed","Petition Partly Allowed","Petition Dismissed","Case Remanded","Appeal Allowed","Appeal Partly Allowed","Appeal Dismissed","Order Accordingly","Application Allowed","Application Partly Allowed","Application Dismissed"],
                                "description": "case decision"
                            }
                        },
                        "required": ["case_name","court_name","case_number", "judges", "complaining_party", "complaining_party_type", "judgement_decision", "date"],
                    },

            }
        ]


def datafinder(data):
    messages = [{"role":"system","content":"you are lela a indian lawyer's assistant, your job is to look at a given set of text and determine various details for a given judgement"},{"role": "user", "content": "Please read the following text "+data}]
    openai.api_key = "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"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages,
        functions=FUNCTIONS,
        function_call="auto",
        temperature=0.9,
    )
    args = json.loads(response['choices'][0]['message']['function_call']['arguments'])

    return args




def html_parser(html):

    soup = bs(html, 'html.parser')
    for p in soup.find_all('p'):
        text = p.get_text()
        if 'Shashank' in text or 'All India Reporter' in text or '© Copyright' in text or 'Annotation' in text or 'Para' in text:
            p.decompose()
    for p in soup.find_all('p', {'style': lambda s: 'text-align:right' in s}):
        if '@page' in p.get_text() or p.get_text().replace("\n","").isdigit():
            p.decompose()
    for p in soup.find_all('span', {'style': lambda s: 'font-size:10px' in s}):
        p.decompose()
    for p in soup.find_all('p', {'style': lambda s: 'font-size:10px' in s}):
        p.decompose()
    for i, span in enumerate(soup.find_all('span')[:4]):
        if i == 0:
            span['text'] = '1111'
            span['style'] = 'font-size:18px;font-weight:700;margin:10px;margin-bottom:16px'
        if i == 1:
            span['style'] = 'font-size:14px;font-weight:600;margin-bottom:20px'
        if i == 2:
            span['style'] = 'font-size:13px;font-weight:600'
    ##for data 
    text = ''
    for span in soup.find_all('span')[:10]:
        text += span.get_text()
    for span in soup.find_all('span')[-5:]:
        text += span.get_text()
    return str(soup), text

def gen_html_string(fp):

    laparams = LAParams()
    # outfp = open('air.html', 'w', encoding='utf-8')
    rsrcmgr = PDFResourceManager(caching=False)
    device = HTMLConverter(rsrcmgr, None, scale=1,
                               layoutmode='normal', laparams=laparams,
                               imagewriter=None, debug=0)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(fp, set(),
                                    maxpages=0, password=b'',
                                    caching=False, check_extractable=True):
        page.rotate = (page.rotate) % 360
        interpreter.process_page(page)
    html = device.html
    device.close()
    parsed_html, text = html_parser(html)
    # data = datafinder(text)
    # with open('air2.html', 'w', encoding='utf-8') as new_f:
    #   new_f.write(parsed_html)

    # if data:
    #     return {"html":parsed_html}
    return {"html":parsed_html}

from flask import Flask, request
app = Flask(__name__)
CORS(app)

@app.route("/pdf", methods=['POST'])
def handle_pdf():
    if request.method == 'POST':
        file = request.files['file']
        return gen_html_string(file)
    return {"error": "Wrong Method"}


if __name__ == '__main__': 
    # app.run(debug=True, host='0.0.0.0', port=9080)
    app.run()
