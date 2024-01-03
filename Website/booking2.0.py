from openai import OpenAI
from util import local_settings


# OpenAI API ------------------------------------------------------------------------------------------------------------------------------------
class GPT_Helper:
    def __init__(self, OPENAI_API_KEY: str, system_behavior: str="", model="gpt-3.5-turbo", functions=None):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.messages = []
        self.model = model
        self.functions = functions

        if self.functions is not None:
            self.functions = {"functions": self.functions}

        if system_behavior:
            self.messages.append({"role": "system", "content": system_behavior})

    # get completion from the model
    def get_completion(self, prompt, temperature=0):

        self.messages.append({"role": "user", "content": prompt})

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=temperature,
            functions=self.functions
        )

        self.messages.append({"role": "assistant", "content": str(completion.choices[0].message.content)})

        return completion.choices[0].message.content    



# ChatBot ---------------------------------------------------------------------------------------------------------------------------------------

class ChatBot:
    """
    Generate a response by using LLMs.
    """

    def __init__(self, system_behavior: str):
        self.__system_behavior = system_behavior

        self.engine = GPT_Helper(
            OPENAI_API_KEY=local_settings.OPENAI_API_KEY,
            system_behavior=system_behavior, functions=functions
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
            system_behavior=self.__system_behavior
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
from util import local_settings

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

#-----------GLOBAL FUNCTIONS----------
def appointment_checking(start_date_time=None, end_date_time=None, timezone=None): #Good
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
                    end_date_time = start_date_time + timedelta(hours=0.5)
                    events_result = service.events().list(calendarId='primary', timeMin=start_date_time.isoformat(), timeMax=end_date_time.isoformat()).execute()
                    if events_result['items']:
                        return "Sorry slot is not available."
                    else:
                        return "The slot requested is available."
                else:
                    return "Please try to check an appointment within working hours, which is 9 AM to 7h30 PM."
    
    except:
        return "We are facing some issues while processing your booking request, please try again."


def get_available_time_slots(doctor, day): # Good
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
    
def is_time_in_range(selected_time, times_list): # Good
    for time_obj in times_list:
        if time_obj == selected_time:
            return "In time range"
    return "Not in time range"

def get_available_times_message(doctor, day, available_times): # Good
    if not available_times:
        return f"{doctor} is not available on {day}."
    else:
        return f"{doctor} is available on {day} at the following times: {', '.join(available_times)}."

# def choose_doctor_based_on_time(start_date_time, requested_doctor): #CHECK
#     available_doctors = []
#     selected_time = start_date_time.time()
#     selected_date = start_date_time.date()
#     requested_weekday = selected_date.strftime("%A").lower()
    
#     for doctor, schedule in doctor_time_tables.items():
#         for weekday, time_range in schedule.items():
#             if weekday == requested_weekday:
#                 doc_start_time = datetime.strptime(time_range['start'], "%H:%M:%S").time()
#                 doc_end_time = datetime.strptime(time_range['end'], "%H:%M:%S").time()

#                 if doc_start_time <= selected_time <= doc_end_time:
#                     available_doctors.append(doctor)

#     if not available_doctors:
#         return 'No doctors available at the requested time'
#     else:
#         if requested_doctor in available_doctors:
#             return requested_doctor
#         else:
#             return None # The originally requested doctor is not available at the requested time


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
            # else:
            #     # Choose a doctor based on the requested time
            #     updated_doctor = choose_doctor_based_on_time(start_date_time, doctor)
            #     if updated_doctor is None:
            #         return f"Please try again"
            #     # Confirm the appointment
            #     return True

#---------------BOOKING----------------
def appointment_booking(arguments):
    try:
        # Handling the date and time
        provided_date_str =  str(datetime.strptime(json.loads(arguments)['book_date'], "%Y-%m-%d").date())
        provided_time_str = str(datetime.strptime(json.loads(arguments)['book_time'], "%H:%M:%S").time()) #.replace("PM","").replace("AM","").strip()
        start_date_time_str = provided_date_str + " " + provided_time_str
        timezone = pytz.timezone('Europe/Lisbon')
        start_date_time = timezone.localize(datetime.strptime(start_date_time_str, "%Y-%m-%d %H:%M:%S"))
        end_date_time = start_date_time + timedelta(hours=0.5)

        # Handling other information
        email_address = json.loads(arguments)['email_address']
        doctor = json.loads(arguments)['doctor']
        
        
        # Checking if the requested slot is available
        if provided_date_str and provided_time_str and email_address and doctor:
            slot_checking = appointment_checking(start_date_time, end_date_time, timezone) 
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
               return "There has been a mismatch in compatibilities." # This should never happen
                
        else:
            return "Please provide all necessary details: Date, time, email and doctor."
    
    except:
        return "We are facing an error while processing your request. Please try again."

#---------------CANCEL----------------
def appointment_delete(arguments):
    try:
        provided_date =  str(datetime.strptime(json.loads(arguments)['del_date'], "%Y-%m-%d").date())
        provided_time = str(datetime.strptime(json.loads(arguments)['del_time'], "%H:%M:%S").time()) #.replace("PM","").replace("AM","").strip()
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
            return "Please provide all necessary details: Start date, End date and Email address."
    except:
        return "We are facing an error while processing your cancelation. Please try again."


#---------------RESCHEDULE----------------
def appointment_reschedule(arguments):
    delete_ap = appointment_delete(arguments)
    book_ap = appointment_booking(arguments)
    if delete_ap == "Appointment deleted successfully." and book_ap == "Appointment added successfully.": 
        return "Appointment rescheduled successfully."
    else:
        if delete_ap == "Appointment deleted successfully.":
            return book_ap
        elif book_ap == "Appointment added successfully.":
            return delete_ap
        else:
            return book_ap + " " + delete_ap
        

functions = [
    {
        # "type": "function",
        # "function": {
            "name": "appointment_booking",
            "description": "When user want to book appointment, then this function should be called.",
            "parameters": {
                "type": "object",
                "properties": {
                    'doctor': {
                        "type" : "string",
                        "description": "doctor of preference, must be one among the existants: {existing_doctors}, otherwise random one will be assigned"
                    },
                    "book_date": {
                        "type": "string",
                        "format": "date",
                        "example":"2023-07-23",
                        "description": "Date to which the user wants to book an appointment. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
                    },
                    "book_time": {
                        "type": "string",
                        "example": "20:12:45", 
                        "description": "time to which the user wants to book an appointment on a specified date. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format.",
                    },
                    "email_address": {
                        "type": "string",
                        "description": "email_address of the user gives for identification.",
                    }   
                },
                "required": ["book_date","book_time","email_address", "doctor"],
            # }
        }
    }, 

    {
        # "type": "function",
        # "function": {
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
                    }
                },
            
                "required": ["del_date","del_time","email_address","doctor","book_date","book_time"],
            # }
        }
    },

    {
        # "type": "function",
        # "function": {
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
            # }
        }
    }

    # {
    #     "type": "function",
    #     "function": {
    #         "name": "appointment_checking",
    #         "description": "When user wants to check if appointment is available or not, then this function should be called.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "date": {
    #                     "type": "string",
    #                     "format": "date",
    #                     "example":"2023-07-23",
    #                     "description": "Date of the appointment the user wants to check. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
    #                 },
    #                 "time": {
    #                     "type": "string",
    #                     "example": "20:12:45", 
    #                     "description": "time of the appointment the user wants to check. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format.",
    #                 },
    #             },
    #             "required": ["date","time"],
    #         }
    #     }
    # }
    ]



# BOT ------------------------------------------------------------------------------------------------------------------------------------------

system_behavior = f"""You are an expert in booking, canceling and reschedueling. You help a clinic with its appointment management. 

GENERAL INSTRUCTIONS:
You will need to ask questions depending on the action requested by the user (this questions will regard information such as: appointment date, appointment time, doctor of preference and email ID. 
Users can only book appointments in a specified timeframe (from 9 AM to 8 PM from Monday to Friday, and from 9 AM to 12 PM on Saturdays), since it's the clinic's working hours. 
You need to remember that today's date is {date.today()} and it is {date.today().strftime("%A")}. 
You will check if the time provided by the user is within the working hours and only then proceed.
Also check if the appointment date is according to the time frame of the chosen doctor.
All the instructions you will have to follow will be presented below in 
        

PROCESS: 
[OPTION 1] If a user wants to book an appointment:
    1. ask for the date of the appointment
    2. ask for the time of the appointment
    3. ask for the doctor of preference (it has to be an existing doctor)
    4. ask for the email address of the user
    5. Check if all the details above have been given and if they were, tell them to the user and ask for confirmation
    6. If the user confirmed, only then proceed with booking the appointment. If the user does not confirm ask for what changes they would like to make and proceed accordingly
    7. If the user confirmed, and you proceeded with the booking, make sure the function appointment_booking has booked the appointment by checking if the function returned "Appointment added successfully.", and, if so, tell the user the appointment was booked.
[OPTION 2] If a user wants to cancel an appointment:
    1. ask for the date of the appointment
    2. ask for the time of the appointment
    3. ask for the email address of the user
    4. Check if all the details above have been given and if they were, tell them to the user and ask for confirmation
    5. If the user confirmed, proceed with canceling the appointment. If the user does not confirm ask for what changes they would like to make and proceed accordingly
    6. Make sure the function appointment_delete has deleted the appointment by checking if the function returned "Appointment deleted successfully.", and, if so, tell the user the appointment was canceled.
[OPTION 3]: If a user whats to reschedule follow the following TWO steps:
    Part 1. Canceling previous booking:
        1. ask for the date of the original appointment
        2. ask for the time of the original appointment
        3. ask for the email address of the user
        4. Check if all the details above have been given and if they were, tell them to the user and ask for confirmation
        5. If the user confirmed, proceed with canceling the appointment. If the user does not confirm ask for what changes they would like to make and proceed accordingly
        6. Make sure the function appointment_delete has deleted the appointment by checking if the function returned "Appointment deleted successfully.", and, if so, proceed with Part 2 to book a new appointment.
    Part 2. Book a new appointment:
        1. ask for the date for the new appointment
        2. ask for the time for the new appointment
        3. ask for the doctor of preference for the new appointment (make sure it exists)
        4. Check if all the details above have been given and if they were, tell them to the user and ask for confirmation
        5. If the user confirmed, only then proceed with booking the appointment. If the user does not confirm ask for what changes they would like to make and proceed accordingly
        6. If the user confirmed, and you proceeded with the booking, make sure the function appointment_booking has booked the appointment by checking if the function returned "Appointment added successfully.", and, if so, tell the user the appointment was rescheduled.

[IMPORTANT ADDITIONAL INFORMATION]:
- Do not ever make assumptions about what values to plug into functions, if the user does not provide one or more of the required parameters then you must ask for clarification.
- If a user request is ambiguous, always kindly ask for clarification.
- Dates must be in the format of YYYY-MM-DD, if the user does not provide it in this format, convert it and store it in this format.
- Time must be in %H:%M:%S format, if the user does not provide it in this format, convert it and store it in this format. In this conversion if a user uses a AM/PM time structure and didn't specify "ante meridiem (AM)" or "post meridiem (PM)" while providing the time, then you must ask for clarification.
- If the doctor is not available at the requested time, tell the user the time frames he is available
- If the user chooses a doctor and the time for the appointment which are not compatible, you must ask to change one of them.

ATTENTION: Make sure to follow all the instructions carefully while processing any request. 
"""

chatbot = ChatBot(system_behavior)
# Testes
prompt = input("Please enter your question here: (if you want to exit then write 'exit' or 'bye'.) ")
while prompt.strip().lower() != "exit" and prompt.strip().lower() != "bye":
    # assistant_response = chatbot.generate_response(message=prompt)
    print('B:', chatbot.generate_response(message=prompt))
    prompt = input("Y: ")
