import streamlit as st
import jwt
import datetime
from dotenv import load_dotenv
import os
import sqlite3
from streamlit_cookies_manager import CookieManager

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", 1))

# Initialize cookies
cookies = CookieManager()

# Database setup
def init_db():
    conn = sqlite3.connect('interview.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT,
                 experience_level TEXT)''')
    
    # Interviews table
    c.execute('''CREATE TABLE IF NOT EXISTS interviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 job_title TEXT,
                 session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Responses table
    c.execute('''CREATE TABLE IF NOT EXISTS interview_responses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 session_id INTEGER,
                 question TEXT,
                 user_answer TEXT,
                 ai_feedback TEXT,
                 score INTEGER,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY(user_id) REFERENCES users(id),
                 FOREIGN KEY(session_id) REFERENCES interviews(id))''')
    
    conn.commit()
    conn.close()

# Job categories and titles
JOB_CATEGORIES = {
    "Business & Management": [
        "Marketing Manager", "Human Resources Manager", "Business Analyst",
        "Project Manager", "Sales Executive", "Operations Manager",
        "Financial Analyst", "Management Consultant"
    ],
    "Technology & IT": [
        "Software Developer", "Data Scientist", "Cybersecurity Analyst",
        "Cloud Engineer", "IT Support Specialist", "UX/UI Designer",
        "DevOps Engineer", "AI/ML Engineer"
    ],
    "Healthcare & Medicine": [
        "Doctor", "Nurse", "Pharmacist", "Physical Therapist",
        "Psychologist", "Radiologist", "Medical Lab Technician", "Dentist"
    ],
    "Engineering": [
        "Mechanical Engineer", "Civil Engineer", "Electrical Engineer",
        "Aerospace Engineer", "Chemical Engineer", "Robotics Engineer",
        "Environmental Engineer", "Structural Engineer"
    ]
}

# JWT functions
def create_jwt(username):
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_jwt(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except:
        return None

# Authentication functions
def register_user(username, password, experience_level):
    conn = sqlite3.connect('interview.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, experience_level) VALUES (?, ?, ?)",
                 (username, password, experience_level))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect('interview.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
             (username, password))
    user = c.fetchone()
    conn.close()
    return user

def get_user_id(username):
    conn = sqlite3.connect('interview.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = c.fetchone()[0]
    conn.close()
    return user_id

# Interview functions
def create_interview_session(user_id, job_title):
    conn = sqlite3.connect('interview.db')
    c = conn.cursor()
    c.execute("INSERT INTO interviews (user_id, job_title) VALUES (?, ?)",
             (user_id, job_title))
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return session_id

def save_response(user_id, session_id, question, user_answer, ai_feedback, score):
    conn = sqlite3.connect('interview.db')
    c = conn.cursor()
    c.execute('''INSERT INTO interview_responses 
                 (user_id, session_id, question, user_answer, ai_feedback, score)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (user_id, session_id, question, user_answer, ai_feedback, score))
    conn.commit()
    conn.close()

def get_user_responses(username):
    conn = sqlite3.connect('interview.db')
    c = conn.cursor()
    
    user_id = get_user_id(username)
    
    c.execute('''SELECT i.session_date, i.job_title, 
                ir.question, ir.user_answer, ir.ai_feedback, ir.score
                FROM interview_responses ir
                JOIN interviews i ON ir.session_id = i.id
                WHERE ir.user_id = ?
                ORDER BY i.session_date DESC''', (user_id,))
    
    responses = []
    for row in c.fetchall():
        responses.append({
            'date': row[0],
            'job_title': row[1],
            'question': row[2],
            'answer': row[3],
            'feedback': row[4],
            'score': row[5]
        })
    
    conn.close()
    return responses

def generate_questions(job_title):
    common_questions = [
        "Tell me about yourself.",
        "What are your strengths and weaknesses?",
        "Why are you interested in this position?",
        "Where do you see yourself in 5 years?",
        "How do you handle pressure or stressful situations?"
    ]
    
    technical_questions = {
        "Software Developer": [
            "Explain a challenging coding problem you solved.",
            "How do you approach code reviews?",
            "Describe your experience with version control systems."
        ],
        "Data Scientist": [
            "Explain a machine learning project you worked on.",
            "How would you handle missing data?",
            "What metrics would you use to evaluate a classification model?"
        ],
        "Marketing Manager": [
            "Describe a successful marketing campaign you led.",
            "How do you measure ROI on marketing efforts?",
            "What digital marketing strategies are you most familiar with?"
        ]
    }
    
    return common_questions + technical_questions.get(job_title, [
        f"What specific skills do you have for this {job_title} role?",
        f"Describe your experience working as a {job_title}.",
        f"What challenges do you anticipate in this {job_title} position?"
    ])

def generate_feedback(question, answer):
    """Simplified feedback generation - replace with AI integration"""
    feedback_templates = {
        "Tell me about yourself.": [
            "Good overview. Consider focusing more on relevant professional experience.",
            "Well structured. Add more specific achievements.",
            "Try to keep it under 2 minutes. Good start!"
        ],
        "What are your strengths and weaknesses?": [
            "Good balance. Provide concrete examples for your strengths.",
            "For weaknesses, show how you're working to improve them.",
            "Honest assessment. Consider framing weaknesses as areas for growth."
        ]
    }
    
    default_feedback = [
        "Good response. Try to include specific examples.",
        "Well answered. Consider expanding on your points.",
        "Clear response. Could benefit from more detail."
    ]
    
    # Simple scoring based on answer length
    score = min(10, max(1, len(answer) // 20))
    
    # Get appropriate feedback
    feedback_options = feedback_templates.get(question, default_feedback)
    feedback = feedback_options[score % len(feedback_options)]
    
    return feedback, score

# Streamlit UI Components
def login_page():
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            user = authenticate_user(username, password)
            if user:
                token = create_jwt(username)
                cookies['auth_token'] = token
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

def register_page():
    with st.form("register_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        experience_level = st.selectbox(
            "Experience Level",
            ["Entry Level", "Mid Level", "Senior Level"]
        )
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if register_user(username, password, experience_level):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username already exists")

def dashboard_page():
    st.title(f"Welcome, {st.session_state.username}!")
    
    # Navigation
    page = st.sidebar.radio("Menu", ["New Interview", "Review Past Interviews"])
    
    if page == "New Interview":
        new_interview_page()
    else:
        review_interviews_page()

def new_interview_page():
    st.header("Start New Mock Interview")
    
    # Job selection
    category = st.selectbox("Select Job Category", list(JOB_CATEGORIES.keys()))
    job_title = st.selectbox("Select Job Title", JOB_CATEGORIES[category])
    
    if st.button("Start Interview"):
        user_id = get_user_id(st.session_state.username)
        session_id = create_interview_session(user_id, job_title)
        
        st.session_state.interview_started = True
        st.session_state.current_question = 0
        st.session_state.questions = generate_questions(job_title)
        st.session_state.current_session_id = session_id
        st.session_state.job_title = job_title
        st.rerun()
    
    if st.session_state.get('interview_started'):
        conduct_interview()

def conduct_interview():
    question = st.session_state.questions[st.session_state.current_question]
    
    st.subheader(f"Question {st.session_state.current_question + 1}/{len(st.session_state.questions)}")
    st.markdown(f"**{question}**")
    
    response = st.text_area("Your response", key=f"response_{st.session_state.current_question}", height=150)
    
    if st.button("Submit Answer"):
        if response.strip():
            # Generate feedback
            feedback, score = generate_feedback(question, response)
            
            # Save response
            user_id = get_user_id(st.session_state.username)
            save_response(
                user_id=user_id,
                session_id=st.session_state.current_session_id,
                question=question,
                user_answer=response,
                ai_feedback=feedback,
                score=score
            )
            
            st.session_state.current_question += 1
            
            if st.session_state.current_question >= len(st.session_state.questions):
                st.session_state.interview_complete = True
                st.session_state.interview_started = False
                st.rerun()
            else:
                st.rerun()
        else:
            st.warning("Please enter your response before submitting")

def review_interviews_page():
    st.header("Your Past Interview Reviews")
    
    responses = get_user_responses(st.session_state.username)
    
    if not responses:
        st.warning("You haven't completed any interviews yet")
        return
    
    # Group by session
    sessions = {}
    for resp in responses:
        session_key = f"{resp['job_title']} - {resp['date']}"
        if session_key not in sessions:
            sessions[session_key] = []
        sessions[session_key].append(resp)
    
    # Display sessions
    for session, session_responses in sessions.items():
        with st.expander(f"📅 {session}"):
            avg_score = sum(r['score'] for r in session_responses) / len(session_responses)
            st.metric("Average Score", f"{avg_score:.1f}/10")
            
            for i, resp in enumerate(session_responses, 1):
                st.markdown(f"### ❓ Question {i}")
                st.markdown(f"**{resp['question']}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### ✍️ Your Answer")
                    st.info(resp['answer'])
                
                with col2:
                    st.markdown(f"#### 💡 AI Feedback (Score: {resp['score']}/10)")
                    st.success(resp['feedback'])
                
                st.divider()

def logout_button():
    if st.sidebar.button("Logout"):
        cookies['auth_token'] = ""
        st.session_state.clear()
        st.rerun()

# Main App Flow
def main():
    # Initialize database
    init_db()
    
    # Check authentication
    token = cookies.get('auth_token')
    if token and verify_jwt(token):
        user_data = verify_jwt(token)
        st.session_state.logged_in = True
        st.session_state.username = user_data['username']
    
    # Show appropriate UI
    if not st.session_state.get('logged_in'):
        st.title("AI Mock Interview Platform")
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            login_page()
        with tab2:
            register_page()
    else:
        if st.session_state.get('interview_complete'):
            st.success("🎉 Interview completed successfully!")
            if st.button("View Results"):
                st.session_state.interview_complete = False
                st.rerun()
        else:
            dashboard_page()
            logout_button()

if __name__ == "__main__":
    main()