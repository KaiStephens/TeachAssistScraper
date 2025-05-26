import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import re

def fetch_yrdsb_marks(username, password):
    # Base URL and login URL for the external system
    base_url = "https://ta.yrdsb.ca/"
    login_url = base_url + "yrdsb/"
    
    # Create a session object
    session_req = requests.Session()
    login_payload = {"username": username, "password": password}
    
    try:
        # Perform POST request to login URL with provided credentials
        response = session_req.post(login_url, data=login_payload)
        response.raise_for_status() # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        return [], 0, f"Network error during login: {e}"

    # Parse the response using BeautifulSoup to find the data table with marks
    soup = BeautifulSoup(response.text, "html.parser")
    # Locate the specific table containing student marks
    table = soup.find('table', width="85%")
    # If table not found, return error indicating failure to retrieve data
    if not table:
        return None, None, "Failed to retrieve data. Check your credentials."
    
    # Extract rows from the table, skipping header row
    rows = table.find_all('tr')[1:]  
    courses = []
    marks = []

    # Loop through each row in the table to extract course and mark information
    for row in rows:
        try:
            cols = row.find_all('td')
            if not cols or len(cols) < 3: # Basic check for expected column count
                print(f"Parsing error for a row: Not enough columns or 'td' elements. Row: {row}")
                continue

            # Extract course name from the first cell
            course_name = cols[0].get_text(strip=True)
            # Get the third cell which contains mark information
            mark_info = cols[2]
            # Find midterm and current marks within the cell
            midterm_mark_tag = mark_info.find('span') # Renamed to avoid conflict
            current_mark_tag = mark_info.find('a')   # Renamed to avoid conflict
            
            # Extract text for midterm mark if present otherwise default message
            midterm_text = midterm_mark_tag.get_text(strip=True) if midterm_mark_tag else "No midterm"
            # Extract text for current mark if present otherwise default message
            current_text = current_mark_tag.get_text(strip=True) if current_mark_tag else "No current mark"
            
            current_link = None
            # If current mark has a link process the URL
            if current_mark_tag and current_mark_tag.get('href'):
                href_value = current_mark_tag['href']
                # Ensure the href_value has the correct starting path
                if not href_value.startswith("live/students/"):
                    href_value = "live/students/" + href_value
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
                # If the current mark contains a percentage
                if "%" in current_text:
                    try:
                        # Extract numerical mark value from current_text
                        mark_value = float(current_text.split("%")[0].split()[-1])
                        marks.append(mark_value)
                    except (ValueError, IndexError):
                        # If parsing fails, skip this mark calculation but course is still added
                        print(f"Parsing error for mark value in row: {row}. Mark text: {current_text}")
                        pass
        except (AttributeError, IndexError) as e:
            print(f"Critical parsing error for a row: {e}. Row: {row}")
            # Decide if you want to skip this row or raise a more general error
            continue # Skipping the problematic row
    
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
    # Do not store password in the JSON file
    existing_data[username] = {
        "courses": courses,
        "average_mark": average_mark
    }


    # Write updated data back to file
    with open("user_marks.json", "w") as f:
        json.dump(existing_data, f, indent=4)
    
    return courses, average_mark, None


def fetch_yrdsb_advanced_report(username, password, advanced_url):
    # Base URL and login URL for the external system
    base_url = "https://ta.yrdsb.ca/"
    login_url = base_url + "yrdsb/"

    # Create a session
    session_req = requests.Session()
    login_data = {"username": username, "password": password}
    # Perform login POST request
    session_req.post(login_url, data=login_data) # Assuming login is robust from fetch_yrdsb_marks

    try:
        # Fetch the advanced report page using the provided URL
        report_response = session_req.get(advanced_url)
        report_response.raise_for_status() # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        return [], None, f"Network error fetching advanced report: {e}"

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
        return None, None, "Could not find the advanced assignment table in the page."

    # Get all rows from the table
    all_rows = main_table.find_all("tr")
    # Check if there are enough rows to contain assignments
    if len(all_rows) < 2:
        return [], None, "No assignment rows found." # Return empty list for assignments

    assignments = []
    i = 1 

    # Loop through rows to process assignment data in pairs of rows
    while i < len(all_rows):
        try:
            row = all_rows[i]

            # Find the cell that spans two rows which contains the assignment name
            name_cell = row.find("td", attrs={"rowspan": "2"})
            # If no such cell, skip to next row
            if not name_cell:
                print(f"Parsing error for an assignment row: 'name_cell' not found. Row: {row}")
                i += 1 # Try to recover by moving to the next row, might not be a pair
                continue

            # Extract assignment name text
            assignment_name = name_cell.get_text(strip=True)
            # Create dictionary to hold assignment marks for different categories
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
            for cell_item in cells: # Renamed to avoid conflict with outer 'cell'
                # Normalize the bgcolor attribute of the cell
                bg = normalize_bgcolor(cell_item.get("bgcolor", ""))
                # Extract the mark text from the cell
                mark_text = extract_mark_text(cell_item)

                # Assign the mark to the correct category based on bgcolor
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
                p = parse_percentage(assignment_data[cat]) # Relies on helper, assumes it's robust
                if p is not None:
                    category_marks.append(p)

            # If any category marks found calculate the average and round to 1 decimal place
            if category_marks:
                avg_val = sum(category_marks) / len(category_marks)
                assignment_data["overall"] = round(avg_val, 1)

            # Append the completed assignment data to the assignments list
            assignments.append(assignment_data)

        except (AttributeError, IndexError, TypeError) as e:
            print(f"Critical parsing error for an assignment row: {e}. Row: {row}")
            # Skipping this assignment and its pair
        finally:
            # Ensure we always advance by 2, even if an error occurs mid-processing an assignment
            i += 2


    # Attempt to find overall mark displayed in a specific styled div
    overall_div = soup.find("div", style=lambda val: val and "font-size:64pt;color:#eeeeee;" in val)
    if overall_div:
        overall_mark = overall_div.get_text(strip=True)
    else:
        overall_mark = None
    
    return assignments, overall_mark, None # No error


# Helper functions
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
