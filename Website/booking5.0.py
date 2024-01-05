from openai import OpenAI
from util import local_settings
import numpy as np
import pandas as pd
import joblib

model = joblib.load('noshow_model.joblib')
scaler = joblib.load('robust_scaler.joblib')
features_scaler = ['AppointmentMonth', 'AppointmentWeekNumber', 'AppointmentDayOfMonth', 'AppointmentHour', 'WeekendConsults', 'WeekdayConsults', 'Adults', 'Children', 'Babies', 'FirstTimePatient', 'AffiliatedPatient', 'PreviousAppointments', 'PreviousConsults', 'PreviousNoShows', 'LastMinutesLate', 'OnlineBooking', 'AppointmentChanges', 'BookingToConsultDays', 'ParkingSpaceBooked', 'SpecialRequests', 'NoInsurance', 'ExtraExamsPerConsult', 'DoctorRequested', 'DoctorAssigned', 'ConsultPriceEuros', 'ConsultPriceUSD', '%PaidinAdvance', 'CountryofOriginAvgIncomeEuros (Year-2)', 'CountryofOriginAvgIncomeEuros (Year-1)', 'CountryofOriginHDI (Year-1)']
feature_names = ['AppointmentWeekNumber', 'AppointmentDayOfMonth', 'AppointmentHour', 'WeekendConsults', 'WeekdayConsults', 'Adults', 'Children', 'Babies', 'AffiliatedPatient', 'PreviousAppointments', 'PreviousNoShows', 'LastMinutesLate', 'OnlineBooking', 'AppointmentChanges', 'BookingToConsultDays', 'ParkingSpaceBooked', 'SpecialRequests', 'NoInsurance', 'ExtraExamsPerConsult', 'DoctorAssigned', 'ConsultPriceEuros', '%PaidinAdvance', 'CountryofOriginHDI (Year-1)']


# OpenAI API ------------------------------------------------------------------------------------------------------------------------------------
class GPT_Helper:
    def __init__(self, OPENAI_API_KEY: str, system_behavior: str="", functions: list=None, model="gpt-3.5-turbo"): # function_call: list=None ,
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.messages = []
        self.model = model

        if system_behavior:
            self.messages.append({"role": "system", "content": system_behavior})
        if functions:
            self.functions = functions

    # get completion from the model
    def get_completion(self, prompt, temperature=0):

        self.messages.append({"role": "user", "content": prompt})

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=temperature,
            tools=self.functions
        )

        if completion.choices[0].message.content:
            self.messages.append({"role": "assistant", "content": completion.choices[0].message.content})
        
        return completion.choices[0].message  



# ChatBot ---------------------------------------------------------------------------------------------------------------------------------------

class ChatBot:
    """
    Generate a response by using LLMs.
    """

    def __init__(self, system_behavior: str, functions: list=None):
        self.__system_behavior = system_behavior
        self.__functions = functions

        self.engine = GPT_Helper(
            OPENAI_API_KEY=local_settings.OPENAI_API_KEY,
            system_behavior=system_behavior,
            functions=functions
        )

    def generate_response(self, message: str):
        return self.engine.get_completion(message)

    def __str__(self):
        shift = "   "
        class_name = str(type(self)).split('.')[-1].replace("'>", "")

        return f"🤖 {class_name}."

    def reset(self):
        self.engine = GPT_Helper(
            OPENAI_API_KEY=local_settings.OPENAI_API_KEY,
            system_behavior=self.__system_behavior,
            functions=self.__functions
    )

    @property
    def memory(self):
        return self.engine.messages

    @property
    def system_behavior(self):
        return self.__system_config

    @system_behavior.setter
    def system_behavior(self, system_config : str):
        self.__system_behavior = system_config


# FUNCTIONS -------------------------------------------------------------------------------------------------------------------------------------
import json
import requests
from datetime import date, datetime, timedelta
from time import time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('calendar', 'v3', credentials=creds)

#-----------GLOBAL VARIABLES---------- PODEM IR PARA FICHEIRO SEPARADO !!!!!!!!!!!!!!!!!!!
limit1 = datetime.strptime("9:00:00", "%H:%M:%S").time() # Start
limit2 = datetime.strptime("20:00:00", "%H:%M:%S").time() # End
limit3 = datetime.strptime("12:00:00", "%H:%M:%S").time() # End Sturday

doctor_time_tables = {
    "Dr. João Santos": {"monday": {'start': '09:00:00', 'end': "13:00:00"}, "wednesday": {'start': '18:00:00','end': "20:00:00"}},
    "Dr. Miguel Costa": {"monday": {'start': "13:30:00", 'end': "17:30:00"}, "thursday": {'start': '09:00:00', 'end': "13:00:00"}},
    "Dra. Sofia Pereira": {"monday": {'start': "18:00:00", 'end': "20:00:00"}, "thursday": {'start': '13:30:00', 'end': "17:30:00"}},
    "Dra. Mariana Chagas": {"tuesday": {'start': "09:00:00", 'end': "13:00:00"}, "thursday": {'start': '18:00:00', 'end': "20:00:00"}},
    "Dr. António Oliveira": {"tuesday": {'start': "13:30:00", 'end': "17:30:00"}, "friday": {'start': '09:00:00', 'end': "13:00:00"}},
    "Dra. Inês Martins": {"tuesday": {'start': "18:00:00", 'end': "20:00:00"}, "friday": {'start': '13:30:00', 'end': "17:30:00"}},
    "Dr. Ângelo Rodrigues": {"wednesday": {'start': "09:00:00", 'end': "13:00:00"}, "friday": {'start': '18:00:00', 'end': "20:00:00"}},
    "Dr. José Dias": {"wednesday": {'start': "13:30:00", 'end': "17:30:00"}, "saturday": {'start': '09:00:00', 'end': "12:00:00"}},
}

doctor_to_ID = {
    'Dr. João Santos': -1,
    'Dr. Miguel Costa': 0,
    'Dra. Sofia Pereira': 1,
    'Dra. Mariana Chagas': 2,
    'Dr. António Oliveira': 3,
    'Dra. Inês Martins': 4,
    'Dr. Ângelo Rodrigues': 5,
    'Dr. José Dias': 6
}

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
        provided_time_str = str(datetime.strptime(json.loads(arguments)['book_time'], "%H:%M:%S").time())
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
        if provided_date_str and provided_time_str and email_address and doctor:
            # Check if slot in clinics' working hours and slot is not already booked
            slot_checking = appointment_checking(start_date_time, end_date_time, timezone)
            # Checks if doctor is available at the given time
            doc_checking = doctor_checking(start_date_time, doctor)
            while doc_checking != "Doctor and time are compatible.":
                return doc_checking        
            while slot_checking != "The slot requested is available.":
                return slot_checking

            patient_data = db.collection('Patients').document(st.session_state.username).get()
            patient_data_dict = patient_data.to_dict()

            if doc_checking == "Doctor and time are compatible." and slot_checking == "The slot requested is available.":        
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
                AppointmentChanges = 0 # ALTERAR NO RESCHEDULE!!!!!!!!!!!!!!!!!!
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

                model_data = np.array([[0,AppointmentWeekNumber,AppointmentDayOfMonth,AppointmentHour,WeekendConsults,WeekdayConsults,Adults,Children,Babies,0,AffiliatedPatient,PreviousAppointments,0,PreviousNoShows,LastMinutesLate,OnlineBooking,AppointmentChanges,BookingToConsultDays,ParkingSpaceBooked,SpecialRequests,NoInsurance,ExtraExamsPerConsult,0,DoctorAssigned,ConsultPriceEuros,0,PaidinAdvance,0,0,CountryofOriginHDI]])
                dataframe_scaler = pd.DataFrame(model_data, columns=features_scaler)
                scaled_data = scaler.transform(dataframe_scaler)
                scaled_dataframe = pd.DataFrame(scaled_data, columns=features_scaler)
                model_dataframe = scaled_dataframe[feature_names]
                model_dataframe.rename(columns={'CountryofOriginHDI (Year-1)': 'CountryofOriginHDI'}, inplace=True)
                prediction = model.predict(model_dataframe)

                event = {
                    'summary': doctor,
                    'location': "Lisbon",
                    'description': f"This appointment was scheduled by the chatbot. And the no-show prediction is: {prediction}",
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
                        ]
                    }
                }
                ev = service.events().insert(calendarId='primary', body=event).execute()
                id = ev['id']

                ap_data={'AppointmentWeekNumber':AppointmentWeekNumber,
                          'AppointmentDayOfMonth': AppointmentDayOfMonth,
                          'AppointmentHour': AppointmentHour,
                          'OnlineBooking':OnlineBooking,
                          'AppointmentChanges':AppointmentChanges,
                          'BookingToConsultDays':BookingToConsultDays,
                          'ParkingSpaceBooked':ParkingSpaceBooked,
                          'DoctorAssigned':DoctorAssigned,
                          'ConsultPriceEuros':ConsultPriceEuros,
                          '%PaidinAdvance':PaidinAdvance,
                          'NoShow':prediction,
                          'Username':st.session_state.username,
                          'id':id
                          }
                
                db.collection('Appointments').document(id).set(ap_data)

                update_data = {"WeekendConsults": WeekendConsults + 1 if start_date_time.strftime("%A") == "Saturday" else WeekendConsults,
                               "WeekdayConsults": WeekdayConsults + 1 if start_date_time.strftime("%A") != "Saturday" else WeekdayConsults,
                               "PreviousAppointments": PreviousAppointments + 1
                               } 
                
                db.collection('Patients').document(st.session_state.username).update(update_data)

                return "Appointment added successfully."
            
            else:
                return "The doctor is already fully booked for the day."
                
        else:
            return "Please provide all necessary details: Date, time, email and doctor."
    
    except Exception as e:
        import traceback
        traceback.print_exc()
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
                    db.collection('Appointments').document(id).delete()
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
        parking_spaces = json.loads(arguments)['book_parking']
        special_requests = json.loads(arguments)['book_special_requests']
        pay_in_advance = json.loads(arguments)['book_pay_in_advance']
        
        check, original_id = check_event(email_address, original_start_date_time)

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

                    patient_data = db.collection('Patients').document(st.session_state.username).get()
                    patient_data_dict = patient_data.to_dict()
                    appointment_data = db.collection('Appointments').document(original_id).get()
                    appointment_data_dict = appointment_data.to_dict()

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

                    model_data = np.array([[0,AppointmentWeekNumber,AppointmentDayOfMonth,AppointmentHour,WeekendConsults,WeekdayConsults,Adults,Children,Babies,0,AffiliatedPatient,PreviousAppointments,0,PreviousNoShows,LastMinutesLate,OnlineBooking,AppointmentChanges,BookingToConsultDays,ParkingSpaceBooked,SpecialRequests,NoInsurance,ExtraExamsPerConsult,0,DoctorAssigned,ConsultPriceEuros,0,PaidinAdvance,0,0,CountryofOriginHDI]])
                    dataframe_scaler = pd.DataFrame(model_data, columns=features_scaler)
                    scaled_data = scaler.transform(dataframe_scaler)
                    scaled_dataframe = pd.DataFrame(scaled_data, columns=features_scaler)
                    model_dataframe = scaled_dataframe[feature_names]
                    model_dataframe.rename(columns={'CountryofOriginHDI (Year-1)': 'CountryofOriginHDI'}, inplace=True)
                    prediction = model.predict(model_dataframe)

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
                    service.events().delete(calendarId='primary', eventId=original_id).execute()
                    db.collection('Appointments').document(original_id).delete()
                    ev = service.events().insert(calendarId='primary', body=event).execute()
                    new_id = ev['id']

                    data={'AppointmentWeekNumber':AppointmentWeekNumber,
                          'AppointmentDayOfMonth': AppointmentDayOfMonth,
                          'AppointmentHour': AppointmentHour,
                          'OnlineBooking':OnlineBooking,
                          'AppointmentChanges':AppointmentChanges,
                          'BookingToConsultDays':BookingToConsultDays,
                          'ParkingSpaceBooked':ParkingSpaceBooked,
                          'DoctorAssigned':DoctorAssigned,
                          'ConsultPriceEuros':ConsultPriceEuros,
                          '%PaidinAdvance':PaidinAdvance,
                          'NoShow':prediction,
                          'Username':st.session_state.username,
                          'id':new_id
                          }
                    db.collection('Appointments').document(new_id).set(data)

                    update_data = {"WeekendConsults": WeekendConsults,
                                "WeekdayConsults": WeekdayConsults
                                } 
                    db.collection('Patients').document(st.session_state.username).update(update_data)

                    return "Appointment rescheduled successfully."
            else:
                return "No registered event found on that id"        
            
        else:
            return "Please provide all necessary details:  Appointment date, Appointment time and doctor."

    except:
        return "We are enable to process. Please try again."
    

functions = [
    {
        "type": "function",
        "function": {
            "name": "appointment_booking",
            "description": "When user want to book appointment, then this function should be called.",
            "parameters": {
                "type": "object",
                "properties": {
                    'doctor': {
                        "type" : "string",
                        "description": "doctor of preference" 
                    },
                    "book_date": {
                        "type": "string",
                        "format": "date",
                        "example":"2023-07-23",
                        "description": "Date to which the user wants to book an appointment. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format." 
                    },
                    "book_time": {
                        "type": "string",
                        "example": "20:12:45", 
                        "description": "Time to which the user wants to book an appointment on a specified date. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format." 
                    },
                    "email_address": {
                        "type": "string",
                        "description": "email_address of the user gives for identification.",
                    },
                    "parking": {
                        "type": "integer",
                        "description": "must be 1 if the user requests a parking space for the appointment, and 0 if the user does not request a parking spot for the appointment.",
                    },
                    "special_requests": {
                        "type": "integer",
                        "description": "the number of special requests the user made for the appointment.",
                    },
                    "pay_in_advance": {
                        "type": "integer",
                        "description": "the percentage of the appointment cost the user wants to pay in advance. This value must be between 0 and 100",
                    }
                },
                "required": ["book_date","book_time","email_address", "doctor","parking","special_requests","pay_in_advance"],
            }
        }
    }, 

    {
        "type": "function",
        "function": {
            "name": "appointment_reschedule",
            "description": "When user want to reschedule appointment, then this function should be called.",
            "parameters": {
                "type": "object",
                "properties": {
                    "del_date": {
                        "type": "string",
                        "format": "date",
                        "example":"2023-07-23",
                        "description": "Date in which the user has the appointment he wants to reschedule. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
                    },
                    "del_time": {
                        "type": "string",
                        "description": "time in which the user has an appointment and wants to reschedule. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format.",
                    },
                    "email_address": {
                        "type": "string",
                        "description": "email_address the user gives for identification.",
                    },
                    "doctor": {
                        "type" : "string",
                        "description": "doctor of preference for the new appointment. Make sure to only ask this once the original appointment has been indeed canceled"
                    },
                    "book_date": {
                        "type": "string",
                        "format": "date",
                        "example":"2023-07-23",
                        "description": "Date to which the user wants to reschedule the appointment. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
                    },
                    "book_time": {
                        "type": "string",
                        "example": "20:12:45", 
                        "description": "time to which the user wants to reschedule the appointment on a prespecified date. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format.",
                    },
                    "book_parking": {
                        "type": "integer",
                        "description": "must be 1 if the user requests a parking space for the new appointment, and 0 if the user does not request a parking spot for the new appointment.",
                    },
                    "book_special_requests": {
                        "type": "integer",
                        "description": "the number of special requests the user made for the appointment.",
                    },
                    "book_pay_in_advance": {
                        "type": "integer",
                        "description": "the percentage of the appointment cost the user wants to pay in advance. This value must be between 0 and 100",
                    }
                },
            
                "required": ["del_date","del_time","email_address","doctor","book_date","book_time","book_parking","book_special_requests","book_pay_in_advance"],
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "appointment_delete",
            "description": "When user want to delete appointment, then this function should be called.",
            "parameters": {
                "type": "object",
                "properties": {
                    "del_date": {
                        "type": "string",
                        "format": "date",
                        "example":"2023-07-23",
                        "description": "Date on which the user has an appointment he wants to cancel. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
                    },
                    "del_time": {
                        "type": "string",
                        "description": "time on which user has an appointment he wants to delete. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format.",
                    },
                    "email_address": {
                        "type": "string",
                        "description": "email_address the user gives for identification.",
                    }
                },
                "required": ["del_date","del_time","email_address"],
            }
        }
    }]


# BOT ------------------------------------------------------------------------------------------------------------------------------------------

system_behavior = """You are an expert in booking, canceling and reschedueling. You help a clinic with its appointment management. 

GENERAL INSTRUCTIONS:
You will need to ask questions depending on the action requested by the user (this questions will regard information such as: appointment date, appointment time, doctor of preference and email ID. 
Users can only book appointments in a specified timeframe (from 9 AM to 8 PM on Mondays, Tuesdays, Wednesdays, Thursdays amd Fridays, and from 9 AM to 12 PM on Saturdays), since it's the clinic's working hours. 
You will check if the time provided by the user is within the working hours and only then proceed.
Also check if the appointment date is according to the time frame of the chosen doctor.
All the instructions you will have to follow will be presented below in 
        

PROCESS: 
[OPTION 1] If a user wants to book an appointment:
    1. ask for the date of the appointment
    2. ask for the time of the appointment
    3. ask for the doctor of preference
    4. ask for the email address of the user
    5. ask if the user requiers a parking space for the appointment
    6. ask if the user has special requests for the appointment. If so, ask what they are.
    7. tell the user that the appointment has a base value of 30 euros and ask if the user wants to pay a percentage of the cost in advance. If so, ask for the percentage of the appointment cost the user wants to pay in advance
    8. Check if all the details above have been provided by the user. Do not assume any values!
    9. If there are details missing (not provided by the user), ask for the remaining information. If they were tell them to the user and ask for confirmation.
    10. If the user confirmed, only then proceed with booking the appointment. If the user does not confirm ask for what changes they would like to make and proceed accordingly
    11. If the user confirmed, and you proceeded with the booking, make sure the function appointment_booking has booked the appointment by checking if the function returned "Appointment added successfully.", and, if so, tell the user the appointment was booked.
[OPTION 2] If a user wants to cancel an appointment:
    1. ask for the date of the appointment
    2. ask for the time of the appointment
    3. ask for the email address of the user
    4. Check if all the details above have been provided by the user. Do not assume any values!
    5. If there are details missing (not provided by the user), ask for the remaining information. If they were tell them to the user and ask for confirmation.
    5. If the user confirmed, proceed with canceling the appointment. If the user does not confirm ask for what changes they would like to make and proceed accordingly
    6. Make sure the function appointment_delete has deleted the appointment by checking if the function returned "Appointment deleted successfully.", and, if so, tell the user the appointment was canceled.
[OPTION 3]: If a user whats to reschedule follow the following steps:
    1. ask for the date of the original appointment
    2. ask for the time of the original appointment
    3. ask for the email address of the user
    4. ask for the date for the new appointment
    5. ask for the time for the new appointment
    6. ask for the new doctor of preference for the new appointment
    7. ask if the user requiers a parking space for the new appointment
    8. ask for the user's has special requests for the appointment. If they dont have any, ask them to write "no"
    9. tell the user that the new appointment has a base value of 30 euros and ask if the user wants to pay a percentage of the cost in advance. If so, ask for the percentage of the new appointment cost the user wants to pay in advance
    10. Check if all the details above have been provided by the user. Do not assume any values!
    11. If there are details missing (not provided by the user), ask for the remaining information. If they were tell them to the user and ask for confirmation.
    12. If the user confirmed, only then proceed with reschedueling the appointment. If the user does not confirm ask for what changes they would like to make and proceed accordingly

[IMPORTANT ADDITIONAL INFORMATION]:
- Do not ever make assumptions about what values to plug into functions, if the user does not provide one or more of the required parameters then you must ask for clarification.
- If a user request is ambiguous, always kindly ask for clarification.
- Dates must be in the format of YYYY-MM-DD, if the user does not provide it in this format, convert it and store it in this format.
- Time must be in %H:%M:%S format, if the user does not provide it in this format, convert it and store it in this format. In this conversion if a user uses a AM/PM time structure and didn't specify "ante meridiem (AM)" or "post meridiem (PM)" while providing the time, then you must ask for clarification.
- If the user chooses a doctor and the time for the appointment which are not compatible, you must ask to change one of them.

ATTENTION: Make sure to follow all the instructions carefully while processing any request. 
"""


chatbot = ChatBot(system_behavior, functions)
# Testes
prompt = input("Please enter your question here: (if you want to exit then write 'exit' or 'bye'.) ")
while prompt.strip().lower() != "exit" and prompt.strip().lower() != "bye":
    # print('antes do response')
    assistant_response = chatbot.generate_response(message=prompt)
    # print("A:", assistant_response.content)
    if assistant_response.content:
        print('B:', assistant_response.content)
    else:
        # print('function call')
        # print(assistant_response.tool_calls)
        fn_name = assistant_response.tool_calls[0].function.name
        arguments = assistant_response.tool_calls[0].function.arguments
        function = locals()[fn_name]
        result = function(arguments)
        print("B: ", result)

    prompt = input("Y: ")


