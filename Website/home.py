import streamlit as st

def app():
    st.subheader('Welcome Home! :house:')


    # # Example: Counter without session state
    # counter = 0

    # if st.button('Increment Counter'):
    #     counter += 1

    # st.write('Counter:', counter)

    if 'counter' not in st.session_state:
        st.session_state.counter = 0

    if st.button('Increment Counter'):
        st.session_state.counter += 1

    st.write('Counter:', st.session_state.counter)

    st.write(st.session_state.username)