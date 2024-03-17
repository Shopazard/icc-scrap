from flask import Flask, request, render_template, send_from_directory
import requests
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "./"  # Replace with your download folder

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        pdf_link = request.form.get("pdf_link")
        try:
            # Download PDF using built-in requests library
            response = requests.get(pdf_link, stream=True)
            if response.status_code == 200:
                # Save the PDF with a unique filename
                filename = f"temp_{str(uuid.uuid4())}.pdf"
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                # Display the downloaded PDF
                return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=False)
            else:
                error_message = f"Error downloading PDF: Status code {response.status_code}"
        except Exception as e:
            error_message = f"Error downloading PDF: {str(e)}"
        return render_template("index.html", error_message=error_message)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=)
