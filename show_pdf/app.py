from flask import Flask, render_template, request, redirect, url_for
import pandas as pd

app = Flask(__name__)

# CSV file path
CSV_FILE = "candidate_data.csv"

# Define data structure for storing candidate information
class Candidate:
    def __init__(self, name, phone, email, resume_link, status):
        self.name = name
        self.phone = phone
        self.email = email
        self.resume_link = resume_link
        self.status = status

# Function to read CSV data and create Candidate objects
def load_candidates():
    try:
        df = pd.read_csv(CSV_FILE)
        candidates = []
        for index, row in df.iterrows():
            candidate = Candidate(row["Name"], row["Phone"], row["Email"], row["Resume Link"], row["Status"])
            candidates.append(candidate)
        return candidates
    except FileNotFoundError:
        print(f"Error: CSV file '{CSV_FILE}' not found.")
        return []

# Global variable to store candidates
candidates = load_candidates()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", candidates=candidates,link=candidates[0].resume_link)
    elif request.method == "POST":
        selected_index = int(request.form["selected_index"])
        if selected_index >= 0 and selected_index < len(candidates):
            selected_candidate = candidates[selected_index]
            print(selected_candidate.resume_link)
            return render_template("index.html", candidates=candidates, error="Invalid selection.", link=selected_candidate.resume_link)
        else:
            print(candidates[0].resume_link)
            return render_template("index.html", candidates=candidates, error="Invalid selection.", link=candidates[0].resume_link)

@app.route("/view_resume")
def view_resume(resume_link):
    try:
        # Open and display the PDF using a suitable method (browser plugin, server-side rendering, etc.)
        # Replace this placeholder with your chosen method

        print(f"Viewing resume: {resume_link}")
        return render_template("view_resume.html", resume_link=resume_link)
    except Exception as e:
        return render_template("view_resume.html", error=f"Error opening resume: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)
