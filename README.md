# YRDSB Mark Fetcher & Teaching Assistant AI

This repository contains a Flask-based web application designed to help students fetch their marks from the YRDSB portal, view detailed assignment reports, and interact with an AI-powered teaching assistant.

## Overview

The application provides the following functionalities:
- **Fetch Marks:** Log in with your YRDSB credentials to retrieve current and midterm marks for your courses.
- **Advanced Reports:** View a detailed breakdown of assignment marks across various categories such as Knowledge, Thinking, Communication, Application, and Culminating.
- **AI Chat Assistant:** Engage in a chat with an AI teaching assistant that can answer questions and offer guidance based on your mark data, using Google’s GenAI services.

## Features

- **User Authentication & Session Management:**  
  Uses Flask sessions to store user information temporarily during the session.
  
- **Data Parsing:**  
  Utilizes `requests` and `BeautifulSoup` to scrape and parse HTML from the YRDSB website for marks and assignment reports.

- **Local Data Storage:**  
  Stores fetched data in a JSON file (`user_marks.json`)

- **AI Integration:**  
  Incorporates Google GenAI to create an interactive chat experience, providing responses based on user input and fetched data.

## Requirements

- Python 3.x
- Flask
- requests
- BeautifulSoup4 (`bs4`)
- google-genai (and its dependencies)
- Other dependencies as listed in `requirements.txt`

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/KaiStephens/TeachAssistScraper
   cd TeachAssistScraper

2. **Set up a virtual environment (optional but recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate   # On Windows use: venv\Scripts\activate

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    
4. **If planning on using AI use** If you run that AI app without setting your google API key in your environment it will return a server error. To set your google API key run this command:

   ```bash
    export GOOGLE_API_KEY="YOUR_API_KEY"
    ```
   If you do not have an api get one at https://aistudio.google.com/u/1/apikey free of charge (as of 01/14/25)

# Running the Application
Start the Flask server by running:

  ```bash
    python app.py
  ```

By default, the application will run on your local network and locally on http://{your_ip}:5001 and http://127.0.0.1:5001. Open this URL in your web browser to access the application.
