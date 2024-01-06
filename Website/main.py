import streamlit as st
from streamlit_option_menu import option_menu
import home, account, chat_4, schedule, about

st.set_page_config(page_title="Doc-IT-Right", initial_sidebar_state="expanded")


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
                    "icon": {"font-size": "23px"}, 
                    "nav-link": {"font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "blue"},
                    "nav-link-selected": {"background-color": "#02ab21"}}
                )


        for app_info in self.apps:
            if app == app_info["title"]:
                app_info["function"]()


# Create an instance of MultiApp
multi_app = MultiApp()

# Register apps
multi_app.add_app("Home", home.app)
multi_app.add_app("Account", account.app)
multi_app.add_app("Chat", chat_4.app)
multi_app.add_app("Schedules", schedule.app)
multi_app.add_app("about", about.app)

# Run the selected app
multi_app.run()
