import streamlit as st
from firebase_admin import firestore
from clinic_info import limit1, limit2, limit3, doctor_time_tables

def app():
    if 'db' not in st.session_state:
        st.session_state.db = ''

    db=firestore.client()
    st.session_state.db=db
    
    if st.session_state.username=='':

        st.text('Login to be able to use the chat!!')

    else:

        st.header("Doc-IT-Right Schedules⏱️")

        bordered_text = f"""
        <div style="
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            font-size: 18px;
        ">
            👋Hello, {st.session_state.username}! \n
            Welcome to the Schedules page. \n
            Here you can find the clinic's opening hours,\n
            and at what days and times your favourite doctor works.
        </div>
        """

        st.markdown(bordered_text, unsafe_allow_html=True)
        st.divider()      

        st.subheader("🕒Clinic Working Hours:")
        st.write("")

        st.markdown(f"""<p style="font-size: 130%;"> &#8226; Monday to Friday: {limit1} - {limit2}</p>""", unsafe_allow_html=True)
        st.markdown(f"""<p style="font-size: 130%;"> &#8226; Saturday: {limit1} - {limit3}</p>""", unsafe_allow_html=True)
        st.markdown(f"""<p style="font-size: 130%;"> &#8226; Sunday: Closed</p>""", unsafe_allow_html=True)

        st.write("")
        st.divider()
        st.subheader("🩺Doctors and their schedules:")
        st.write("")  

        options = st.multiselect(
            'Choose your preferable day:',
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
            default=['Monday']
        )

        for i in range(0, len(options), 2):
            col1, col2 = st.columns(2)

            for day in options[i:i + 2]:
                col = col1 if day == options[i] else col2
                col.markdown(f"<p style='font-size: 150%;'>Doctors available on {day.capitalize()}:</p>", unsafe_allow_html=True)

                for doctor, schedule in doctor_time_tables.items():
                    if day.lower() in schedule:
                        col.markdown(f"<p style='font-size: 150%;'>{doctor}</p>", unsafe_allow_html=True)
                        col.write(f"{schedule[day.lower()]['start']} to {schedule[day.lower()]['end']}")
                        col.write("")