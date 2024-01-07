import streamlit as st
from datetime import date, datetime, timedelta
import json
import pytz
import numpy as np
import pandas as pd

from firebase_admin import firestore
# import requests
from time import sleep #, time
from chat_bot import DrChatBot
from util import service #, local_settings
from info_files.prompt_list import prompts
from functions import *
from info_files.clinic_info import *

def app():

    # Initialize our firestore database
    if 'db' not in st.session_state:
        st.session_state.db = ''
    db=firestore.client()
    st.session_state.db=db

    # If user is not logged in
    if st.session_state.username=='':
        st.text('Login to be able to use the chat!!')

    # If user is logged in
    else:
        def initialize() -> None:
            """
            Initialize the app
            """

            # Select the chatbot's behavior
            with st.expander("Bot Configuration", expanded=True):
                # Retrieves the selected prompt from st.session_state if it exists. Uses the first prompt as a default.
                selected_prompt = st.session_state.get("selected_prompt", prompts[0]['name'])
                selected_prompt = st.selectbox(label="Prompt", options=[prompt['name'] for prompt in prompts], index=prompts.index(next((prompt for prompt in prompts if prompt['name'] == selected_prompt), None)))

                # Retrieve the selected prompt's entire dictionary
                selected_prompt_dict = next((prompt for prompt in prompts if prompt['name'] == selected_prompt), None)

                # Use st.session_state to store and update the system_behavior variable
                st.session_state.system_behavior = selected_prompt_dict.get("prompt", "")
                st.text_area(label="Prompt", value=selected_prompt_dict.get("description", ""))

                # Add a button to trigger the update
                if st.button("Click here to update system"):
                    st.session_state.chatbot = DrChatBot(st.session_state.system_behavior, functions)
            
            # Store the selected prompt in st.session_state for persistence across pages
            st.session_state.selected_prompt = selected_prompt
            
            # Check if the chatbot is not in the session state or if the button was pressed
            if "chatbot" not in st.session_state or st.button("Restart ChatBot"):
                st.session_state.chatbot = DrChatBot(st.session_state.system_behavior, functions)

            # Display the chatbot's name
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


        #-----------GLOBAL SCHEDUEING BOT FUNCTIONS----------
        def appointment_checking(start_date_time=None, end_date_time=None, timezone=None):
            """
            Check if the slot for the requested appointment is available
            """

            try:
                # Chech if given date is in the past
                if start_date_time < datetime.now(timezone):
                    return "Please enter valid date and time. The date provided is in the past."
                
                else:
                    # Check if the appointment is in a Saturday
                    if start_date_time.strftime("%A") == "Saturday":
                        
                        # If given time is within working hours
                        if start_date_time.time() >= limit1 and start_date_time.time() <= limit3:
                            
                            # Get all events in the calendar
                            events_result = service.events().list(calendarId='primary', timeMin=start_date_time.isoformat(), timeMax=end_date_time.isoformat()).execute()
                            
                            # Tell the user if the slot is or isn't available
                            if events_result['items']:
                                return "Sorry slot is not available."
                            else:
                                return "The slot requested is available."
                        
                        # Tell the user the time slot is not within working hours
                        else:
                            return "Please try to check an appointment within working hours, which are from 9AM to 12PM on Saturdays."
                    
                    # Do the same for week days
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
            """
            Get the available time slots for a specific doctor on a given day
            """

            # Get the doctor's schedule for the given day
            doctor_schedule = doctor_time_tables.get(doctor, {}).get(day, {})
            
            # Check if the doctor is available on the given day
            if not doctor_schedule:
                return []
            
            else:
                # Get the possible start times for appointments with the given doctor
                
                start_time = datetime.strptime(doctor_schedule.get('start', '09:00:00'), "%H:%M:%S").time()
                end_time = datetime.strptime(doctor_schedule.get('end', '20:00:00'), "%H:%M:%S").time()

                available_times = []
                current_time = start_time

                while current_time <= end_time:
                    available_times.append(current_time.strftime("%H:%M:%S"))
                    current_time = (datetime.combine(date.today(), current_time) + timedelta(minutes=30)).time()

                return available_times
            

        def is_time_in_range(selected_time, times_list):
            """
            Check if the requested time is within the doctor's working hours
            """

            for time_obj in times_list:

                if time_obj == selected_time.strftime("%H:%M:%S"):
                    return "In time range"
                
            return "Not in time range"
        

        def available_doctor(strat_date_time):
            """
            Get the list available doctors for a requested time slot
            """

            available_doctors = []
            day_of_week = strat_date_time.strftime("%A").lower()

            for doctor in doctor_time_tables.keys():

                doctor_schedule = get_available_time_slots(doctor, day_of_week)
                in_doctor_slots = is_time_in_range(strat_date_time.time(), doctor_schedule) == "In time range"
                
                if doctor_schedule and in_doctor_slots:
                    available_doctors.append(doctor)
            
            # Return the list of available doctors
            return available_doctors


        def get_available_times_message(doctor, day, available_times):
            """
            Get the message to be displayed to the user regarding the availability on the requested time
            """
            if not available_times:
                return f"{doctor} is not available on {day}."
            else:
                return f"{doctor} is only available on {day}s at the following times: {', '.join(available_times)}. Please choose a valid schedule."


        def doctor_checking(start_date_time=None, doctor=None):
            """
            Check if the doctor is available at the requested time
            """

            # Get the existing doctors
            existing_doctors = list(doctor_time_tables.keys())

            # Check if the doctor exists
            if doctor is not None:

                if doctor not in existing_doctors:
                    return "Please choose a valid doctor from the list: " + ", ".join(existing_doctors)

                else:
                    # Get the necessary information to check if the doctor works at a given time 
                    day_of_week = start_date_time.strftime("%A").lower()
                    doctor_schedule = get_available_time_slots(doctor, day_of_week)
                    in_doctor_slots = is_time_in_range(start_date_time.time(), doctor_schedule) == "In time range"
                    available_doctors = available_doctor(start_date_time)
                    
                    # If the time and doctor are not compatible, return a message with the available doctors
                    if not doctor_schedule or not in_doctor_slots:
                        available_times_message = get_available_times_message(doctor, day_of_week, doctor_schedule)
                        
                        return f"{available_times_message} The doctor{' available is' if len(available_doctors) == 1 else 's available are'}: {', '.join(available_doctors)}."
                    else:
                        return "Doctor and time are compatible."
            else:
                return "No doctor specified"

        #---------------BOOKING----------------
        def appointment_booking(arguments):
            """
            Book an appointment
            """

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
                parking_spaces = json.loads(arguments)['parking']
                special_requests = json.loads(arguments)['special_requests']
                pay_in_advance = json.loads(arguments)['pay_in_advance']
                
                # Checking if the requested slot is available
                if provided_date_str and provided_time_str and email_address and doctor and parking_spaces is not None and special_requests is not None and pay_in_advance is not None:
                    # Check if slot in clinics' working hours and slot is not already booked
                    slot_checking = appointment_checking(start_date_time, end_date_time, timezone)
                    # Checks if doctor is available at the given time
                    doc_checking = doctor_checking(start_date_time, doctor)

                    # Make sure the doctor and time are compatible and the slot is available
                    while doc_checking != "Doctor and time are compatible.":
                        return doc_checking        

                    while slot_checking != "The slot requested is available.":
                        return slot_checking
                
                    if doc_checking == "Doctor and time are compatible." and slot_checking == "The slot requested is available.":        
                        
                        # Get data from the database
                        patient_data = db.collection('Patients').document(st.session_state.username).get()
                        patient_data_dict = patient_data.to_dict()

                        # Get the necessary information to make the prediction
                        AppointmentWeekNumber = int(start_date_time.strftime("%U"))
                        AppointmentDayOfMonth = int(start_date_time.strftime("%d"))
                        AppointmentHour = start_date_time.time().hour + start_date_time.time().minute / 60 + start_date_time.time().second / 3600
                        WeekendConsults = patient_data_dict["WeekendConsults"]
                        WeekdayConsults = patient_data_dict["WeekdayConsults"]
                        Adults = patient_data_dict["Adults"]
                        Children = float(patient_data_dict["Children"])
                        Babies = patient_data_dict["Babies"]
                        AffiliatedPatient = patient_data_dict["AffiliatedPatient"]
                        PreviousAppointments = patient_data_dict["PreviousAppointments"]
                        PreviousNoShows = patient_data_dict["PreviousNoShows"]
                        LastMinutesLate = patient_data_dict["LastMinutesLate"]
                        OnlineBooking = 1 
                        AppointmentChanges = 0
                        time_difference = start_date_time.date() - datetime.today().date()
                        BookingToConsultDays = time_difference.days
                        ParkingSpaceBooked = parking_spaces
                        SpecialRequests = special_requests
                        NoInsurance = patient_data_dict["NoInsurance"]
                        ExtraExamsPerConsult = patient_data_dict["ExtraExamsPerConsult"]
                        DoctorAssigned = doctor_to_ID.get(doctor, None)
                        ConsultPriceEuros = 30.0
                        PaidinAdvance = pay_in_advance/100
                        CountryofOriginHDI = patient_data_dict["CountryofOriginHDI"]

                        # Make the prediction
                        model_data = np.array([[0,AppointmentWeekNumber,AppointmentDayOfMonth,AppointmentHour,WeekendConsults,WeekdayConsults,Adults,Children,Babies,0,AffiliatedPatient,PreviousAppointments,0,PreviousNoShows,LastMinutesLate,OnlineBooking,AppointmentChanges,BookingToConsultDays,ParkingSpaceBooked,SpecialRequests,NoInsurance,ExtraExamsPerConsult,0,DoctorAssigned,ConsultPriceEuros,0,PaidinAdvance,0,0,CountryofOriginHDI]])
                        dataframe_scaler = pd.DataFrame(model_data, columns=features_scaler)
                        scaled_data = scaler.transform(dataframe_scaler)
                        scaled_dataframe = pd.DataFrame(scaled_data, columns=features_scaler)
                        model_dataframe = scaled_dataframe[feature_names].copy()
                        model_dataframe.rename(columns={'CountryofOriginHDI (Year-1)': 'CountryofOriginHDI'}, inplace=True)
                        prediction = model.predict(model_dataframe)
                        prediction = 'show' if int(prediction[0]) == 0 else 'no-show'

                        # Define the event and add it to the calendar
                        event = {
                            'summary': doctor,
                            'location': "Lisbon",
                            'description': f"This appointment was scheduled by the chatbot. Prediction is: {prediction}",
                            
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

                        ev = service.events().insert(calendarId='primary', body=event).execute()

                        # Add the appointment to the database
                        id = ev['id']
                        ap_data={'AppointmentWeekNumber':AppointmentWeekNumber,
                                 'AppointmentDayOfMonth': AppointmentDayOfMonth,
                                 'AppointmentHour': AppointmentHour,
                                 'OnlineBooking':OnlineBooking,
                                 'AppointmentChanges':AppointmentChanges,
                                 'BookingToConsultDays':BookingToConsultDays,
                                 'ParkingSpaceBooked':ParkingSpaceBooked,
                                 'SpecialRequests':SpecialRequests,
                                 'DoctorAssigned':DoctorAssigned,
                                 'ConsultPriceEuros':ConsultPriceEuros,
                                 '%PaidinAdvance':PaidinAdvance,
                                 'NoShow':'show' if prediction == 0 else 'no-show',
                                 'Username':st.session_state.username,
                                 'id':id
                                 }
                        db.collection('Appointments').document(id).set(ap_data)

                        # Update the patient's data
                        update_data = {"WeekendConsults": WeekendConsults + 1 if start_date_time.strftime("%A") == "Saturday" else WeekendConsults,
                               "WeekdayConsults": WeekdayConsults + 1 if start_date_time.strftime("%A") != "Saturday" else WeekdayConsults,
                               "PreviousAppointments": PreviousAppointments + 1
                               }
                        db.collection('Patients').document(st.session_state.username).update(update_data)
                        
                        return "Appointment added successfully."
                    
                    else:
                        return "The doctor is already fully booked for the day."
                        
                else:
                    return "Please provide all necessary details: Date, time, email, doctor, parking space requirement, special requests and paid in advance amount."
            
            except Exception as e:
                import traceback
                traceback.print_exc()
                return "We are facing an error while processing your request. Please try again."

        #---------------CANCEL----------------
        def appointment_delete(arguments):
            """
            Delete an appointment
            """
            try:
                # Handling the provided data
                provided_date =  str(datetime.strptime(json.loads(arguments)['del_date'], "%Y-%m-%d").date())
                provided_time = str(datetime.strptime(json.loads(arguments)['del_time'], "%H:%M:%S").time())
                email_address = json.loads(arguments)['email_address']

                if provided_date is not None and provided_time is not None and email_address is not None :
                    
                    # Dealing with the date and time
                    start_date_time = provided_date + " " + provided_time
                    timezone = pytz.timezone('Europe/Lisbon')
                    start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))

                    if start_date_time < datetime.now(timezone):
                        return "Make sure you inserted the correct date and time. The date provided is in the past."
                    
                    else:
                        # Get events from the calendar
                        events = service.events().list(calendarId="primary").execute()
                        id = ""

                        # Check if the event exists
                        for event in events['items']:

                            # Check if the email is valid
                            if event['attendees'][0]['email'] == email_address:
                                
                                # Get the id for the specified event
                                if datetime.fromisoformat(str(event['start']['dateTime'])) == datetime.fromisoformat(str(start_date_time)):
                                    id = event['id']
                        if id:
                            # Delete the event from the calendar and the database
                            service.events().delete(calendarId='primary', eventId=id).execute()
                            db.collection('Appointments').document(id).delete()
                            return "Appointment deleted successfully."
                        
                        else:
                            return "No registered event found on your id."
                        
                else:
                    return "Please provide all necessary details: Appointment date, Appointment time, and Email addres."
                
            except:
                return "We are facing an error while processing your cancelation. Please try again."

            
        def check_event(email_address, start_date_time):
            """
            Check if an event exists
            """

            # Get the events from the calendar
            events = service.events().list(calendarId="primary").execute()
            id = ""
            final_event = None

            # Check if the event exists
            for event in events['items']:

                # Check if the email is valid and event exists on the given date and time
                if event['attendees'][0]['email'] == email_address and datetime.fromisoformat(str(event['start']['dateTime'])) == datetime.fromisoformat(str(start_date_time)): 
                    # Get the id for the specified event
                    id = event['id']
                    final_event = event

            if final_event:
                id = final_event['id']
                return "Appointments was found.", id
            else:
                return "Your email is not assigned to any appointment. Please try again."
            
            
        def appointment_reschedule(arguments):
            """
            Reschedule an appointment
            """
            try:
                # Handling the date and time data
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

                # Handling other information
                email_address = json.loads(arguments)['email_address']
                doctor = json.loads(arguments)['doctor']
                parking_spaces = json.loads(arguments)['book_parking']
                special_requests = json.loads(arguments)['book_special_requests']
                pay_in_advance = json.loads(arguments)['book_pay_in_advance']
                
                # Check if the event exists
                check, original_id = check_event(email_address, original_start_date_time)

                if original_date_str and original_time_str and email_address and doctor and parking_spaces is not None and special_requests is not None and pay_in_advance is not None and new_date_str and new_time_str:
                    
                    if check == "Appointments was found.":

                        #Confirm that the new date is available in the calendar and with the doctor
                        slot_checking = appointment_checking(new_start_date_time, new_end_date_time, timezone) 
                        doc_checking = doctor_checking(new_start_date_time, doctor)

                        # Make sure the doctor and time are compatible and the slot is available
                        while doc_checking != "Doctor and time are compatible.":
                            return doc_checking        

                        while slot_checking != "The slot requested is available.":
                            return slot_checking 
                        
                        if doc_checking == "Doctor and time are compatible." and slot_checking == "The slot requested is available.":
                            
                            # Get the data from the database
                            patient_data = db.collection('Patients').document(st.session_state.username).get()
                            patient_data_dict = patient_data.to_dict()
                            appointment_data = db.collection('Appointments').document(original_id).get()
                            appointment_data_dict = appointment_data.to_dict()

                            # Get the necessary information to make the prediction
                            AppointmentWeekNumber = int(new_start_date_time.strftime("%U"))
                            AppointmentDayOfMonth = int(new_start_date_time.strftime("%d"))
                            AppointmentHour = new_start_date_time.time().hour + new_start_date_time.time().minute / 60 + new_start_date_time.time().second / 3600
                            if new_start_date_time.strftime("%A") == "Saturday" and original_start_date_time.strftime("%A") != "Saturday":
                                WeekendConsults = patient_data_dict["WeekendConsults"] + 1
                                WeekdayConsults = patient_data_dict["WeekdayConsults"] - 1
                            elif new_start_date_time.strftime("%A") != "Saturday" and original_start_date_time.strftime("%A") == "Saturday":
                                WeekendConsults = patient_data_dict["WeekendConsults"] - 1
                                WeekdayConsults = patient_data_dict["WeekdayConsults"] + 1
                            else:
                                WeekendConsults = patient_data_dict["WeekendConsults"]
                                WeekdayConsults = patient_data_dict["WeekdayConsults"]
                            Adults = patient_data_dict["Adults"]
                            Children = float(patient_data_dict["Children"])
                            Babies = patient_data_dict["Babies"]
                            AffiliatedPatient = patient_data_dict["AffiliatedPatient"]
                            PreviousAppointments = patient_data_dict["PreviousAppointments"]
                            PreviousNoShows = patient_data_dict["PreviousNoShows"]
                            LastMinutesLate = patient_data_dict["LastMinutesLate"]
                            OnlineBooking = 1 
                            AppointmentChanges = appointment_data_dict['AppointmentChanges'] + 1
                            time_difference = new_start_date_time.date() - datetime.today().date()
                            BookingToConsultDays = time_difference.days
                            ParkingSpaceBooked = parking_spaces
                            SpecialRequests = special_requests
                            NoInsurance = patient_data_dict["NoInsurance"]
                            ExtraExamsPerConsult = patient_data_dict["ExtraExamsPerConsult"]
                            DoctorAssigned = doctor_to_ID.get(doctor, None)
                            ConsultPriceEuros = 30.0
                            PaidinAdvance = pay_in_advance/100
                            CountryofOriginHDI = patient_data_dict["CountryofOriginHDI"]

                            # Make the prediction
                            model_data = np.array([[0,AppointmentWeekNumber,AppointmentDayOfMonth,AppointmentHour,WeekendConsults,WeekdayConsults,Adults,Children,Babies,0,AffiliatedPatient,PreviousAppointments,0,PreviousNoShows,LastMinutesLate,OnlineBooking,AppointmentChanges,BookingToConsultDays,ParkingSpaceBooked,SpecialRequests,NoInsurance,ExtraExamsPerConsult,0,DoctorAssigned,ConsultPriceEuros,0,PaidinAdvance,0,0,CountryofOriginHDI]])
                            dataframe_scaler = pd.DataFrame(model_data, columns=features_scaler)
                            scaled_data = scaler.transform(dataframe_scaler)
                            scaled_dataframe = pd.DataFrame(scaled_data, columns=features_scaler)
                            model_dataframe = scaled_dataframe[feature_names].copy()
                            model_dataframe.rename(columns={'CountryofOriginHDI (Year-1)': 'CountryofOriginHDI'}, inplace=True)
                            prediction = model.predict(model_dataframe)
                            prediction = 'show' if int(prediction[0]) == 0 else 'no-show'

                            # Delete the previous event, define the new event, and add it to the calendar
                            event = {
                                'summary': doctor,
                                'location': "Lisbon",
                                'description': f"This appointment was scheduled by the chatbot. Prediction is: {prediction}",
                                
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
                            service.events().delete(calendarId='primary', eventId=original_id).execute()
                            db.collection('Appointments').document(original_id).delete()
                            ev = service.events().insert(calendarId='primary', body=event).execute()
                            new_id = ev['id']

                            # Set the new appointment in the database
                            data={'AppointmentWeekNumber':AppointmentWeekNumber,
                                  'AppointmentDayOfMonth': AppointmentDayOfMonth,
                                  'AppointmentHour': AppointmentHour,
                                  'OnlineBooking':OnlineBooking,
                                  'AppointmentChanges':AppointmentChanges,
                                  'BookingToConsultDays':BookingToConsultDays,
                                  'ParkingSpaceBooked':ParkingSpaceBooked,
                                  'SpecialRequests':SpecialRequests,
                                  'DoctorAssigned':DoctorAssigned,
                                  'ConsultPriceEuros':ConsultPriceEuros,
                                  '%PaidinAdvance':PaidinAdvance,
                                  'NoShow':prediction,
                                  'Username':st.session_state.username,
                                  'id':new_id
                                  }
                            db.collection('Appointments').document(new_id).set(data)

                            # Update the patient's data
                            update_data = {"WeekendConsults": WeekendConsults,
                                           "WeekdayConsults": WeekdayConsults
                                           } 
                            db.collection('Patients').document(st.session_state.username).update(update_data)

                            return "Appointment rescheduled successfully."
                    else:
                        return "No registered event found on that id"        
                    
                else:
                    return "Please provide all necessary details:  Appointment date and Appointment for the new and original appointments, time, doctor, parking space requirement, special requests and paid in advance amount."
        
            except Exception as e:
                import traceback
                traceback.print_exc()
                return "We are unable to process. Please try again."
            


        # MAIN ----------------------------------------------------------------------------------------------------------------------------------
        #if __name__ == "chat_4":
        initialize()


        # ---------------------------- Display History ------------------------------------
        display_history_messages()

        if prompt := st.chat_input("Type your request..."):

            # ---------------------------- Request & Response ----------------------------
            if st.session_state.selected_prompt == "Clarifying medicine doubts ChatBot":
                display_user_msg(message=prompt)
                assistant_response = st.session_state.chatbot.generate_response(message=prompt, is_langchain=True)
                display_assistant_msg(message=assistant_response)
            

            else:
                display_user_msg(message=prompt)
                assistant_response = st.session_state.chatbot.generate_response(message=prompt)
                if assistant_response.content:
                    display_assistant_msg(message=assistant_response.content)
                else:
                    fn_name = assistant_response.tool_calls[0].function.name
                    arguments = assistant_response.tool_calls[0].function.arguments
                    function = locals()[fn_name]
                    result = function(arguments)
                    display_assistant_msg(message=result)

