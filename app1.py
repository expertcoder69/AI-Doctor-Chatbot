'''import time
import os
import joblib
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

load_dotenv()

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize session state variables
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None
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
if "medications" not in st.session_state:
    st.session_state.medications = {}
if "scheduler" not in st.session_state:
    st.session_state.scheduler = BackgroundScheduler()
    st.session_state.scheduler.start()
if "chat" not in st.session_state:
    st.session_state.chat = None

new_chat_id = f'{time.time()}'
MODEL_ROLE = 'ai'
AI_AVATAR_ICON = '👨🏾‍⚕️'

# Create a data/ folder if it doesn't already exist
try:
    os.makedirs('data/', exist_ok=True)  # Use os.makedirs with exist_ok
except Exception as e:
    st.error(f"Error creating data directory: {e}")

# Load past chats (if available)
try:
    past_chats = joblib.load('data/past_chats_list')
    st.session_state.past_chats = past_chats # Update session state
except FileNotFoundError:
    past_chats = {}
    st.session_state.past_chats = past_chats

# --- User Biodata Input Form ---
st.write("# User Biodata")

with st.form("user_biodata_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, value=25, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", min_value=0, value=170, step=1)
    weight = st.number_input("Weight (kg)", min_value=0, value=70, step=1)
    health_issues = st.text_area("Health Issues (comma-separated)", placeholder="e.g., Diabetes, Hypertension")
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
col1, col2 = st.columns([1, 3])

with col1:
    st.write("# User Profile")
    if st.session_state.user_biodata:
        st.dataframe(pd.DataFrame([st.session_state.user_biodata]).T, width=250)
    else:
        st.write("Please submit your biodata first.")

with col2:
    st.write('# Dr. Pashupathy 2.0 here!')
    st.write(' ഞാൻ പഷുപതി... ഡോക്ടർ പഷുപതി... ബൊംബെയിൽ MBBS, MD, MS, BSc, PhD, DDT, LSD ഒക്കെ കഴിഞ്ഞത്!')

    # --- Exercise Planning ---
    st.write("## Exercise Plan")
    if st.session_state.user_biodata:
        if st.session_state.user_biodata["Activity Level"] == "Moderate":
            st.write("- Walk for 30 minutes daily.")
            st.write("- Strength training 2 times a week.")
        # ... (Other activity level conditions)
    else:
        st.write("Please submit your biodata to view personalized recommendations.")

    # --- Medication Tracking ---
    st.write("## Medication Tracker")


    # Display existing medications as a checklist
    if st.session_state.medications:
        for med_name, med_data in st.session_state.medications.items():
            checkbox_key = f"{med_name}-taken-{datetime.date.today()}"
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = False
            taken = st.checkbox(f"{med_name} (Dosage: {med_data['Dosage']})", key=checkbox_key)

    # ... (Medication input form)
    st.write("### Add New Medication")  # Subheading for clarity

with st.form("add_medication_form"):  # Use a form for better organization
    medication_name = st.text_input("Medication Name", placeholder="Enter medication name")
    dosage = st.text_input("Dosage", placeholder="e.g., 10mg, 2 tablets")
    frequency = st.selectbox("Frequency", ["Once Daily", "Twice Daily", "Thrice Daily"], placeholder="Select frequency")
    start_date = st.date_input("Start Date", value=datetime.date.today())

    # Time pickers based on frequency (improved)
    reminder_times = []
    if frequency == "Once Daily":
        reminder_time = st.time_input("Reminder Time")
        if reminder_time:  # Check if a time was selected
            reminder_times = [reminder_time]
    elif frequency == "Twice Daily":
        col1, col2 = st.columns(2)  # Use columns for better layout
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
            st.error("Medication name is required.")  # More specific error message
        elif not reminder_times:  # Check if any reminder times were selected
            st.error("Please select at least one reminder time.")
        else:
            st.session_state.medications[medication_name] = {
                "Dosage": dosage,
                "Frequency": frequency,
                "Start Date": start_date,
                "Reminder Times": reminder_times,
            }
            st.success(f"Medication '{medication_name}' added successfully!")

            # Schedule reminders (after adding medication)
            #schedule_reminders(medication_name)  # Call function to schedule reminders

            # Clear the form after submission (optional)
            st.rerun() # Refresh the UI to clear the form

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

    # --- Chatbot ---
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
        )'''
import time
import os
import joblib
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

load_dotenv()

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize session state variables
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None
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
if "medications" not in st.session_state:
    st.session_state.medications = {}
if "scheduler" not in st.session_state:
    st.session_state.scheduler = BackgroundScheduler()
    st.session_state.scheduler.start()
if "chat" not in st.session_state:
    st.session_state.chat = None
if "model" not in st.session_state:
    st.session_state.model = None

new_chat_id = f'{time.time()}'
MODEL_ROLE = 'ai'
AI_AVATAR_ICON = '👨🏾‍⚕️'

# Create a data/ folder if it doesn't already exist
try:
    os.makedirs('data/', exist_ok=True)
except Exception as e:
    st.error(f"Error creating data directory: {e}")

# Load past chats (if available)
try:
    past_chats = joblib.load('data/past_chats_list')
    st.session_state.past_chats = past_chats
except FileNotFoundError:
    past_chats = {}
    st.session_state.past_chats = past_chats

# --- User Biodata Input Form ---
st.write("# User Biodata")

with st.form("user_biodata_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, value=25, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", min_value=0, value=170, step=1)
    weight = st.number_input("Weight (kg)", min_value=0, value=70, step=1)
    health_issues = st.text_area("Health Issues (comma-separated)", placeholder="e.g., Diabetes, Hypertension")
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
        st.rerun()

# --- Main Page Layout ---
col1, col2 = st.columns([1, 3])

with col1:
    st.write("# User Profile")
    if st.session_state.user_biodata:
        st.dataframe(pd.DataFrame([st.session_state.user_biodata]).T, width=250)
    else:
        st.write("Please submit your biodata first.")

with col2:
    st.write('# Dr. Pashupathy 2.0 here!')
    st.write(' ഞാൻ പഷുപതി... ഡോക്ടർ പഷുപതി... ബൊംബെയിൽ MBBS, MD, MS, BSc, PhD, DDT, LSD ഒക്കെ കഴിഞ്ഞത്!')

    # --- Exercise Planning ---
    st.write("## Exercise Plan")
    if st.session_state.user_biodata:
        if st.session_state.user_biodata["Activity Level"] == "Moderate":
            st.write("- Walk for 30 minutes daily.")
            st.write("- Strength training 2 times a week.")
        # ... (Other activity level conditions)
    else:
        st.write("Please submit your biodata to view personalized recommendations.")


    # --- Medication Tracking ---
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
        frequency = st.selectbox("Frequency", ["Once Daily", "Twice Daily", "Thrice Daily"], placeholder="Select frequency")
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
                st.session_state.medications[medication_name] = {
                    "Dosage": dosage,
                    "Frequency": frequency,
                    "Start Date": start_date,
                    "Reminder Times": reminder_times,
                }
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
                        st.write("  ✅ Taken")
                    else:
                        st.write("  ❌ Not Taken")
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