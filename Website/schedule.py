import streamlit as st
from firebase_admin import firestore
# from account import Usernm

  
def app():
    
    if 'db' not in st.session_state:
        st.session_state.db = ''

    db=firestore.client()
    st.session_state.db=db
    # st.title('  :violet[DOC-IT-RIGHT]  :sunglasses:')
    
    ph = ''
    if st.session_state.username=='':
        ph = 'Login first!!'
    else:
        ph = 'Hello, ' + st.session_state.username + '!'
    post=st.text_area(label=' :orange[+ New Post]', placeholder=ph, height=None, max_chars=500)