import streamlit as st

def app():
    st.image("images/logo.png")

    st.title('Welcome Home! :house:')

    st.header('Come meet Dr. ChatBot!')
    st.caption('Here you can interact with it and ask it your health related questions.')

    st.divider()
    
    st.subheader('What can Dr. ChatBot do for you?')

    st.write(" - 🪪 Schedule or change your appointments", unsafe_allow_html=True)

    st.write(" - 👨🏽‍⚕️ Ask doubts about your medication", unsafe_allow_html=True)

    st.write(" - 💡 Other questions about your health", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader('To learn more explore our streamlit app and our website!😉')

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

    st.caption("\nTo access Doc IT right's full website please click [here](https://docitrightcp.wixsite.com/doc-it-right).")