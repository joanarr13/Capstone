import streamlit as st 

st.title("Log in")

# input
user_input = st.text_input("Enter your username", "Your Name")

user_input = st.text_input("Enter your password", "Password")


with st.sidebar:
    st.title("Hello world from side bar")