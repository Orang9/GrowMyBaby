import streamlit as st
from utils.db import get_user

def login():
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Sign In"):
        user = get_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()  # Refresh the page to navigate to the welcome page
        else:
            st.error("Invalid username or password")

if __name__ == "__main__":
    login()
