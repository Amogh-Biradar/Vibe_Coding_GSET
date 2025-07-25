# MindWell - Mental Wellness Companion

A comprehensive mental wellness application that helps users track their mood, journal their thoughts, and get real-time support through a Gemini-powered AI chatbot.

## Features

- **Mood Tracking**: Log and visualize your mood patterns over time
- **Journaling**: Express your thoughts and feelings in a private journal
- **AI Wellness Chat**: Get personalized support from an AI assistant powered by Google's Gemini API
- **Analytics**: View insights and trends about your mental wellness journey

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key (get one from [Google AI Studio](https://ai.google.dev/))

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd mindwell
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. Run the application:
   ```
   python main.py
   ```

6. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. Register for a new account or log in
2. Use the dashboard to navigate to different features
3. Track your mood daily
4. Write journal entries to express your thoughts
5. Chat with the AI wellness assistant for support
6. View your analytics to gain insights into your wellness journey

## Technologies Used

- **Backend**: Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite
- **AI**: Google Gemini API

## License

This project is licensed under the MIT License - see the LICENSE file for details. 