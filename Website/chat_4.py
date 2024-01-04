import streamlit as st
from datetime import date, datetime, timedelta
import json
import pytz

from firebase_admin import firestore
import requests
from time import time, sleep
from chat_bot_4 import ChatBot
from util import local_settings, service
from prompt_list_4 import prompts
from functions4 import functions
from clinic_info import *

def app():
    if 'db' not in st.session_state:
        st.session_state.db = ''

    db=firestore.client()
    st.session_state.db=db
    # st.title('  :violet[DOC-IT-RIGHT]  :sunglasses:')
    
    if st.session_state.username=='':

        st.text('Login to be able to use the chat!!')

    else:
        def initialize() -> None:
            """
            Initialize the app
            """
            with st.expander("Bot Configuration"):
                selected_prompt = st.selectbox(label="Prompt", options=[prompt['name'] for prompt in prompts])
                selected_prompt_dict = next((prompt for prompt in prompts if prompt['name'] == selected_prompt), None)
                system_behavior = st.text_area(label="Prompt", value=selected_prompt_dict["prompt"])

            st.sidebar.title("🤖 🥼")

            if "chatbot" not in st.session_state:
                st.session_state.chatbot = ChatBot(system_behavior, functions)

            with st.sidebar:
                st.markdown(f"ChatBot in use: <font color='cyan'>{st.session_state.chatbot.__str__()}</font>", unsafe_allow_html=True)


        # ------------- Display History Message -------------

        def display_history_messages():
            # Display chat messages from history on app rerun
            for message in st.session_state.chatbot.memory:
                if message["role"] != "system":
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])


        # --------------- Display User Message ---------------

        def display_user_msg(message: str):
            """
            Display user message in chat message container
            """

            with st.chat_message("user", avatar="😎"):
                st.markdown(message)


        # ------------------ Display Assistant Message ------------------

        def display_assistant_msg(message: str, animated=True):
            """
            Display assistant message
            """

            if animated:
                with st.chat_message("assistant", avatar="🤖"):
                    message_placeholder = st.empty()

                    # Simulate stream of response with milliseconds delay
                    full_response = ""
                    for chunk in message.split():
                        full_response += chunk + " "
                        sleep(0.05)

                        # Add a blinking cursor to simulate typing
                        message_placeholder.markdown(full_response + "▌")

                    message_placeholder.markdown(full_response)
                    
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message)


        #-----------GLOBAL FUNCTIONS----------
        def appointment_checking(start_date_time=None, end_date_time=None, timezone=None):
            try:
                # Chech if given date is in the past
                if start_date_time < datetime.now(timezone):
                    return "Please enter valid date and time. The date provided is in the past."
                
                else:
                    # Check if the appointment is in a Saturday
                    if start_date_time.strftime("%A") == "Saturday":
                        # If given time is within working hours
                        if start_date_time.time() >= limit1 and start_date_time.time() <= limit3:
                            events_result = service.events().list(calendarId='primary', timeMin=start_date_time.isoformat(), timeMax=end_date_time.isoformat()).execute()
                            if events_result['items']:
                                return "Sorry slot is not available."
                            else:
                                return "The slot requested is available."
                        else:
                            return "Please try to check an appointment within working hours, which are from 9AM to 12PM on Saturdays."
                    
                    else:
                        if start_date_time.time() >= limit1 and start_date_time.time() <= limit2:
                            end_date_time = start_date_time + timedelta(minutes=30)
                            events_result = service.events().list(calendarId='primary', timeMin=start_date_time.isoformat(), timeMax=end_date_time.isoformat()).execute()
                            if events_result['items']:
                                return "Sorry slot is not available."
                            else:
                                return "The slot requested is available."
                        else:
                            return "Please try to check an appointment within working hours, which is 9 AM to 8 PM."
            
            except:
                return "We are facing some issues while processing your booking request, please try again."


        def get_available_time_slots(doctor, day):
            # Function to get available time slots for a specific doctor on a given day
            doctor_schedule = doctor_time_tables.get(doctor, {}).get(day, {})
            
            if not doctor_schedule:
                return []
            
            else:
                start_time = datetime.strptime(doctor_schedule.get('start', '09:00:00'), "%H:%M:%S").time()
                end_time = datetime.strptime(doctor_schedule.get('end', '20:00:00'), "%H:%M:%S").time()

                available_times = []
                current_time = start_time

                while current_time <= end_time:
                    available_times.append(current_time.strftime("%H:%M:%S"))
                    current_time = (datetime.combine(date.today(), current_time) + timedelta(minutes=30)).time()

                return available_times
            

        def is_time_in_range(selected_time, times_list):
            for time_obj in times_list:
                if time_obj == selected_time.strftime("%H:%M:%S"):
                    return "In time range"
            return "Not in time range"


        def get_available_times_message(doctor, day, available_times):
            if not available_times:
                return f"{doctor} is not available on {day}."
            else:
                return f"{doctor} is available on {day} at the following times: {', '.join(available_times)}."


        def doctor_checking(start_date_time=None, doctor=None):

            existing_doctors = list(doctor_time_tables.keys())

            if doctor is not None:
                if doctor not in existing_doctors:
                    return "Please choose a valid doctor from the list: " + ", ".join(existing_doctors)

                else:   
                    day_of_week = start_date_time.strftime("%A").lower()
                    doctor_schedule = get_available_time_slots(doctor, day_of_week)
                    in_doctor_slots = is_time_in_range(start_date_time.time(), doctor_schedule) == "In time range"
                    
                    if not doctor_schedule or not in_doctor_slots:
                        available_times_message = get_available_times_message(doctor, day_of_week, doctor_schedule)
                        
                        return f"{doctor} is not available in the desiered schedule. {available_times_message} Please choose a valid schedule."
                    else:
                        return "Doctor and time are compatible."
            else:
                return "No doctor specified"

        #---------------BOOKING----------------
        def appointment_booking(arguments):
            try:
                # Handling the date and time
                provided_date_str =  str(datetime.strptime(json.loads(arguments)['book_date'], "%Y-%m-%d").date())
                provided_time_str = str(datetime.strptime(json.loads(arguments)['book_time'], "%H:%M:%S").time()) #.replace("PM","").replace("AM","").strip()
                start_date_time_str = provided_date_str + " " + provided_time_str
                timezone = pytz.timezone('Europe/Lisbon')
                start_date_time = timezone.localize(datetime.strptime(start_date_time_str, "%Y-%m-%d %H:%M:%S"))
                end_date_time = start_date_time + timedelta(minutes=30)

                # Handling other information
                email_address = json.loads(arguments)['email_address']
                doctor = json.loads(arguments)['doctor']
                
                
                # Checking if the requested slot is available
                if provided_date_str and provided_time_str and email_address and doctor:
                    # Check if slot in clinics' working hours and slot is not already booked
                    slot_checking = appointment_checking(start_date_time, end_date_time, timezone)
                    # Checks if doctor is available at the given time
                    doc_checking = doctor_checking(start_date_time, doctor)

                    while doc_checking != "Doctor and time are compatible.":
                        return doc_checking        

                    while slot_checking != "The slot requested is available.":
                        return slot_checking
                
                    if doc_checking == "Doctor and time are compatible." and slot_checking == "The slot requested is available.":        
            
                        event = {
                            'summary': doctor,
                            'location': "Lisbon",
                            'description': "This appointment was scheduled by the chatbot",
                            
                            'start': {
                                'dateTime': start_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                'timeZone': 'Europe/Lisbon',
                            },
                            'end': {
                                'dateTime': end_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                'timeZone': 'Europe/Lisbon',
                            },
                            'attendees': [
                                {'email': email_address},
                            ],
                                                
                            'reminders': {
                                'useDefault': False,
                                'overrides': [
                                    {'method': 'email', 'minutes': 24 * 60},
                                    {'method': 'popup', 'minutes': 10},
                                ],
                            }
                        }
                        service.events().insert(calendarId='primary', body=event).execute()
                        return "Appointment added successfully."
                    
                    else:
                        return "The doctor is already fully booked for the day."
                        
                else:
                    return "Please provide all necessary details: Date, time, email and doctor."
            
            except:
                return "We are facing an error while processing your request. Please try again."

        #---------------CANCEL----------------
        def appointment_delete(arguments):
            try:
                provided_date =  str(datetime.strptime(json.loads(arguments)['del_date'], "%Y-%m-%d").date())
                provided_time = str(datetime.strptime(json.loads(arguments)['del_time'], "%H:%M:%S").time())
                email_address = json.loads(arguments)['email_address']

                if provided_date and provided_time and email_address:
                    start_date_time = provided_date + " " + provided_time
                    timezone = pytz.timezone('Europe/Lisbon')
                    start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))
                    if start_date_time < datetime.now(timezone):
                        return "Make sure you inserted the correct date and time. The date provided is in the past."
                    else:
                        events = service.events().list(calendarId="primary").execute()
                        id = ""
                        for event in events['items']:
                            if event['attendees'][0]['email'] == email_address:
                                if datetime.fromisoformat(str(event['start']['dateTime'])) == datetime.fromisoformat(str(start_date_time)):
                                    id = event['id']
                        if id:
                            service.events().delete(calendarId='primary', eventId=id).execute()
                            return "Appointment deleted successfully."
                        else:
                            return "No registered event found on your id."
                else:
                    return "Please provide all necessary details: Appointment date, Appointment time and Email address."
            except:
                return "We are facing an error while processing your cancelation. Please try again."

            
        def check_event(email_address, start_date_time):
            events = service.events().list(calendarId="primary").execute()  #all the events presented in google calendar
            id = ""
            final_event = None
            for event in events['items']:
                if event['attendees'][0]['email'] == email_address and datetime.fromisoformat(str(event['start']['dateTime'])) == datetime.fromisoformat(str(start_date_time)): #if the email exists in the attendees on the given date and time
                    id = event['id']
                    final_event = event

            if final_event:
                id = final_event['id']
                return "Appointments was found.", id
            else:
                return "Your email is not assigned to any appointment. Please try again."
            
            
        def appointment_reschedule(arguments):
            try:
                original_date_str =  str(datetime.strptime(json.loads(arguments)['del_date'], "%Y-%m-%d").date())
                original_time_str = str(datetime.strptime(json.loads(arguments)['del_time'], "%H:%M:%S").time()) #.replace("PM","").replace("AM","").strip()
                new_date_str =  str(datetime.strptime(json.loads(arguments)['book_date'], "%Y-%m-%d").date())
                new_time_str = str(datetime.strptime(json.loads(arguments)['book_time'], "%H:%M:%S").time())
                original_start_date_time_str = original_date_str + " " + original_time_str
                new_start_date_time_str = new_date_str + " " + new_time_str

                timezone = pytz.timezone('Europe/Lisbon')
                original_start_date_time = timezone.localize(datetime.strptime(original_start_date_time_str, "%Y-%m-%d %H:%M:%S"))
                new_start_date_time = timezone.localize(datetime.strptime(new_start_date_time_str, "%Y-%m-%d %H:%M:%S"))
                new_end_date_time = new_start_date_time + timedelta(minutes=30)

                email_address = json.loads(arguments)['email_address']
                doctor = json.loads(arguments)['doctor']
                
                check, id = check_event(email_address, original_start_date_time)

                if original_date_str and original_time_str and email_address and doctor:
                    
                    if check == "Appointments was found.":

                        #Confirm that the new date is available in the calendar and with the doctor
                        slot_checking = appointment_checking(new_start_date_time, new_end_date_time, timezone) 
                        doc_checking = doctor_checking(new_start_date_time, doctor)

                        while doc_checking != "Doctor and time are compatible.":
                            return doc_checking        

                        while slot_checking != "The slot requested is available.":
                            return slot_checking 
                        
                        if doc_checking == "Doctor and time are compatible." and slot_checking == "The slot requested is available.":

                            event = {
                                'summary': doctor,
                                'location': "Lisbon",
                                'description': "This appointment was scheduled by the chatbot",
                                
                                'start': {
                                    'dateTime': new_start_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Europe/Lisbon',
                                },
                                'end': {
                                    'dateTime': new_end_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    'timeZone': 'Europe/Lisbon',
                                },
                                'attendees': [
                                    {'email': email_address},
                                ],
                                                    
                                'reminders': {
                                    'useDefault': False,
                                    'overrides': [
                                        {'method': 'email', 'minutes': 24 * 60},
                                        {'method': 'popup', 'minutes': 10},
                                    ]
                                }
                            }
                            service.events().delete(calendarId='primary', eventId=id).execute()
                            service.events().insert(calendarId='primary', body=event).execute()

                            return "Appointment rescheduled successfully."
                    else:
                        return "No registered event found on that id"        
                    
                else:
                    return "Please provide all necessary details:  Appointment date, Appointment time and doctor."
        
            except:
                return "We are enable to process. Please try again."
            


        # MAIN ----------------------------------------------------------------------------------------------------------------------------------
        #if __name__ == "chat_4":
        initialize()


        # ---------------------------- Display History ------------------------------------
        display_history_messages()

        if prompt := st.chat_input("Type your request..."):

            # ---------------------------- Request & Response ----------------------------
            #if system == 'medicine':
            display_user_msg(message=prompt)
            assistant_response = st.session_state.chatbot.generate_response(message=prompt, langchain=True)
            display_assistant_msg(message=assistant_response)

            # else:
            #     display_user_msg(message=prompt)
            #     assistant_response = st.session_state.chatbot.generate_response(message=prompt)
            #     if assistant_response.content:
            #         display_assistant_msg(message=assistant_response.content)
            #     else:
            #         fn_name = assistant_response.tool_calls[0].function.name
            #         arguments = assistant_response.tool_calls[0].function.arguments
            #         function = locals()[fn_name]
            #         result = function(arguments)
            #         display_assistant_msg(message=result)


        # ----------------------------------- Sidebar -----------------------------------
        with st.sidebar:
            with st.expander("Information"):
                if local_settings.OPENAI_API_KEY:
                    st.write(f"🔑 Key loaded: {local_settings.OPENAI_API_KEY[0:6]}...")

                st.text("💬 MEMORY")
                st.write(st.session_state.chatbot.memory)

