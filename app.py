# Made by Kai Stephens

from flask import Flask, render_template, request, Response
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_marks', methods=['POST'])
def fetch_marks():
    url = "https://ta.yrdsb.ca/yrdsb/"
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return render_template("result.html", error="Please enter both username and password.")

    data = {"username": username, "password": password}
    response = requests.Session().post(url, data=data)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find('table', width="85%")
    if not table:
        return render_template("result.html", error="Failed to retrieve data. Please check your credentials.")

    rows = table.find_all('tr')[1:]  # Skip the header row
    courses = []
    marks = []

    for row in rows:
        cols = row.find_all('td')
        course_name = cols[0].get_text(strip=True)
        mark_info = cols[2]
        midterm_mark = mark_info.find('span')
        current_mark = mark_info.find('a')

        midterm_text = midterm_mark.get_text(strip=True) if midterm_mark else "No midterm"
        current_text = current_mark.get_text(strip=True) if current_mark else "No current mark"

        if current_text != "No current mark":
            courses.append({
                "course": course_name,
                "midterm": midterm_text,
                "current": current_text
            })
            try:
                mark_value = float(current_text.split("%")[0].split()[-1])
                marks.append(mark_value)
            except (ValueError, IndexError):
                marks.append(0.0)

    average_mark = round(sum(marks) / len(marks), 2) if marks else 0

    return render_template("result.html", courses=courses, average=average_mark)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)