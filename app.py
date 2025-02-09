import time
import os
import joblib
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY=os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

new_chat_id = f'{time.time()}'
MODEL_ROLE = 'ai'
AI_AVATAR_ICON = '👨🏾‍⚕️'

# Create a data/ folder if it doesn't already exist
try:
    os.mkdir('data/')
except:
    # data/ folder already exists
    pass

# Load past chats (if available)
try:
    past_chats: dict = joblib.load('data/past_chats_list')
except:
    past_chats = {}

# Sidebar allows a list of past chats
with st.sidebar:
    st.write('# Past Chats')
    if st.session_state.get('chat_id') is None:
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id] + list(past_chats.keys()),
            format_func=lambda x: past_chats.get(x, 'New Chat'),
            placeholder='_',
        )
    else:
        # This will happen the first time AI response comes in
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id, st.session_state.chat_id] + list(past_chats.keys()),
            index=1,
            format_func=lambda x: past_chats.get(x, 'New Chat' if x != st.session_state.chat_id else st.session_state.chat_title),
            placeholder='_',
        )
    # Save new chats after a message has been sent to AI
    # TODO: Give user a chance to name chat
    st.session_state.chat_title = f'ChatSession-{st.session_state.chat_id}'

st.write('# Dr. Pashupathy 2.0 here!')
st.write(' ഞാൻ പഷുപതി... ഡോക്ടർ പഷുപതി... ബൊംബെയിൽ MBBS, MD, MS, BSc, PhD, DDT, LSD ഒക്കെ കഴിഞ്ഞത്')

# Chat history (allows to ask multiple questions)
try:
    st.session_state.messages = joblib.load(
        f'data/{st.session_state.chat_id}-st_messages'
    )
    st.session_state.gemini_history = joblib.load(
        f'data/{st.session_state.chat_id}-gemini_messages'
    )
    print('old cache')
except:
    st.session_state.messages = []
    st.session_state.gemini_history = []
    print('new_cache made')
st.session_state.model = genai.GenerativeModel('gemini-pro')
st.session_state.chat = st.session_state.model.start_chat(
    history=st.session_state.gemini_history,
)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(
        name=message['role'],
        avatar=message.get('avatar'),
    ):
        st.markdown(message['content'])

# React to user input
if prompt := st.chat_input('Your message here...'):
    # Save this as a chat for later
    if st.session_state.chat_id not in past_chats.keys():
        past_chats[st.session_state.chat_id] = st.session_state.chat_title
        joblib.dump(past_chats, 'data/past_chats_list')
    # Display user message in chat message container
    with st.chat_message('user'):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append(
        dict(
            role='user',
            content=prompt,
        )
    )
    ## Send message to AI
    response = st.session_state.chat.send_message(
        prompt,
        stream=True,
    )
    # Display assistant response in chat message container
    with st.chat_message(
        name=MODEL_ROLE,
        avatar=AI_AVATAR_ICON,
    ):
        message_placeholder = st.empty()
        full_response = ''
        assistant_response = response
        # Streams in a chunk at a time
        for chunk in response:
            # Simulate stream of chunk
            # TODO: Chunk missing `text` if API stops mid-stream ("safety"?)
            for ch in chunk.text.split(' '):
                full_response += ch + ' '
                time.sleep(0.05)
                # Rewrites with a cursor at end
                message_placeholder.write(full_response + '▌')
        # Write full message with placeholder
        message_placeholder.write(full_response)

    # Add assistant response to chat history
    st.session_state.messages.append(
        dict(
            role=MODEL_ROLE,
            content=st.session_state.chat.history[-1].parts[0].text,
            avatar=AI_AVATAR_ICON,
        )
    )
    st.session_state.gemini_history = st.session_state.chat.history
    # Save to file
    joblib.dump(
        st.session_state.messages,
        f'data/{st.session_state.chat_id}-st_messages',
    )
    joblib.dump(
        st.session_state.gemini_history,
        f'data/{st.session_state.chat_id}-gemini_messages',
    )

import time
import os
import joblib
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd  # For data display (biodata)
# ... (Import other libraries as needed: for exercise planning, diet chart, medication tracking)

load_dotenv()

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# ... (Other constants and setup)

# --- User Biodata Input Form ---
st.write("# User Biodata")

with st.form("user_biodata_form"):  # Use a form for better organization
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, value=25, step=1)  # Number input for age
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", min_value=0, value=170, step=1)
    weight = st.number_input("Weight (kg)", min_value=0, value=70, step=1)
    health_issues = st.text_area("Health Issues (comma-separated)", placeholder="e.g., Diabetes, Hypertension")
    activity_level = st.selectbox("Activity Level", ["Light", "Moderate", "Heavy"])

    submitted = st.form_submit_button("Submit Biodata")

    if submitted:
        # Store user input in session state (or a database if you have one)
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

# --- Display User Biodata (Only if submitted) ---
if "user_biodata" in st.session_state:  # Check if biodata has been submitted
    st.write("## Your Biodata")
    st.dataframe(pd.DataFrame([st.session_state.user_biodata]).T)  # Display in a table format

    # ... (Rest of your Streamlit app code using st.session_state.user_biodata)
    # For instance, in your exercise planning section:
    st.write("## Exercise Plan (Based on your biodata)")

    if st.session_state.user_biodata["Activity Level"] == "Moderate":
        st.write("- Walk for 30 minutes daily.")
        st.write("- Strength training 2 times a week.")

    # ... (Continue using st.session_state.user_biodata in your other sections)

else:
    st.info("Please submit your biodata to view personalized recommendations.")

# --- Main Page Layout ---
col1, col2 = st.columns([1, 3])  # Adjust column ratios as needed

with col1:
    st.write("# User Profile")
    if "user_biodata" in st.session_state: # Check if user_biodata exists
        st.dataframe(pd.DataFrame([st.session_state.user_biodata]).T, width=250)  # Corrected syntax
    else:
        st.write("Please submit your biodata first.") # Inform the user

with col2:
    # ... (Your other content)

    # --- Exercise Planning ---
    st.write("## Exercise Plan")

    if "user_biodata" in st.session_state: # Check if user_biodata exists
        if st.session_state.user_biodata["Activity Level"] == "Moderate":  # Corrected NameError
            st.write("- Walk for 30 minutes daily.")
            # ... (Rest of your exercise plan)
        # ... (Other activity level conditions)
    else:
        st.write("Please submit your biodata to view personalized recommendations.") # Inform the user
    # --- Diet Chart ---
    st.write("## Diet Chart")
    # (Your diet chart generation logic here based on user_biodata)
    # Example:
    st.write("- Eat plenty of fruits and vegetables.")
    st.write("- Limit processed foods.")
    # ... (Display a more detailed diet chart)

    # --- Medication Tracking ---
    st.write("## Medication Tracking")
    import streamlit as st
import pandas as pd
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time  # For time-related operations

# ... (Other imports and setup, including loading environment variables, etc.)

# Initialize scheduler (do this ONCE at the beginning of your script)
if "scheduler" not in st.session_state:
    st.session_state.scheduler = BackgroundScheduler()
    st.session_state.scheduler.start()

# ... (User biodata input form and other sections)

# --- Medication Tracking ---
st.write("## Medication Tracker")

if "medications" not in st.session_state:
    st.session_state.medications = {}

# Display existing medications as a checklist
if st.session_state.medications:
    medication_df = pd.DataFrame.from_dict(st.session_state.medications, orient='index')

    for med_name, med_data in st.session_state.medications.items():
        # Create a unique key for each checkbox to avoid issues with Streamlit reruns
        checkbox_key = f"{med_name}-taken-{datetime.date.today()}"  # Include the date in the key

        # Check if the checkbox state is already in the session state
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = False  # Initialize to False if not present

        # Create the checkbox and update the session state
        taken = st.checkbox(f"{med_name} (Dosage: {med_data['Dosage']})", key=checkbox_key)

        if taken:
            st.session_state[checkbox_key] = True  # Update the checkbox state

# ... (Medication input form - same as before)

# --- Medication Reminders ---
st.write("### Medication Reminders")

if st.session_state.medications:
    today = datetime.date.today()
    for med_name, med_data in st.session_state.medications.items():
        if med_data["Start Date"] <= today:
            st.write(f"**{med_name}**:")
            for reminder_time in med_data["Reminder Times"]:
                st.write(f"- {med_data['Frequency']} at {reminder_time.strftime('%I:%M %p')}")
                # Check if the dosage has been taken today
                taken_key = f"{med_name}-taken-{today}"
                if taken_key in st.session_state and st.session_state[taken_key]:
                    st.write("  ✅ Taken")  # Display a checkmark if taken
                else:
                    st.write("  ❌ Not Taken")  # Display a cross if not taken

        else:
            st.write(f"**{med_name}** will start on {med_data['Start Date']}")

else:
    st.info("No medications added yet.")


def schedule_reminders(medication_name):
    # ... (Same as before)
    # Example:
    medications = st.text_area("Enter your medications (comma-separated):")
    if st.button("Set Reminders"):
        # ... (Implement reminder logic using a scheduling library or external service)
        st.write("Reminders set!")

def send_reminder(medication_name):  # Improved reminder function
    st.balloons()
    st.write(f"Reminder: Time to take {medication_name}!")
    st.experimental_rerun()  # Refresh the UI to show the reminder immediately

# Stop the scheduler (same as before)

# ... (Rest of your Streamlit app code)
'''  # Example:
    medications = st.text_area("Enter your medications (comma-separated):")
    if st.button("Set Reminders"):
        # ... (Implement reminder logic using a scheduling library or external service)
        st.write("Reminders set!")'''


    # --- Chatbot (Moved to the main content area) ---
    # ... (Your existing chatbot code here, including chat history loading, display, and Gemini interaction)
try:
        st.session_state.messages = joblib.load(
            f'data/{st.session_state.chat_id}-st_messages'
        )
        st.session_state.gemini_history = joblib.load(
            f'data/{st.session_state.chat_id}-gemini_messages'
        )
        print('old cache')
except:
        st.session_state.messages = []
        st.session_state.gemini_history = []
        print('new_cache made')
        st.session_state.model = genai.GenerativeModel('gemini-pro')
        st.session_state.chat = st.session_state.model.start_chat(
        history=st.session_state.gemini_history,
    )

    # Display chat messages from history on app rerun
for message in st.session_state.messages:
        with st.chat_message(
            name=message['role'],
            avatar=message.get('avatar'),
        ):
            st.markdown(message['content'])

    # React to user input
if prompt := st.chat_input('Your message here...'):
        # Save this as a chat for later
        if st.session_state.chat_id not in past_chats.keys():
            past_chats[st.session_state.chat_id] = st.session_state.chat_title
            joblib.dump(past_chats, 'data/past_chats_list')
        # Display user message in chat message container
        with st.chat_message('user'):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append(
            dict(
                role='user',
                content=prompt,
            )
        )
        ## Send message to AI
        response = st.session_state.chat.send_message(
            prompt,
            stream=True,
        )
        # Display assistant response in chat message container
        with st.chat_message(
            name=MODEL_ROLE,
            avatar=AI_AVATAR_ICON,
        ):
            message_placeholder = st.empty()
            full_response = ''
            assistant_response = response
            # Streams in a chunk at a time
            for chunk in response:
                # Simulate stream of chunk
                # TODO: Chunk missing `text` if API stops mid-stream ("safety"?)
                for ch in chunk.text.split(' '):
                    full_response += ch + ' '
                    time.sleep(0.05)
                    # Rewrites with a cursor at end
                    message_placeholder.write(full_response + '▌')
            # Write full message with placeholder
            message_placeholder.write(full_response)

        # Add assistant response to chat history
        st.session_state.messages.append(
            dict(
                role=MODEL_ROLE,
                content=st.session_state.chat.history[-1].parts[0].text,
                avatar=AI_AVATAR_ICON,
            )
        )
        st.session_state.gemini_history = st.session_state.chat.history
        # Save to file
        joblib.dump(
            st.session_state.messages,
            f'data/{st.session_state.chat_id}-st_messages',
        )
        joblib.dump(
            st.session_state.gemini_history,
            f'data/{st.session_state.chat_id}-gemini_messages',
        )