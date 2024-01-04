from datetime import datetime

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