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
                        "description": "doctor of preference" #, must be one among the existants: {existing_doctors}, otherwise random one will be assigned"
                    },
                    "book_date": {
                        "type": "string",
                        "format": "date",
                        "example":"2023-07-23",
                        "description": "Date to which the user wants to book an appointment." # The date must be in the format of YYYY-MM-DD, if it is not, convert it and store it in this format.",
                    },
                    "book_time": {
                        "type": "string",
                        "example": "20:12:45", 
                        "description": "time to which the user wants to book an appointment on a specified date." # Time must be in %H:%M:%S format, if it is not, convert it and store it in this format.",
                    },
                    "email_address": {
                        "type": "string",
                        "description": "email_address of the user gives for identification.",
                    }   
                },
                "required": ["book_date","book_time","email_address", "doctor"],
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
                    }
                },
            
                "required": ["del_date","del_time","email_address","doctor","book_date","book_time"],
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
    },]