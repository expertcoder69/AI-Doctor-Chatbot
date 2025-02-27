import time
import os
import joblib
import streamlit as st
import sqlite3
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

# Load .env file
load_dotenv(dotenv_path=".env")

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    st.error("Google API key not found! Check your .env file.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Initialize session state variables
if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(time.time())  # Unique chat ID

if "past_chats" not in st.session_state:
    st.session_state.past_chats = {}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []

if "chat_title" not in st.session_state:
    st.session_state.chat_title = None

if "user_biodata" not in st.session_state:
    st.session_state.user_biodata = {}

if "scheduler" not in st.session_state:
    st.session_state.scheduler = BackgroundScheduler()
    st.session_state.scheduler.start()

if "chat" not in st.session_state:
    st.session_state.chat = None

# Create a data folder if it doesn’t exist
os.makedirs("data/", exist_ok=True)

# Load past chats
try:
    past_chats = joblib.load("data/past_chats_list")
except (FileNotFoundError, EOFError):
    past_chats = {}
st.session_state.past_chats = past_chats

# --- User Biodata Input Form ---
st.write("# Dr. Pashupathy 2.0 here!")
st.write("ഞാൻ പഷുപതി... ഡോക്ടർ പഷുപതി... ബൊംബെയിൽ MBBS, MD, MS, BSc, PhD, DDT, LSD ഒക്കെ കഴിഞ്ഞത്!")
st.write("# User Biodata")

with st.form("user_biodata_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, value=25, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", min_value=0, value=170, step=1)
    weight = st.number_input("Weight (kg)", min_value=0, value=70, step=1)
    health_issues = st.text_area("Health Issues (comma-separated)")
    activity_level = st.selectbox("Activity Level", ["Light", "Moderate", "Heavy"])

    submitted = st.form_submit_button("Submit Biodata")

    if submitted:
        st.session_state.user_biodata = {
            "Name": name,
            "Age": age,
            "Gender": gender,
            "Height (cm)": height,
            "Weight (kg)": weight,
            "Health Issues": health_issues,
            "Activity Level": activity_level,
        }
        st.success("Biodata submitted successfully!")

# --- Main Page Layout ---
    st.write("# User Profile")
    if st.session_state.user_biodata:
        st.dataframe(pd.DataFrame([st.session_state.user_biodata]).T)
    else:
        st.write("Please submit your biodata first.")

# --- SQLite Database Functions ---
DB_FILE = "medications.db"

def init_db():
    """Initialize the database and create the necessary tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            start_date TEXT NOT NULL,
            reminder_times TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_medication_to_db(med_name, dosage, frequency, start_date, reminder_times):
    """Save medication details to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO medications (name, dosage, frequency, start_date, reminder_times)
        VALUES (?, ?, ?, ?, ?)
    """, (med_name, dosage, frequency, start_date, ",".join(map(str, reminder_times))))
    conn.commit()
    conn.close()

def load_medications_from_db():
    """Load medications from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, dosage, frequency, start_date, reminder_times FROM medications")
    rows = cursor.fetchall()
    conn.close()
    
    medications = {}
    for row in rows:
        medications[row[0]] = {
            "Dosage": row[1],
            "Frequency": row[2],
            "Start Date": datetime.datetime.strptime(row[3], "%Y-%m-%d").date(),
            "Reminder Times": [datetime.datetime.strptime(t, "%H:%M:%S").time() for t in row[4].split(",")]
        }
    return medications

# Initialize database
init_db()

# Load medications from database
st.session_state.medications = load_medications_from_db()

# --- Medication Tracking UI ---
st.write("## Medication Tracker")

if st.session_state.medications:
    for med_name, med_data in st.session_state.medications.items():
        checkbox_key = f"{med_name}-taken-{datetime.date.today()}"
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = False
        taken = st.checkbox(f"{med_name} (Dosage: {med_data['Dosage']})", key=checkbox_key)

st.write("### Add New Medication")

with st.form("add_medication_form"):
    medication_name = st.text_input("Medication Name", placeholder="Enter medication name")
    dosage = st.text_input("Dosage", placeholder="e.g., 10mg, 2 tablets")
    frequency = st.selectbox("Frequency", ["Once Daily", "Twice Daily", "Thrice Daily"])
    start_date = st.date_input("Start Date", value=datetime.date.today())

    reminder_times = []
    if frequency == "Once Daily":
        reminder_time = st.time_input("Reminder Time")
        if reminder_time:
            reminder_times = [reminder_time]
    elif frequency == "Twice Daily":
        col1, col2 = st.columns(2)
        with col1:
            reminder_time1 = st.time_input("Reminder Time 1")
        with col2:
            reminder_time2 = st.time_input("Reminder Time 2")
        if reminder_time1 and reminder_time2:
            reminder_times = [reminder_time1, reminder_time2]
    elif frequency == "Thrice Daily":
        col1, col2, col3 = st.columns(3)
        with col1:
            reminder_time1 = st.time_input("Reminder Time 1")
        with col2:
            reminder_time2 = st.time_input("Reminder Time 2")
        with col3:
            reminder_time3 = st.time_input("Reminder Time 3")
        if reminder_time1 and reminder_time2 and reminder_time3:
            reminder_times = [reminder_time1, reminder_time2, reminder_time3]

    submitted = st.form_submit_button("Add Medication")

    if submitted:
        if not medication_name:
            st.error("Medication name is required.")
        elif not reminder_times:
            st.error("Please select at least one reminder time.")
        else:
            save_medication_to_db(medication_name, dosage, frequency, str(start_date), reminder_times)
            st.success(f"Medication '{medication_name}' added successfully!")
            st.rerun()

# --- Medication Reminders ---
st.write("### Medication Reminders")

if st.session_state.medications:
    today = datetime.date.today()
    for med_name, med_data in st.session_state.medications.items():
        if med_data["Start Date"] <= today:
            st.write(f"**{med_name}**:")
            for reminder_time in med_data["Reminder Times"]:
                st.write(f"- {med_data['Frequency']} at {reminder_time.strftime('%I:%M %p')}")
                taken_key = f"{med_name}-taken-{today}"
                if taken_key in st.session_state and st.session_state[taken_key]:
                    st.write("  ✅ Taken")
                else:
                    st.write("  ❌ Not Taken")
        else:
            st.write(f"**{med_name}** will start on {med_data['Start Date']}")
else:
    st.info("No medications added yet.")

# --- Diet Plan Section ---
st.write("## Personalized Diet Plan")

# Check if user biodata is available
if st.session_state.user_biodata:
    with st.form("diet_plan_form"):
        dietary_preference = st.selectbox("Dietary Preference", ["Vegetarian", "Non-Vegetarian", "Vegan"])
        allergies = st.text_area("Allergies (comma-separated)", placeholder="e.g., peanuts, dairy")
        specific_goals = st.selectbox("Health Goal", ["Weight Loss", "Muscle Gain", "Maintenance"])

        diet_submitted = st.form_submit_button("Generate Diet Plan")

        if diet_submitted:
            # Store user's dietary preferences
            st.session_state.user_biodata["Dietary Preference"] = dietary_preference
            st.session_state.user_biodata["Allergies"] = allergies
            st.session_state.user_biodata["Health Goal"] = specific_goals

            # Generate diet plan based on user data
            diet_plan = []

            # Sample meal plans based on activity level & health goal
            if specific_goals == "Weight Loss":
                diet_plan = [
                    "Breakfast: Oatmeal with fruits",
                    "Lunch: Grilled chicken salad",
                    "Dinner: Steamed vegetables with quinoa",
                ]
            elif specific_goals == "Muscle Gain":
                diet_plan = [
                    "Breakfast: Scrambled eggs with toast",
                    "Lunch: Grilled salmon with rice",
                    "Dinner: Chicken breast with sweet potatoes",
                ]
            else:
                diet_plan = [
                    "Breakfast: Whole grain toast with peanut butter",
                    "Lunch: Lentil soup with whole grain bread",
                    "Dinner: Brown rice with stir-fried vegetables",
                ]

            # Consider medications that may impact diet
            if st.session_state.medications:
                for med_name, med_data in st.session_state.medications.items():
                    if "Blood Pressure" in st.session_state.user_biodata["Health Issues"]:
                        diet_plan.append("**Note:** Avoid high-sodium foods due to blood pressure medication.")
                    if "Diabetes" in st.session_state.user_biodata["Health Issues"]:
                        diet_plan.append("**Note:** Opt for low-sugar, high-fiber meals.")

            # Store and display diet plan
            st.session_state.user_biodata["Diet Plan"] = diet_plan
            st.success("Diet plan generated successfully!")

# Display diet plan
if "Diet Plan" in st.session_state.user_biodata:
    st.write("### Your Diet Plan:")
    for meal in st.session_state.user_biodata["Diet Plan"]:
        st.write(f"- {meal}")
else:
    st.info("Please generate a diet plan first.")

# --- Chatbot ---
try:
    st.session_state.messages = joblib.load(f"data/{st.session_state.chat_id}-st_messages")
    st.session_state.gemini_history = joblib.load(f"data/{st.session_state.chat_id}-gemini_messages")
except (FileNotFoundError, EOFError):
    st.session_state.messages = []
    st.session_state.gemini_history = []
    st.session_state.model = genai.GenerativeModel("gemini-pro")
    st.session_state.chat = st.session_state.model.start_chat(history=st.session_state.gemini_history)

# Display past chat messages
for message in st.session_state.messages:
    with st.chat_message(name=message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])

# --- Handle New Chat Input ---
if st.session_state.user_biodata and st.session_state.medications:
    if st.button("Get Personalized Advice"):
        final_prompt = f"""
User biodata:
- Age: {st.session_state.user_biodata.get('Age', 'N/A')}
- Gender: {st.session_state.user_biodata.get('Gender', 'N/A')}
- Height: {st.session_state.user_biodata.get('Height (cm)', 'N/A')} cm
- Weight: {st.session_state.user_biodata.get('Weight (kg)', 'N/A')} kg

Medications: {st.session_state.medications if 'medications' in st.session_state else 'No medications provided.'}

The user is looking for **general fitness advice** to improve health. Provide **general guidance** on nutrition and exercise, without giving medical advice.
⚠️ **Note:** This is for informational purposes only, and the user should consult a doctor for personalized guidance.
"""

        response = st.session_state.chat.send_message(final_prompt, stream=True)

        # Display AI response
        with st.chat_message(name="ai", avatar="👨🏾‍⚕️"):
            message_placeholder = st.empty()
            full_response = ""
            for chunk in response:
                for ch in chunk.text.split(" "):
                    full_response += ch + " "
                    time.sleep(0.05)
                    message_placeholder.write(full_response + "▌")
            message_placeholder.write(full_response)

        # Save AI response to history
        st.session_state.messages.append(
            {"role": "ai", "content": st.session_state.chat.history[-1].parts[0].text, "avatar": "👨🏾‍⚕️"}
        )
        st.session_state.gemini_history = st.session_state.chat.history

        # Save chat history to file
        joblib.dump(st.session_state.messages, f"data/{st.session_state.chat_id}-st_messages")
        joblib.dump(st.session_state.gemini_history, f"data/{st.session_state.chat_id}-gemini_messages")

# Continue chatting
if prompt := st.chat_input("Dr. Pashupathy 2.0 at your service..."):
    # Save chat
    if st.session_state.chat_id not in past_chats.keys():
        past_chats[st.session_state.chat_id] = st.session_state.chat_title
        joblib.dump(past_chats, "data/past_chats_list")

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Send message to AI
    response = st.session_state.chat.send_message(prompt, stream=True)

    # Display AI response
    with st.chat_message(name="ai", avatar="👨🏾‍⚕️"):
        message_placeholder = st.empty()
        full_response = ""
        for chunk in response:
            for ch in chunk.text.split(" "):
                full_response += ch + " "
                time.sleep(0.05)
                message_placeholder.write(full_response + "▌")
        message_placeholder.write(full_response)

    # Save AI response to history
    st.session_state.messages.append(
        {"role": "ai", "content": st.session_state.chat.history[-1].parts[0].text, "avatar": "👨🏾‍⚕️"}
    )
    st.session_state.gemini_history = st.session_state.chat.history

    # Save chat history to file
    joblib.dump(st.session_state.messages, f"data/{st.session_state.chat_id}-st_messages")
    joblib.dump(st.session_state.gemini_history, f"data/{st.session_state.chat_id}-gemini_messages")