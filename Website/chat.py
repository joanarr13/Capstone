import streamlit as st
from firebase_admin import firestore

# def app():
    
#     st.text('home')


def app():
    
    if 'db' not in st.session_state:
        st.session_state.db = ''

    db=firestore.client()
    st.session_state.db=db
    # st.title('  :violet[Pondering]  :sunglasses:')
    
    #ph = ''
    if st.session_state.username=='':
        #ph = 'Login to be able to post!!'
        st.text('Login to be able to use the chat!!')
    else:
        st.text('home')