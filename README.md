# YRDSB Mark Fetcher & Teaching Assistant AI

This repository contains a Flask-based web application designed to help students fetch their marks from the YRDSB portal, view detailed assignment reports, and interact with an AI-powered teaching assistant.

## Overview

The application provides the following functionalities:
- **Fetch Marks:** Log in with your YRDSB credentials to get current and midterm marks for your courses.
- **Advanced Reports:** View a detailed breakdown of assignment marks and see your Knowledge, Thinking, Communication, Application, and Culminating marks with weighting.
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

### Security Configuration

**Flask Secret Key**

To ensure the security of user sessions, it's crucial to set a strong, random secret key for the Flask application.

Set the `FLASK_SECRET_KEY` environment variable to a unique, random string. For example:

On Linux/macOS:
```bash
export FLASK_SECRET_KEY='your_strong_random_secret_key_here'
```

On Windows (Command Prompt):
```bash
set FLASK_SECRET_KEY=your_strong_random_secret_key_here
```

On Windows (PowerShell):
```bash
$env:FLASK_SECRET_KEY='your_strong_random_secret_key_here'
```

You can generate a strong key using Python:
```python
import secrets
secrets.token_hex(16)
```
The application includes a default fallback key for development if `FLASK_SECRET_KEY` is not set, but this fallback **should not** be used in any environment other than local development.

# Running the Application
Start the Flask server by running:

  ```bash
    python app.py
  ```

Or run the app without the AI Assistant with

  ```bash
    python appNoAI.py
  ```

By default, the application will run on your local network and locally on http://{your_ip}:5001 and http://127.0.0.1:5001. Open this URL in your web browser to access the application.

## Running Tests

Basic unit tests are provided for some helper functions in `yrdsb_scraper.py`. To run them, navigate to the project's root directory and execute:

```bash
python -m unittest tests.test_yrdsb_scraper
```
Alternatively, you can run the test file directly:
```bash
python tests/test_yrdsb_scraper.py
```
The test file `tests/test_yrdsb_scraper.py` includes logic to adjust `sys.path` to ensure that the `yrdsb_scraper` module can be imported correctly when run directly.
