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


GPT_MODEL = "gpt-3.5-turbo-0613"
openai_api_key = local_settings.OPENAI_API_KEY

# FUNCTION CALL INEXISTENTE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def chat_completion_request(messages, functions=None, function_call=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + openai_api_key,
    }
    json_data = {"model": model, "messages": messages}
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


limit1 = datetime.strptime("9:00:00", "%H:%M:%S").time() # Start
limit2 = datetime.strptime("20:00:00", "%H:%M:%S").time() # End
limit3 = datetime.strptime("12:00:00", "%H:%M:%S").time() # End Sturday

def is_time_in_range(selected_time, times_list): #CHECK
    selected_time = datetime.strptime(selected_time, "%H:%M:%S").time()
    
    for times in times_list:
        time_obj = datetime.strptime(times, "%H:%M:%S").time()
        if time_obj == selected_time:
            return True
    return False


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

def get_available_time_slots(doctor, day): #CHECK
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


def get_available_times_message(doctor, day):
    available_times = get_available_time_slots(doctor, day)
    if not available_times:
        return f"{doctor} is not available on {day}."
    else:
        return f"{doctor} is available on {day} at the following times: {', '.join(available_times)}."

def choose_doctor_based_on_time(requested_time_str, requested_doctor, requested_date_str): #CHECK
    available_doctors = []
    requested_weekday = datetime.strptime(requested_date_str, "%Y-%m-%d").strftime("%A").lower()
    requested_time = datetime.strptime(requested_time_str, "%H:%M:%S").time()

    for doctor, schedules in doctor_time_tables.items():
        for day, time_range in schedules.items():
            if day == requested_weekday:
                start_time = datetime.strptime(time_range['start'], "%H:%M:%S").time()
                end_time = datetime.strptime(time_range['end'], "%H:%M:%S").time()

                if start_time <= requested_time <= end_time:
                    available_doctors.append(doctor)

    if not available_doctors:
        return None  # No doctors available at the requested time

    if requested_doctor in available_doctors:
        return requested_doctor
    else:
        return None # The originally requested doctor is not available at the requested time

def doctor_checking(arguments, predetermined_doctor = None):
    provided_date =  str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
    provided_time = str(datetime.strptime(json.loads(arguments)['time'], "%H:%M:%S").time()) #.replace("PM","").replace("AM","").strip()
    start_date_time = provided_date + " " + provided_time
    timezone = pytz.timezone('Europe/Lisbon')
    start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))

    # email_address = json.loads(arguments)['email_address']
    doctor = predetermined_doctor or json.loads(arguments)['doctor'] # VOLATR AQUI !!!!!!!!!!!!!!!
    end_date_time = start_date_time + timedelta(minutes=30)

    
    existing_doctors = ["Dr. João Santos", "Dr. Miguel Costa", "Dra. Sofia Pereira", 'Dra. Mariana Chagas', 'Dr. António Oliveira',
                            'Dra. Inês Martins', 'Dr. Ângelo Rodrigues', 'Dr. José Dias']


    if doctor is not None:
        if doctor not in existing_doctors:
            return "Please choose a valid doctor from the list: " + ", ".join(existing_doctors)

        else:   
            day_of_week = start_date_time.strftime("%A").lower()
            doctor_schedule = get_available_time_slots(doctor, day_of_week)

            if not doctor_schedule or not is_time_in_range(provided_time, doctor_schedule):
                available_times_message = get_available_times_message(doctor, day_of_week)
                
                return f"{doctor} is not available at the selected time. {available_times_message} Please choose a valid time."
            else:
                # Choose a doctor based on the requested time
                requested_time = start_date_time.time().strftime("%H:%M:%S")
                updated_doctor = choose_doctor_based_on_time(requested_time, doctor, provided_date)
                if updated_doctor is None:
                    return f"Please try again"
                # Confirm the appointment
                return True
        
def check_event(arguments):

    email_address = json.loads(arguments)['email_address']
    events = service.events().list(calendarId="primary").execute()  #all the events presented in google calendar
    id = ""
    final_event = None
    events_list = []
    for event in events['items']:
        if event['attendees'][0]['email'] == email_address: #if the email exists in the attendees 
            id = event['id'] #id => event id
            final_event = event #final event => is the full event
    if final_event:
        start_datetime_str = final_event['start']['dateTime']
        start_datetime = datetime.fromisoformat(start_datetime_str[:-1]).replace(tzinfo=pytz.UTC)
        formatted_date= start_datetime.strftime('%Y-%m-%d')
        formatted_time = start_datetime.strftime('%H:%M:%S')


        return f"Your next appointment was scheduled for {formatted_date} at {formatted_time} with {final_event['summary']} do you wish t proceed?", final_event
    else:
        return f"Your email is not assigned to any appointment. Please try again."

#---------------BOOKING----------------
        
def appointment_booking(arguments):
    try:
        provided_date =  str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
        provided_time = str(datetime.strptime(json.loads(arguments)['time'].replace("PM","").replace("AM","").strip(), "%H:%M:%S").time())
        start_date_time = provided_date + " " + provided_time
        timezone = pytz.timezone('Europe/Lisbon')
        start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))
        email_address = json.loads(arguments)['email_address']
        doctor = json.loads(arguments)['doctor']
        end_date_time = start_date_time + timedelta(hours=0.5)

           
                # checking if the slot is available
        if provided_date and provided_time and email_address and doctor:
            slot_checking = appointment_checking(arguments) 
            doc_checking = doctor_checking(arguments)

            while doc_checking != True:
                return doc_checking        

            while slot_checking != True:
                return slot_checking   
        
            if doc_checking == True and slot_checking == True:        
    
                if day_list[start_date_time.date().weekday()] == "Saturday": # REPETIDOOO !!!!!!!!!!
                    #   if start_date_time.time() >= limit1 and start_date_time.time() <= limit3:
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
                        },
                    }
                    service.events().insert(calendarId='primary', body=event).execute()
                    return "Appointment added successfully."
                #else:
                #    return "Please try to book an appointment into working hours, which is 9 AM to 12 AM at saturday."
                else:
                    # if start_date_time.time() >= limit1 and start_date_time.time() <= limit2:
                    event = {
                        'summary': doctor,
                        'location': "Lisbon",
                        'description': "This appointment has been scheduled by the booking chatbot",
                        
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
                    #else:
                    #    return "Please try to book an appointment into working hours, which is 10 AM to 7 PM."
          
        else:
            return "Please provide all necessary details: Date, time, email and doctor."
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return "We are facing an error while processing your request. Please try again."



#------------rescheduling--------------
    
def appointment_reschedule(arguments):
    delete_ap = appointment_delete(arguments)
    book_ap = appointment_booking(arguments)
    return delete_ap, book_ap
    

    # try:
    #     email_address = json.loads(arguments)['email_address']
    #   #  provided_date = None  # Initialize provided_date
    #   #  provided_time = None
    #     #doctor = None
    #     provided_date =  str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
    #     provided_time = str(datetime.strptime(json.loads(arguments)['time'].replace("PM","").replace("AM","").strip(), "%H:%M:%S").time())
    #     start_date_time = provided_date + " " + provided_time
    #     timezone = pytz.timezone('Europe/Lisbon')
    #     start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))
    #     end_date_time = start_date_time + timedelta(hours=0.5)
    #     doctor = json.loads(arguments)['doctor']


    #     # check if the event exists and conclude if the user wants to keep the same doctor
    #     checking = check_event(arguments)
    #     check_same_doctor, final_event = checking[0], checking[1]
    #     # print(check_same_doctor)  # Ask the user the question
    #     user_response = chat_completion_request(check_same_doctor)
    #     # user_response = input("Please enter your question here: ")

    #     if "yes" in user_response:
    #         if provided_date and provided_time:

    #         #Confirm that the new date is available in the calendar and with the doctor
    #             slot_checking = appointment_checking(arguments) 
    #             doc_checking = doctor_checking(arguments, predetermined_doctor = final_event['summary'])

    #             while doc_checking != True:
    #                 return doc_checking        

    #             while slot_checking != True:
    #                 return slot_checking   
            
    #             # if the new date is available and correct
    #             if doc_checking == True and slot_checking == True:        

    #                 event = {
    #                     'summary': final_event['summary'],
    #                     'location': "Lisbon",
    #                     'description': "This appointment was scheduled by the chatbot",
                        
    #                     'start': {
    #                         'dateTime': start_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
    #                         'timeZone': 'Europe/Lisbon',
    #                     },
    #                     'end': {
    #                         'dateTime': end_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
    #                         'timeZone': 'Europe/Lisbon',
    #                     },
    #                     'attendees': [
    #                         {'email': email_address},
    #                     ],
                                            
    #                     'reminders': {
    #                         'useDefault': False,
    #                         'overrides': [
    #                             {'method': 'email', 'minutes': 24 * 60},
    #                             {'method': 'popup', 'minutes': 10},
    #                         ],
    #                     },
    #                 }
    #                 id = final_event['id']
    #                 service.events().delete(calendarId='primary', eventId=id).execute()
    #                 service.events().insert(calendarId='primary', body=event).execute()
  
    #                 return "Appointment rescheduled successfully."
    #         else:
    #              return "Please provide date and time."
                
    #     if "no" in user_response.lower():


    #         #choose other doctor

    #         if provided_date and provided_time and doctor:

    #             slot_checking = appointment_checking(arguments) 
    #             doc_checking = doctor_checking(arguments)

    #             while doc_checking != True:
    #                 return doc_checking        

    #             while slot_checking != True:
    #                 return slot_checking   
        
    #             if doc_checking == True and slot_checking == True:        
                    
    #                 event = {
    #                     'summary': doctor,
    #                     'location': "Lisbon",
    #                     'description': "This appointment was scheduled by the chatbot",
                        
    #                     'start': {
    #                         'dateTime': start_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
    #                         'timeZone': 'Europe/Lisbon',
    #                     },
    #                     'end': {
    #                         'dateTime': end_date_time.strftime("%Y-%m-%dT%H:%M:%S"),
    #                         'timeZone': 'Europe/Lisbon',
    #                     },
    #                     'attendees': [
    #                         {'email': email_address},
    #                     ],
                                            
    #                     'reminders': {
    #                         'useDefault': False,
    #                         'overrides': [
    #                             {'method': 'email', 'minutes': 24 * 60},
    #                             {'method': 'popup', 'minutes': 10},
    #                         ],
    #                     },
    #                 }
    #                 id = final_event['id']
    #                 service.events().delete(calendarId='primary', eventId=id).execute()
    #                 service.events().insert(calendarId='primary', body=event).execute()
    #                 return "Appointment rescheduled successfully."              
    #         else:
    #              return "Please provide date, time and doctor of preference."
    #     else:
    #         return "Please answer yes or no"
        
    # except Exception as e:
    #         import traceback
    #         traceback.print_exc()
    #         return "We are enable to process. Please try again."

    
#-------------------Cancel appointment-------------------

def appointment_delete(arguments):
    try:
        provided_date =  str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
        provided_time = str(datetime.strptime(json.loads(arguments)['time'].replace("PM","").replace("AM","").strip(), "%H:%M:%S").time())
        email_address = json.loads(arguments)['email_address']

        if provided_date and provided_time and email_address:
            start_date_time = provided_date + " " + provided_time
            timezone = pytz.timezone('Europe/Lisbon')
            start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))
            if start_date_time < datetime.now(timezone):
                return "Please enter valid date and time."
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
        return "We are unable to process, please try again."

# -----------CHECKING---------------
    
def appointment_checking(arguments):
    try:
        provided_date =  str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
        provided_time = str(datetime.strptime(json.loads(arguments)['time'].replace("PM","").replace("AM","").strip(), "%H:%M:%S").time())
        start_date_time = provided_date + " " + provided_time
        timezone = pytz.timezone('Europe/Lisbon')
        start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))
        if start_date_time < datetime.now(timezone): #past
            return "Please enter valid date and time. The date provided is in the past."
        else:
            if day_list[start_date_time.date().weekday()] == "Saturday":
                if start_date_time.time() >= limit1 and start_date_time.time() <= limit3:
                    end_date_time = start_date_time + timedelta(hours=0.5)
                    events_result = service.events().list(calendarId='primary', timeMin=start_date_time.isoformat(), timeMax=end_date_time.isoformat()).execute()
                    if events_result['items']:
                        return "Sorry slot is not available."
                    else:
                        return True
                else:
                    return "Please try to check an appointment within working hours, which is 9 AM to 11h30 AM at saturday."
            else:
                if start_date_time.time() >= limit1 and start_date_time.time() <= limit2:
                    end_date_time = start_date_time + timedelta(hours=0.5)
                    events_result = service.events().list(calendarId='primary', timeMin=start_date_time.isoformat(), timeMax=end_date_time.isoformat()).execute()
                    if events_result['items']:
                        return "Sorry slot is not available."
                    else:
                        return True
                else:
                    return "Please try to check an appointment within working hours, which is 9 AM to 7h30 PM."
    except:
        return "We are unable to process, please try again."
    
#----------------------ALL---------------
    
functions = [
    {
        "name": "appointment_booking",
        "description": "When user want to book appointment, then this function should be called.",
        "parameters": {
            "type": "object",
            "properties": {
                'doctor': {
                    "type" : "string",
                    "description": "doctor of preference, must be one among the existants: {existing_doctors}, otherwise random one will be assigned"
                },
                "date": {
                    "type": "string",
                    "format": "date",
                    "example":"2023-07-23",
                    "description": "Date to which the user wants to book an appointment. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
                },
                "time": {
                    "type": "string",
                    "example": "20:12:45", 
                    "description": "time to which the user wants to book an appointment on a specified date. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format.",
                },
                "email_address": {
                    "type": "string",
                    "description": "email_address of the user gives for identification.",
                }
                
            },
            "required": ["date","time","email_address", "doctor"],
        },
    },
    # {
    #     "name": "appointment_reschedule",
    #     "description": "When user want to reschedule appointment, then this function should be called.",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #              "email_address": {
    #                 "type": "string",
    #                 "description": "email_address of the user gives for identification. First thing to be asked.",
    #             },
    #             "date": {
    #                 "type": "string",
    #                 "format": "date",
    #                 "example":"2023-07-23",
    #                 "description": " It is the date on which the user wants to reschedule the appointment. The date must be in the format of YYYY-MM-DD.",
    #             },
    #             "time": {
    #                 "type": "string",
    #                 "description": "It is the time on which user wants to reschedule the appointment. Time must be in %H:%M:%S format.",
    #             },
    #             'doctor': {
    #                 "type" : "string",
    #                 "description": "Asked if the answer to this: 'Your next appointment was scheduled for {formatted_date} at {formatted_time} with {final_event['summary']} do you wish to keep the same doctor?' is 'no'"
    #             }
               
                
    #         },
    #         "required": ["email_address", "date","time", "doctor"],
    #     },
    # },
    {
        "name": "appointment_reschedule",
        "description": "When user want to reschedule appointment, then this function should be called.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "format": "date",
                    "example":"2023-07-23",
                    "description": "Date in which the user has the appointment he wants to reschedule. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
                },
                "time": {
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
                "date": {
                    "type": "string",
                    "format": "date",
                    "example":"2023-07-23",
                    "description": "Date to which the user wants to reschedule the appointment. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
                },
                "time": {
                    "type": "string",
                    "example": "20:12:45", 
                    "description": "time to which the user wants to reschedule the appointment on a prespecified date. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format.",
                }
            },
        
            "required": ["date","time","email_address","doctor"],
        },
    },
    {
        "name": "appointment_delete",
        "description": "When user want to delete appointment, then this function should be called.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "format": "date",
                    "example":"2023-07-23",
                    "description": "Date on which the user has an appointment he wants to cancel. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
                },
                "time": {
                    "type": "string",
                    "description": "time on which user has an appointment he wants to delete. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format.",
                },
                "email_address": {
                    "type": "string",
                    "description": "email_address the user gives for identification.",
                }
            },
            "required": ["date","time","email_address"],
        },
    },
    {
        "name": "appointment_checking",
        "description": "When user wants to check if appointment is available or not, then this function should be called.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "format": "date",
                    "example":"2023-07-23",
                    "description": "Date, when the user wants to book an appointment. The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format..",
                },
                "time": {
                    "type": "string",
                    "example": "20:12:45", 
                    "description": "time, on which user wants to book an appointment on a specified date. Time must be in %H:%M:%S format, if it is not, convert it and store it in this format..",
                },
            },
            "required": ["date","time"],
        }
    }]


#-------------TEST---------------


day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

messages = [{"role": "system", "content": f"""You are an expert in booking appointments. You need to ask the user for the appointment date, appointment time, doctor of preference and email ID. The user can book the appointment from 9 AM to 8 PM from Monday to Friday, and from 9 AM to 12 AM on Saturdays. You need to remember that today's date is {date.today()} and day is {day_list[date.today().weekday()]}. Check if the time provided by the user is within the working hours then only you will proceed.
             Also check if the appointment date is according to the time frame of the chosen doctor.
        

Instructions: 
- If a user whats to reschedule follow the following TWO steps:
    1. Canceling previous booking:
        1. ask for the date of the original appointment
        2. ask for the time of the original appointment
        3. ask for the email address of the user
        4. Check if all the details above have been given
        5. Check if the function appointment_delete has deleted the previous appointment and tell the user the appointment was cancelled by saying "yay it was canceled". Then it is important tha you proceed with the following questions:
    2. Book a new appointment:
        1. ask for the date for the new appointment
        2. ask for the time for the new appointment
        3. ask for the doctor of preference for the new appointment (make sure it exists)
        4. after all needed information was gathered make sure the function appointment_booking has booked the new appointment, if so, tell the user the appointment was rescheduled
- If a user wants to book an appointment:
    1. ask for the date of the appointment
    2. ask for the time of the appointment
    3. ask for the doctor of preference (it has to be an existing doctor)
    4. ask for the email address of the user
    5. Check if all the details above have been given and if they were, tell them to the user and ask for confirmation
    6. Make sure the function appointment_booking has booked the appointment by checking if the function returned "Appointment added successfully.", and, if so, tell the user the appointment was booked
- If a user wants to cancel an appointment:
    1. ask for the date of the appointment
    2. ask for the time of the appointment
    3. ask for the email address of the user
    4. Check if all the details above have been given and then make sure the function appointment_delete has deleted the appointment by returning "Appointment deleted successfully."

IMPORTANT:
- Don't make assumptions about what values to plug into functions, if the user does not provide one or more of the required parameters then you must ask for clarification.
- If the doctor is not available at the requested time, tell the user the time frames he is available
- If the user chooses a doctor and the time for the appointment which are not compatible, you must ask to change one of them.
- If a user request is ambiguous, always kindly ask for clarification.
- If a user uses a AM/PM time structure and didn't specify "ante meridiem (AM)" or "post meridiem (PM)" while providing the time, then you must ask for clarification.

                         
ATTENTION: Make sure to follow the instructions carefully while processing the request. 
"""}]

user_input = input("Please enter your question here: (if you want to exit then write 'exit' or 'bye'.) ")

while user_input.strip().lower() != "exit" and user_input.strip().lower() != "bye":
    
    messages.append({"role": "user", "content": user_input})

    # calling chat_completion_request to call ChatGPT completion endpoint
    chat_response = chat_completion_request(
        messages, functions=functions
    )

    # fetch response of ChatGPT and call the function
    assistant_message = chat_response.json()["choices"][0]["message"]

    if assistant_message['content']:
        print("Response is: ", assistant_message['content'])
        messages.append({"role": "assistant", "content": assistant_message['content']})
    else:
        fn_name = assistant_message["function_call"]["name"]
        arguments = assistant_message["function_call"]["arguments"]
        function = locals()[fn_name]
        result = function(arguments)
        print("Response is: ", result)
       
    user_input = input("Please enter your question here: ")

