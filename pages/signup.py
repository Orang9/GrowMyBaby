import streamlit as st
from utils.db import add_user

def signup():
    st.title("Sign Up")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Sign Up"):
        if add_user(username, password):
            st.success("Account created successfully! Please go to the Login page to sign in.")
        else:
            st.error("Username already exists. Please choose a different username.")

if __name__ == "__main__":
    signup()
