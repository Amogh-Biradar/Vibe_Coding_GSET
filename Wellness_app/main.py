import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
load_dotenv()

# Gemini API setup
import google.generativeai as genai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wellness.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Custom Jinja filters
@app.template_filter('nl2br')
def nl2br(value):
    if value:
        return value.replace('\n', '<br>')
    return value

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # In production, use proper password hashing
    
class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Gemini API functions
def generate_gemini_response(prompt, model="gemini-2.5-flash", user_context=None, profile="default"):
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    
    # Check if API key is available and valid
    if not api_key or api_key == 'your_gemini_api_key_here':
        return "I'm sorry, but the chatbot is currently unavailable. The administrator needs to set up a valid Gemini API key in the .env file. Please try the other features of the application in the meantime."
    
    try:
        # Configure the API key
        genai.configure(api_key=api_key)
        
        # Persona prompt
        if profile == "goggins":
            persona = (
                "You are David Goggins, the ultra-endurance athlete and motivational speaker. "
                "Respond with tough love, directness, and motivation. Be concise, gritty, and push the user to embrace discomfort and take action. "
                "Your language must always be PG-13: do not use profanity or explicit language. Limit your response to 2-3 sentences."
            )
        elif profile == "dean_antoine":
            persona = (
                "You are Dean Jean Patrick Antoine, Assistant Dean for Enrichment Programs at Rutgers School of Engineering. "
                "You are supportive, motivational, and value education, collaboration, and personal growth. "
                "You have experience as an engineer and manager at Lockheed Martin, Dow Jones, and Bloomberg, and you direct the Honors Academy. "
                "Respond with wisdom, encouragement, and practical advice, especially for students and those seeking to improve themselves. "
                "Keep your language professional, warm, and always PG. Limit your response to 2-3 sentences."
            )
        elif profile == "niral_shah":
            persona = (
                "You are Mr. Niral Shah, a Machine Learning Engineer at Apple, with expertise in Applied AI, ML Platforms, Software Engineering, Computer Vision, and Augmented Reality. "
                "You have a strong background in both academia (Rutgers, Duke, Stanford) and industry (Apple, Tesla, Boeing, Verizon). "
                "Respond with professional, insightful, and encouraging advice, especially on topics related to technology, career development, and continuous learning. "
                "Your language should be constructive and always PG. Limit your response to 2-3 sentences."
            )
        else:
            persona = ("You are a supportive, empathetic mental wellness assistant. Respond in a concise, friendly, and encouraging way. Limit your response to 2-3 sentences.")
        
        # Compose the full prompt
        if user_context:
            full_prompt = f"{persona}\n\nUser context: {user_context}\n\nUser query: {prompt}"
        else:
            full_prompt = f"{persona}\n\nUser query: {prompt}"
        
        # Generate content
        model_obj = genai.GenerativeModel(model)
        response = model_obj.generate_content(full_prompt)
        
        return response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I apologize, but I'm having trouble connecting to the AI service right now. This could be due to an invalid API key or a network issue. Please try again later or contact the administrator."

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # In production, use proper password verification
            session['user_id'] = user.id
            return redirect(url_for('index'))
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/mood', methods=['GET', 'POST'])
def mood_tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        mood_score = request.form.get('mood_score')
        notes = request.form.get('notes')
        
        new_entry = MoodEntry(
            user_id=session['user_id'],
            mood_score=mood_score,
            notes=notes
        )
        db.session.add(new_entry)
        db.session.commit()
        
    # Get mood history
    mood_entries = MoodEntry.query.filter_by(user_id=session['user_id']).order_by(MoodEntry.timestamp.desc()).limit(10).all()
    return render_template('mood.html', entries=mood_entries)

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        content = request.form.get('content')
        
        new_entry = JournalEntry(
            user_id=session['user_id'],
            content=content
        )
        db.session.add(new_entry)
        db.session.commit()
        
    # Get journal entries
    journal_entries = JournalEntry.query.filter_by(user_id=session['user_id']).order_by(JournalEntry.timestamp.desc()).all()
    return render_template('journal.html', entries=journal_entries)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Check if API key is set
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key_here':
        flash('The chatbot requires a valid Gemini API key. Please check the .env file.', 'warning')
    chat_history = ChatHistory.query.filter_by(user_id=session['user_id']).order_by(ChatHistory.timestamp.desc()).limit(10).all()
    # Pass available profiles to the template
    profiles = [
        {"id": "default", "name": "Wellness Assistant"},
        {"id": "goggins", "name": "David Goggins"},
        {"id": "dean_antoine", "name": "Dean Jean Patrick Antoine"},
        {"id": "niral_shah", "name": "Mr. Niral Shah"}
    ]
    return render_template('chat.html', chat_history=chat_history, profiles=profiles)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    message = data.get('message', '')
    profile = data.get('profile', 'default')
    # Get recent mood and journal entries for context
    recent_moods = MoodEntry.query.filter_by(user_id=session['user_id']).order_by(MoodEntry.timestamp.desc()).limit(3).all()
    recent_journals = JournalEntry.query.filter_by(user_id=session['user_id']).order_by(JournalEntry.timestamp.desc()).limit(2).all()
    # Build context
    user_context = ""
    if recent_moods:
        mood_context = [f"Recent mood: {m.mood_score}/10 - {m.notes}" for m in recent_moods if m.notes]
        if mood_context:
            user_context += "Recent moods: " + "; ".join(mood_context) + ". "
    if recent_journals:
        journal_context = [f"Journal entry: {j.content[:100]}..." for j in recent_journals]
        if journal_context:
            user_context += "Recent journal entries: " + "; ".join(journal_context)
    # Generate response with context and profile
    response_text = generate_gemini_response(message, user_context=user_context, profile=profile)
    # Save to history
    new_chat = ChatHistory(
        user_id=session['user_id'],
        message=message,
        response=response_text
    )
    db.session.add(new_chat)
    db.session.commit()
    return jsonify({'response': response_text})

@app.route('/api/arcade_gemini', methods=['POST'])
def arcade_gemini():
    data = request.get_json()
    game = data.get('game')
    winner = data.get('winner')
    # Compose prompt for Gemini
    if game == 'pong':
        if winner == 'left':
            prompt = "The left player scored a point in Pong. Give a short, fun, motivational message for the left player, and a supportive message for the right player."
        else:
            prompt = "The right player scored a point in Pong. Give a short, fun, motivational message for the right player, and a supportive message for the left player."
    else:
        prompt = "A player just finished a game. Give a short, fun, motivational message."
    msg = generate_gemini_response(prompt, model="gemini-2.5-flash")
    return {"message": msg}

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get mood data for charts
    mood_data = MoodEntry.query.filter_by(user_id=session['user_id']).order_by(MoodEntry.timestamp.asc()).all()
    mood_scores = [entry.mood_score for entry in mood_data]
    mood_dates = [entry.timestamp.strftime('%Y-%m-%d') for entry in mood_data]
    
    return render_template('analytics.html', mood_scores=mood_scores, mood_dates=mood_dates)

@app.route('/arcade')
def arcade():
    return render_template('arcade.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)