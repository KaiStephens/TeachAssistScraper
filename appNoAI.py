# Made by Kai Stephens

# Import libraries
from flask import Flask, render_template, request, jsonify, session
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import json
import re

# Make Flask app and configure secret key
app = Flask(__name__)
app.secret_key = "some-random-secret-key"

# Make route for the home page
@app.route('/')
def index():
    # Render the index.html template when the home page is accessed 
    return render_template('index.html')

# Make route to fetch marks from an external website based on user creds
@app.route('/fetch_marks', methods=['POST'])
def fetch_marks():
    # Base URL and login URL for the external system
    base_url = "https://ta.yrdsb.ca/"
    login_url = base_url + "yrdsb/"
    
    # Retrieve username and password from the form
    username = request.form.get("username")
    password = request.form.get("password")
    
    # Check if both username and password are provided
    if not username or not password:
        # If missing render template with an error message
        return render_template("resultNoAI.html", error="Please enter both username and password.")
    
    # Create a session object
    session_req = requests.Session()
    
    # Perform POST request to login URL with provided credentials
    response = session_req.post(login_url, data={"username": username, "password": password})

    # Parse the response using BeautifulSoup to find the data table with marks
    soup = BeautifulSoup(response.text, "html.parser")
    # Locate the specific table containing student marks
    table = soup.find('table', width="85%")
    # If table not found, render error page indicating failure to retrieve data (Usually user entered credentials wrong)
    if not table:
        return render_template("resultNoAI.html", error="Failed to retrieve data. Check your credentials.")
    
    # Extract rows from the table, skipping header row
    rows = table.find_all('tr')[1:]
    courses = []
    marks = []

    # Loop through each row in the table to extract course and mark information
    for row in rows:
        # Get all cells in the row
        cols = row.find_all('td')
        # Extract course name from the first cell
        course_name = cols[0].get_text(strip=True)
        # Get the third cell which contains mark information
        mark_info = cols[2]
        # Find midterm and current marks within the cell
        midterm_mark = mark_info.find('span')
        current_mark = mark_info.find('a')
        
        # Extract text for midterm mark if present otherwise default message
        midterm_text = midterm_mark.get_text(strip=True) if midterm_mark else "No midterm"
        # Extract text for current mark if present otherwise default message
        current_text = current_mark.get_text(strip=True) if current_mark else "No current mark"
        
        current_link = None
        # If current mark has a link process the URL
        if current_mark and current_mark.get('href'):
            href_value = current_mark['href']
            # Ensure the href_value has the correct starting path
            if not href_value.startswith("live/students/"):
                href_value = "live/students/" + href_value
            # Join base URL with href to form complete URL
            current_link = urljoin(base_url, href_value)

        # Only process courses that have a current mark available
        if current_text != "No current mark":
            # Append course details to courses list
            courses.append({
                "course": course_name,
                "midterm": midterm_text,
                "current": current_text,
                "link": current_link
            })
            # If the current mark contains a percentage attempt to parse and store it (Ignores no marks or something like Level 4)
            if "%" in current_text:
                try:
                    # Extract numerical mark value from current_text
                    mark_value = float(current_text.split("%")[0].split()[-1])
                    marks.append(mark_value)
                except (ValueError, IndexError):
                    # If parsing fails, skip this mark
                    pass
    
    # Calculate average mark from all collected marks round to 2 decimal places
    average_mark = round(sum(marks) / len(marks), 2) if marks else 0

    save_data = {
        "username": username,
        "courses": courses,
        "average_mark": average_mark
    }

    # Try to read existing user marks data from file
    try:
        with open("user_marks.json", "r") as f:
            existing_data = json.load(f)
            # Ensure existing_data is a dictionary
            if not isinstance(existing_data, dict):
                existing_data = {}
    except (FileNotFoundError, json.JSONDecodeError):
        # If file not found or contains invalid JSON initialize empty dictionary
        existing_data = {}

    # Update existing data with current user's data
    existing_data[username] = save_data

    # Write updated data back to file
    with open("user_marks.json", "w") as f:
        json.dump(existing_data, f, indent=4)

    # Store relevant information in session for later use if needed
    session['username'] = username
    session['courses'] = courses
    session['average'] = average_mark

    # Render results page with fetched courses, average, and user creds
    return render_template(
        "resultNoAI.html",
        courses=courses,
        average=average_mark,
        username=username,
        password=password
    )

# Define route to fetch report for assignments
@app.route('/fetch_advanced_report', methods=['POST'])
def fetch_advanced_report():
    # Base URL and login URL for the external system
    base_url = "https://ta.yrdsb.ca/"
    login_url = base_url + "yrdsb/"

    # Retrieve username, password, and advanced report URL from form data
    username = request.form.get("username")
    password = request.form.get("password")
    advanced_url = request.form.get("advanced_url")

    # Check if all necessary fields are provided
    if not username or not password or not advanced_url:
        return "Missing fields for advanced report."

    # Create a session
    session_req = requests.Session()
    # Perform login POST request
    session_req.post(login_url, data={"username": username, "password": password})

    # Fetch the advanced report page using the provided URL
    report_response = session_req.get(advanced_url)
    # Check if request was successful
    if report_response.status_code != 200:
        return f"Failed to fetch advanced report, status code: {report_response.status_code}"

    # Parse the fetched page using BeautifulSoup
    soup = BeautifulSoup(report_response.text, "html.parser")

    # Locate the main assignment table in the page
    main_table = soup.find("table", attrs={
        "border": "1",
        "cellpadding": "3",
        "cellspacing": "0",
        "width": "100%"
    })
    # If the table is not found, return an error message
    if not main_table:
        return "Could not find the advanced assignment table in the page."

    # Get all rows from the table
    all_rows = main_table.find_all("tr")
    # Check if there are enough rows to contain assignments
    if len(all_rows) < 2:
        return "No assignment rows found."

    # Function to normalize bgcolor attribute value
    def normalize_bgcolor(bg):
        if not bg:
            return ""
        return bg.lower().replace("#", "")

    # Function to parse percentage value from text
    def parse_percentage(mark_text):
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', mark_text)
        if match:
            return float(match.group(1))
        return None

    # Function to extract text from a table cell
    def extract_mark_text(td):
        sub_td = td.find("td")
        if sub_td:
            text = sub_td.get_text(strip=True)
            return text if text else "No Mark"
        text = td.get_text(strip=True)
        return text if text else "No Mark"

    assignments = []
    i = 1

    # Loop through rows to process assignment data in pairs of rows
    while i < len(all_rows):
        row = all_rows[i]

        # Find the cell that spans two rows which contains the assignment name
        name_cell = row.find("td", attrs={"rowspan": "2"})
        # If no such cell, skip to next row
        if not name_cell:
            i += 1
            continue

        # Extract assignment name text
        assignment_name = name_cell.get_text(strip=True)
        # Make dictionary to hold assignment marks for different categories
        assignment_data = {
            "name": assignment_name,
            "knowledge": "No Mark",
            "thinking": "No Mark",
            "communication": "No Mark",
            "application": "No Mark",
            "culminating": "No Mark",
            "overall": None
        }

        # Find all cells in the row that do not span multiple rows
        cells = row.find_all("td", attrs={"rowspan": None}, recursive=False)

        # Process each cell to determine its category based on background color
        for cell in cells:
            # Normalize the bgcolor attribute of the cell
            bg = normalize_bgcolor(cell.get("bgcolor", ""))
            # Extract the mark text from the cell
            mark_text = extract_mark_text(cell)

            # Assign the mark to the correct category based on bgcolor (they better not change thier color scheme)
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

        # Collect percentage values from each category to calculate overall average
        category_marks = []
        for cat in ["knowledge", "thinking", "communication", "application", "culminating"]:
            p = parse_percentage(assignment_data[cat])
            if p is not None:
                category_marks.append(p)

        # If any category marks found calculate the average and round to 1 decimal place
        if category_marks:
            avg_val = sum(category_marks) / len(category_marks)
            assignment_data["overall"] = round(avg_val, 1)

        # Append the completed assignment data to the assignments list
        assignments.append(assignment_data)

        # Skip to the next pair of rows (each assignment uses two rows)
        i += 2

    # Attempt to find overall mark displayed in a specific styled div
    overall_div = soup.find("div", style=lambda val: val and "font-size:64pt;color:#eeeeee;" in val)
    if overall_div:
        overall_mark = overall_div.get_text(strip=True)
    else:
        overall_mark = None

    # Render the advanced_report template with assignment data and overall mark
    return render_template(
        "advanced_report.html",
        assignments=assignments,
        overall=overall_mark,
        username=username,
        password=password
    )

if __name__ == "__main__":
    # Print ASCII art and credits
    print("|      |  /  _] /    |   /  ]|  |  |     /    | / ___/ / ___/|    | / ___/|      |     / ___/   /  ]|    \\  /    ||    \\   /  _]|    \\ ")
    print("|      | /  [_ |  o  |  /  / |  |  |    |  o  |(   \\_ (   \\_  |  | (   \\_ |      |    (   \\_   /  / |  D  )|  o  ||  o  ) /  [_ |  D  )")
    print("|_|  |_||    _]|     | /  /  |  _  |    |     | \\__  | \\__  | |  |  \\__  ||_|  |_|     \\__  | /  /  |    / |     ||   _/ |    _]|    / ")
    print("  |  |  |   [_ |  _  |/   \\_ |  |  |    |  _  | /  \\ | /  \\ | |  |  /  \\ |  |  |       /  \\ |/   \\_ |    \\ |  _  ||  |   |   [_ |    \\ ")
    print("  |  |  |     ||  |  |\\     ||  |  |    |  |  | \\    | \\    | |  |  \\    |  |  |       \\    |\\     ||  .  \\|  |  ||  |   |     ||  .  \\")
    print("  |__|  |_____||__|__| \\____||__|__|    |__|__|  \\___|  \\___||____|  \\___|  |__|        \\___| \\____||__|\\_||__|__||__|   |_____||__|\\_|")
    print(" ")
    print("Made by Kai Stephens")
    print(" ")
    print("**No AI version, run app.py to use AI version.**")
    print(" ")

    # Start Flask app on host 0.0.0.0 and port 5001
    app.run(host="0.0.0.0", port=5001)
