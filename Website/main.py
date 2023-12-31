import streamlit as st

from streamlit_option_menu import option_menu


import home, account, chat, schedule, about
st.set_page_config(
        page_title="Doc-IT-Right",
)



# class MultiApp:

#     def __init__(self):
#         self.apps = []

#     def add_app(self, title, func):

#         self.apps.append({
#             "title": title,
#             "function": func
#         })

#     def run():
#         # app = st.sidebar(
#         with st.sidebar:        
#             app = option_menu(
#                 menu_title='Doc-IT-Right',
#                 options=['Chat','Account','Schedules','about'],
#                 icons=['chat-fill','person-circle','calendar-week-fill','info-circle-fill'],
#                 menu_icon='check-circle-fill',
#                 default_index=1,
#                 styles={
#                     "container": {"padding": "5!important","background-color":'black'},
#         "icon": {"color": "white", "font-size": "23px"}, 
#         "nav-link": {"color":"white","font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "blue"},
#         "nav-link-selected": {"background-color": "#02ab21"},}
                
#                 )

        
#         if app == "Chat":
#             chat.app()
#         if app == "Account":
#             account.app()          
#         if app == 'Schedules':
#             schedule.app()
#         if app == 'about':
#             about.app()    
                      
#     run()            


class MultiApp:
    def __init__(self):
        self.apps = []

    def add_app(self, title, func):
        self.apps.append({
            "title": title,
            "function": func
        })

    def run(self):
        with st.sidebar:        
            app = option_menu(
                menu_title='Doc-IT-Right',
                options=['Home', 'Account','Chat','Schedules','about'],
                icons=['house-fill','person-circle','chat-fill','calendar-week-fill','info-circle-fill'],
                menu_icon='check-circle-fill',
                default_index=1,
                styles={
                    "container": {"padding": "5!important","background-color":'black'},
        "icon": {"color": "white", "font-size": "23px"}, 
        "nav-link": {"color":"white","font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "blue"},
        "nav-link-selected": {"background-color": "#02ab21"},}
                
                )

        for app_info in self.apps:
            if app == app_info["title"]:
                app_info["function"]()


# Create an instance of MultiApp
multi_app = MultiApp()

# Register apps
multi_app.add_app("Home", home.app)
multi_app.add_app("Account", account.app)
multi_app.add_app("Chat", chat.app)
multi_app.add_app("Schedules", schedule.app)
multi_app.add_app("About", about.app)

# Run the selected app
multi_app.run()
