# Made by Kai Stephens

# Import libraries
from flask import Flask, render_template, request, jsonify, session
from yrdsb_scraper import fetch_yrdsb_marks, fetch_yrdsb_advanced_report

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

import json
import os # Import os module
# import re # re is no longer used directly in app.py
# from urllib.parse import urljoin # urljoin is no longer used directly in app.py

# Make Flask app and configure secret key
app = Flask(__name__)
# For production, the secret key should be set via the FLASK_SECRET_KEY environment variable.
# A default is provided for development convenience if the environment variable is not set.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a-default-fallback-key-for-development-only")

# Make route for the home page
@app.route('/')
def index():
    # Render the index.html template when the home page is accessed
    return render_template('index.html')

# Make route to fetch marks from an external website based on user creds
@app.route('/fetch_marks', methods=['POST'])
def fetch_marks():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return render_template("result.html", error="Please enter both username and password.")

    courses, average_mark, error = fetch_yrdsb_marks(username, password)

    if error:
        return render_template("result.html", error=error)

    # Store relevant information in session for later use if needed
    session['username'] = username
    session['courses'] = courses
    session['average'] = average_mark

    # Render results page with fetched courses, average, and user creds
    return render_template(
        "result.html",
        courses=courses,
        average=average_mark,
        username=username,
        password=password # Password should be passed for the form in result.html
    )

# Define route to fetch report for assignments
@app.route('/fetch_advanced_report', methods=['POST'])
def fetch_advanced_report():
    username = request.form.get("username")
    password = request.form.get("password")
    advanced_url = request.form.get("advanced_url")

    if not username or not password or not advanced_url:
        return "Missing fields for advanced report." # This could be an HTML template too

    assignments, overall_mark, error_message = fetch_yrdsb_advanced_report(username, password, advanced_url)

    if error_message:
        return render_template(
            "advanced_report.html",
            error=error_message,
            assignments=[], # Provide default empty list
            overall=None,   # Provide default None
            username=username,
            password=password
        )

    # Render the advanced_report template with assignment data and overall mark
    return render_template(
        "advanced_report.html",
        assignments=assignments,
        overall=overall_mark,
        username=username,
        password=password # Password should be passed for the form in advanced_report.html
    )

# Chat route to handle user questions with AI assistance
@app.route('/chat', methods=['POST'])
def chat():
    # Get JSON data from the request
    data = request.get_json()
    # Gets user's message from the JSON input
    user_message = data.get('text', '')

    # If no message provided, return an error response
    if not user_message:
        return jsonify({"reply": "No message received."}), 400

    # Retrieve student information from session
    student_username = session.get('username', 'UnknownUser')
    courses_info = session.get('courses', [])
    average_mark = session.get('average', 'N/A')

    # System prompt for the AI model for fine tune.
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

    # Initialize Google Generative AI client and set model
    client = genai.Client()
    model_id = "gemini-2.0-flash-exp"

    # Create a Google Search tool instance so it can use google search
    google_search_tool = Tool(
        google_search=GoogleSearch()
    )

    # Generate content using the AI model with the system prompt and tool
    response = client.models.generate_content(
        model=model_id,
        contents=system_prompt,
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"]
        )
    )

    gemini_reply = ""
    # Check if AI response is valid and extract the reply
    if response and response.candidates and len(response.candidates) > 0:
        parts = [part.text for part in response.candidates[0].content.parts]
        gemini_reply = " ".join(parts)
    else:
        gemini_reply = "Sorry, I couldn't generate a response."

    # Return the AI's reply as JSON response
    return jsonify({"reply": gemini_reply}), 200

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

    app.run(host="0.0.0.0", port=5001)

    
