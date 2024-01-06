import joblib

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
                        "description": "the number of special requests the user made for the appointment. If there are no special requests it is 0.",
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



model = joblib.load('noshow_model.joblib')
scaler = joblib.load('robust_scaler.joblib')
features_scaler = ['AppointmentMonth', 'AppointmentWeekNumber', 'AppointmentDayOfMonth', 'AppointmentHour', 'WeekendConsults', 'WeekdayConsults', 'Adults', 'Children', 'Babies', 'FirstTimePatient', 'AffiliatedPatient', 'PreviousAppointments', 'PreviousConsults', 'PreviousNoShows', 'LastMinutesLate', 'OnlineBooking', 'AppointmentChanges', 'BookingToConsultDays', 'ParkingSpaceBooked', 'SpecialRequests', 'NoInsurance', 'ExtraExamsPerConsult', 'DoctorRequested', 'DoctorAssigned', 'ConsultPriceEuros', 'ConsultPriceUSD', '%PaidinAdvance', 'CountryofOriginAvgIncomeEuros (Year-2)', 'CountryofOriginAvgIncomeEuros (Year-1)', 'CountryofOriginHDI (Year-1)']
feature_names = ['AppointmentWeekNumber', 'AppointmentDayOfMonth', 'AppointmentHour', 'WeekendConsults', 'WeekdayConsults', 'Adults', 'Children', 'Babies', 'AffiliatedPatient', 'PreviousAppointments', 'PreviousNoShows', 'LastMinutesLate', 'OnlineBooking', 'AppointmentChanges', 'BookingToConsultDays', 'ParkingSpaceBooked', 'SpecialRequests', 'NoInsurance', 'ExtraExamsPerConsult', 'DoctorAssigned', 'ConsultPriceEuros', '%PaidinAdvance', 'CountryofOriginHDI (Year-1)']
