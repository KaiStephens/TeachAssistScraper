# Made by Kai Stephens

from flask import Flask, render_template, request, jsonify, session
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

import json
import re

app = Flask(__name__)
app.secret_key = "some-random-secret-key" 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_marks', methods=['POST'])
def fetch_marks():

    base_url = "https://ta.yrdsb.ca/"
    login_url = base_url + "yrdsb/"
    
    username = request.form.get("username")
    password = request.form.get("password")
    
    if not username or not password:
        return render_template("result.html", error="Please enter both username and password.")
    
    session_req = requests.Session()
    login_payload = {"username": username, "password": password}
    response = session_req.post(login_url, data=login_payload)

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find('table', width="85%")
    if not table:
        return render_template("result.html", error="Failed to retrieve data. Check your credentials.")
    
    rows = table.find_all('tr')[1:]  
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
        
        current_link = None
        if current_mark and current_mark.get('href'):
            href_value = current_mark['href']
            if not href_value.startswith("live/students/"):
                href_value = "live/students/" + href_value
            current_link = urljoin(base_url, href_value)

        if current_text != "No current mark":
            courses.append({
                "course": course_name,
                "midterm": midterm_text,
                "current": current_text,
                "link": current_link
            })
            if "%" in current_text:
                try:
                    mark_value = float(current_text.split("%")[0].split()[-1])
                    marks.append(mark_value)
                except (ValueError, IndexError):
                    pass
    
    average_mark = round(sum(marks) / len(marks), 2) if marks else 0

    save_data = {
        "username": username,
        "courses": courses,
        "average_mark": average_mark
    }

    try:
        with open("user_marks.json", "r") as f:
            existing_data = json.load(f)
            if not isinstance(existing_data, dict):
                existing_data = {}
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = {}

    existing_data[username] = save_data

    with open("user_marks.json", "w") as f:
        json.dump(existing_data, f, indent=4)



    session['username'] = username
    session['courses'] = courses
    session['average'] = average_mark

    return render_template(
        "result.html",
        courses=courses,
        average=average_mark,
        username=username,
        password=password
    )

@app.route('/fetch_advanced_report', methods=['POST'])
def fetch_advanced_report():

    base_url = "https://ta.yrdsb.ca/"
    login_url = base_url + "yrdsb/"

    username = request.form.get("username")
    password = request.form.get("password")
    advanced_url = request.form.get("advanced_url")

    if not username or not password or not advanced_url:
        return "Missing fields for advanced report."

    session_req = requests.Session()
    login_data = {"username": username, "password": password}
    session_req.post(login_url, data=login_data)

    report_response = session_req.get(advanced_url)
    if report_response.status_code != 200:
        return f"Failed to fetch advanced report, status code: {report_response.status_code}"

    soup = BeautifulSoup(report_response.text, "html.parser")

    main_table = soup.find("table", attrs={
        "border": "1",
        "cellpadding": "3",
        "cellspacing": "0",
        "width": "100%"
    })
    if not main_table:
        return "Could not find the advanced assignment table in the page."

    all_rows = main_table.find_all("tr")
    if len(all_rows) < 2:
        return "No assignment rows found."

    def normalize_bgcolor(bg):
        if not bg:
            return ""
        return bg.lower().replace("#", "")

    def parse_percentage(mark_text):
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', mark_text)
        if match:
            return float(match.group(1))
        return None

    def extract_mark_text(td):
        sub_td = td.find("td")
        if sub_td:
            text = sub_td.get_text(strip=True)
            return text if text else "No Mark"
        text = td.get_text(strip=True)
        return text if text else "No Mark"

    assignments = []
    i = 1 

    while i < len(all_rows):
        row = all_rows[i]

        name_cell = row.find("td", attrs={"rowspan": "2"})
        if not name_cell:
            i += 1
            continue

        assignment_name = name_cell.get_text(strip=True)
        assignment_data = {
            "name": assignment_name,
            "knowledge": "No Mark",
            "thinking": "No Mark",
            "communication": "No Mark",
            "application": "No Mark",
            "culminating": "No Mark",
            "overall": None
        }

        cells = row.find_all("td", attrs={"rowspan": None}, recursive=False)

        for cell in cells:
            bg = normalize_bgcolor(cell.get("bgcolor", ""))
            mark_text = extract_mark_text(cell)

            if bg == "ffffaa":
                assignment_data["knowledge"] = mark_text
            elif bg == "c0fea4":
                assignment_data["thinking"] = mark_text
            elif bg == "afafff":
                assignment_data["communication"] = mark_text
            elif bg == "ffd490":
                assignment_data["application"] = mark_text
            elif bg == "dedede":
                assignment_data["culminating"] = mark_text

        category_marks = []
        for cat in ["knowledge", "thinking", "communication", "application", "culminating"]:
            p = parse_percentage(assignment_data[cat])
            if p is not None:
                category_marks.append(p)

        if category_marks:
            avg_val = sum(category_marks) / len(category_marks)
            assignment_data["overall"] = round(avg_val, 1)

        assignments.append(assignment_data)

        i += 2

    overall_div = soup.find("div", style=lambda val: val and "font-size:64pt;color:#eeeeee;" in val)
    if overall_div:
        overall_mark = overall_div.get_text(strip=True)
    else:
        overall_mark = None

    return render_template(
        "advanced_report.html",
        assignments=assignments,
        overall=overall_mark,
        username=username,
        password=password
    )

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('text', '')

    if not user_message:
        return jsonify({"reply": "No message received."}), 400

    student_username = session.get('username', 'UnknownUser')
    courses_info = session.get('courses', [])
    average_mark = session.get('average', 'N/A')

    system_prompt = f"""
    You are a helpful teaching assistant AI.
    The student logged in as {student_username}.
    Below is the student's current courses and marks:
    {courses_info}

    The student's overall average is {average_mark}%.

    All of this information is from YRDSB (York region district school board), if the user asks for information you do not have, (example: information about a sepcific class) search for the needed information relative to YRDSB.

    The student says: {user_message}

    Please answer as a friendly tutor/assistant, referencing the data above if helpful.

    Students may try and ask you questions not relating to their marks, in this case, answer the question (if appropriate) and try to keep them on track, always bring the conversation back to their marks if they stray too far.
    """

    client = genai.Client()
    model_id = "gemini-2.0-flash-exp"

    google_search_tool = Tool(
        google_search=GoogleSearch()
    )

    response = client.models.generate_content(
        model=model_id,
        contents=system_prompt,
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"]
        )
    )

    gemini_reply = ""
    if response and response.candidates and len(response.candidates) > 0:
        parts = [part.text for part in response.candidates[0].content.parts]
        gemini_reply = " ".join(parts)
    else:
        gemini_reply = "Sorry, I couldn't generate a response."

    return jsonify({"reply": gemini_reply}), 200

if __name__ == "__main__":
    print("|      |  /  _] /    |   /  ]|  |  |     /    | / ___/ / ___/|    | / ___/|      |     / ___/   /  ]|    \\  /    ||    \\   /  _]|    \\ ")
    print("|      | /  [_ |  o  |  /  / |  |  |    |  o  |(   \\_ (   \\_  |  | (   \\_ |      |    (   \\_   /  / |  D  )|  o  ||  o  ) /  [_ |  D  )")
    print("|_|  |_||    _]|     | /  /  |  _  |    |     | \\__  | \\__  | |  |  \\__  ||_|  |_|     \\__  | /  /  |    / |     ||   _/ |    _]|    / ")
    print("  |  |  |   [_ |  _  |/   \\_ |  |  |    |  _  | /  \\ | /  \\ | |  |  /  \\ |  |  |       /  \\ |/   \\_ |    \\ |  _  ||  |   |   [_ |    \\ ")
    print("  |  |  |     ||  |  |\\     ||  |  |    |  |  | \\    | \\    | |  |  \\    |  |  |       \\    |\\     ||  .  \\|  |  ||  |   |     ||  .  \\")
    print("  |__|  |_____||__|__| \\____||__|__|    |__|__|  \\___|  \\___||____|  \\___|  |__|        \\___| \\____||__|\\_||__|__||__|   |_____||__|\\_|")
    print(" ")
    print("Made by Kai Stephens")
    print(" ")

    app.run(host="0.0.0.0", port=5001)


                                                                                                                                
