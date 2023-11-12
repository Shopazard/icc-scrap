#!/Users/aritrog/Documents/chatpe/Misc Code/pdfenv/bin/python
import sys
from bs4 import BeautifulSoup as bs

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter

def html_parser(html):

    soup = bs(html, 'html.parser')
    for p in soup.find_all('p'):
        text = p.get_text()
        if 'Shashank' in text or 'All India Reporter' in text or '© Copyright' in text or '@page' in text or 'Annotation' in text or 'Para' in text:
            p.decompose()
    for i, span in enumerate(soup.find_all('span')):
        if i == 0:
            span['text'] = '1111'
            span['style'] = 'font-size:18px;font-weight:700;margin:10px;margin-bottom:16px'
        if i == 1:
            span['style'] = 'font-size:14px;font-weight:600;margin-bottom:20px'
        if i == 2:
            span['style'] = 'font-size:13px;font-weight:600'
    return str(soup)

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
    # with open('air2.html', 'w', encoding='utf-8') as new_f:
    #     new_f.write(html_parser(html))
    return html_parser(html)

from flask import Flask, request
app = Flask(__name__)


@app.route("/pdf", methods=['POST'])
def handle_pdf():
    if request.method == 'POST':
        file = request.files['file']
        return {"html": gen_html_string(file)}
    return {"error": "Wrong Method"}


if __name__ == '__main__': 
    app.run(debug=True)
