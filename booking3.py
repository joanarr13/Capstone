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

limit1 = datetime.strptime("9:00:00", "%H:%M:%S").time()
limit2 = datetime.strptime("20:00:00", "%H:%M:%S").time()
limit3 = datetime.strptime("12:00:00", "%H:%M:%S").time()

def is_time_in_range(selected_time, time_list):
    selected_time = datetime.strptime(selected_time, "%H:%M:%S").time()
    
    for time in time_list:
        time_obj = datetime.strptime(time, "%H:%M:%S").time()
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

def get_available_time_slots(doctor, day):
    # Function to get available time slots for a specific doctor on a given day
    doctor_schedule = doctor_time_tables.get(doctor, {}).get(day, {})
    
    if not doctor_schedule:
        return []

    start_time = datetime.strptime(doctor_schedule.get('start', '00:00:00'), "%H:%M:%S").time()
    end_time = datetime.strptime(doctor_schedule.get('end', '23:59:59'), "%H:%M:%S").time()

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
    return f"{doctor} is available on {day} at the following times: {', '.join(available_times)}."

def choose_doctor_based_on_time(requested_time_str, requested_doctor, requested_date_str):
    available_doctors = []
    requested_date = datetime.strptime(requested_date_str, "%Y-%m-%d").strftime("%A").lower()   # Monday
    requested_time = datetime.strptime(requested_time_str, "%H:%M:%S").time()  # 09:00:00

    for doctor, schedules in doctor_time_tables.items():
        for day, time_range in schedules.items():
            if day == requested_date:
                start_time = datetime.strptime(time_range['start'], "%H:%M:%S").time()
                end_time = datetime.strptime(time_range['end'], "%H:%M:%S").time()

                if start_time <= requested_time <= end_time:
                    available_doctors.append(doctor)

    if not available_doctors:
        return None  # No available doctors for the requested time

    if requested_doctor in available_doctors:
        return requested_doctor

    return None # The originally requested doctor is not available at the requested time

def doctor_checking(arguments):
    provided_date =  str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
    provided_time = str(datetime.strptime(json.loads(arguments)['time'].replace("PM","").replace("AM","").strip(), "%H:%M:%S").time())
    start_date_time = provided_date + " " + provided_time
    timezone = pytz.timezone('Europe/Lisbon')
    start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))
    email_address = json.loads(arguments)['email_address']
    doctor = json.loads(arguments)['doctor']
    end_date_time = start_date_time + timedelta(hours=0.5)

    
    existing_doctors = ["Dr. João Santos", "Dr. Miguel Costa", "Dra. Sofia Pereira", 'Dra. Mariana Chagas', 'Dr. António Oliveira',
                            'Dra. Inês Martins', 'Dr. Ângelo Rodrigues', 'Dr. José Dias']


    if doctor is not None:
        if doctor not in existing_doctors:
            return "Please choose a valid doctor from the list: " + ", ".join(existing_doctors)
                
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
                return False
            # Update the 'doctor' variable with the chosen doctor
            #doctor = updated_doctor
            # Confirm the appointment
            return True


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
    
                if day_list[start_date_time.date().weekday()] == "Saturday":
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

    try:
        provided_date =  str(datetime.strptime(json.loads(arguments)['date'], "%Y-%m-%d").date())
        provided_time = str(datetime.strptime(json.loads(arguments)['time'].replace("PM","").replace("AM","").strip(), "%H:%M:%S").time())
        start_date_time = provided_date + " " + provided_time
        timezone = pytz.timezone('Europe/Lisbon')
        start_date_time = timezone.localize(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))
        email_address = json.loads(arguments)['email_address']
        doctor = json.loads(arguments)['doctor']


        existing_doctors = ["Dr. João Santos", "Dr. Miguel Costa", "Dra. Sofia Pereira", 'Dra. Mariana Chagas', 'Dr. António Oliveira',
                            'Dra. Inês Martins', 'Dr. Ângelo Rodrigues', 'Dr. José Dias']

        
        if provided_date and provided_time and email_address:
            if start_date_time < datetime.now(timezone):
                return "Please enter valid date and time."
            else:
                if day_list[start_date_time.date().weekday()] == "Saturday":
                    if start_date_time.time() >= limit1 and start_date_time.time() <= limit3:
                        end_date_time = start_date_time + timedelta(hours=2)
                        events = service.events().list(calendarId="primary").execute()
                        id = ""
                        final_event = None
                        for event in events['items']:
                            if event['attendees'][0]['email'] == email_address:
                                id = event['id']
                                final_event = event
                        if final_event:
                            if appointment_checking(arguments) == True:
                                final_event['start']['dateTime'] = start_date_time.strftime("%Y-%m-%dT%H:%M:%S")
                                final_event['end']['dateTime'] = end_date_time.strftime("%Y-%m-%dT%H:%M:%S")
                                service.events().update(calendarId='primary', eventId=id, body=final_event).execute()
                                return "Appointment rescheduled."
                            else:
                                return "Sorry, slot is not available at this time, please try a different time."
                        else:
                            return "No registered event found on your id."
                    else:
                        return "Please try to book an appointment into working hours, which is 9 AM to 11 AM at saturday."
                else:
                    if start_date_time.time() >= limit1 and start_date_time.time() <= limit2: #Day of the week
                        end_date_time = start_date_time + timedelta(hours=2)
                        events = service.events().list(calendarId="primary").execute()
                        id = ""
                        final_event = None
                        for event in events['items']:
                            if event['attendees'][0]['email'] == email_address:
                                id = event['id']
                                final_event = event
                        if final_event:
                            if appointment_checking(arguments) == "Slot is available for appointment. Would you like to proceed?":
                                final_event['start']['dateTime'] = start_date_time.strftime("%Y-%m-%dT%H:%M:%S")
                                final_event['end']['dateTime'] = end_date_time.strftime("%Y-%m-%dT%H:%M:%S")
                                service.events().update(calendarId='primary', eventId=id, body=final_event).execute()
                                return "Appointment rescheduled."
                            else:
                                return "Sorry, slot is not available at this time, please try a different time."
                        else:
                            return "No registered event found on your id."
                    else:
                        return "Please try to book an appointment into working hours, which is 9 AM to 7 PM."
        else: 
            return "Please provide all necessary details: Start date, End date and Email address."
        
    except Exception as e:
            import traceback
            traceback.print_exc()
            return "We are enable to process. Please try again."

    
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
                    "description": "doctor of preference, must be one among the existants: {existing_doctors}, otherwise a random one will be assigned"
                },
                "date": {
                    "type": "string",
                    "format": "date",
                    "example":"2023-07-23",
                    "description": "Date, when the user wants to book an appointment. The date must be in the format of YYYY-MM-DD.",
                },
                "time": {
                    "type": "string",
                    "example": "20:12:45", 
                    "description": "time, on which user wants to book an appointment on a specified date. Time must be in %H:%M:%S format.",
                },
                "email_address": {
                    "type": "string",
                    "description": "email_address of the user gives for identification.",
                }
                
            },
            "required": ["date","time","email_address", "doctor"],
        },
    },
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
                    "description": "It is the date on which the user wants to reschedule the appointment. The date must be in the format of YYYY-MM-DD.",
                },
                "time": {
                    "type": "string",
                    "description": "It is the time on which user wants to reschedule the appointment. Time must be in %H:%M:%S format.",
                },
                "email_address": {
                    "type": "string",
                    "description": "email_address of the user gives for identification.",
                },
                'doctor': {
                    "type" : "string",
                    "description": "doctor of preference, must be one among the existants: {existing_doctors}, otherwise a random one will be assigned"
                }
            },
            "required": ["date","time","email_address", "doctor"],
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
                    "description": "Date, on which user has appointment and wants to delete it. The date must be in the format of YYYY-MM-DD.",
                },
                "time": {
                    "type": "string",
                    "description": "time, on which user has an appointment and wants to delete it. Time must be in %H:%M:%S format.",
                },
                "email_address": {
                    "type": "string",
                    "description": "email_address of the user gives for identification.",
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
                    "description": "Date, when the user wants to book an appointment. The date must be in the format of YYYY-MM-DD.",
                },
                "time": {
                    "type": "string",
                    "example": "20:12:45", 
                    "description": "time, on which user wants to book an appointment on a specified date. Time must be in %H:%M:%S format.",
                },
                
                
            },
            "required": ["date","time"],
        },
    }]


#-------------TEST---------------


day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

messages = [{"role": "system", "content": f"""You are an expert in booking appointments. You need to ask the user for the appointment date, appointment time, doctor of preference and email ID. The user can book the appointment from 9 AM to 8 PM from Monday to Friday, and from 9 AM to 12 AM on Saturdays. You need to remember that today's date is {date.today()} and day is {day_list[date.today().weekday()]}. Check if the time provided by the user is within the working hours then only you will proceed.
             Also check if the appointment date is according to the time frame of the chosen doctor.

Instructions: 
- Don't make assumptions about what values to plug into functions, if the user does not provide any of the required parameters then you must need to ask for clarification.
- Make sure the email Id is valid and not empty.
- Make sure the doctor asked for exists.
- If the doctor is not available at that time, show the time frames he is available
- If the person chooses a doctor and the time of the appointment is not compatible you must ask to change one of them.
- If a user request is ambiguous, then also you need to ask for clarification.
- When a user asks for a rescheduling date or time of the current appointment, then you must ask for the new appointment details only.
- If a user didn't specify "ante meridiem (AM)" or "post meridiem (PM)" while providing the time, then you must have to ask for clarification. If the user didn't provide day, month, and year while giving the time then you must have to ask for clarification.

                         
 
Make sure to follow the instructions carefully while processing the request. 
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
