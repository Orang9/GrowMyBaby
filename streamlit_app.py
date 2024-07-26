import streamlit as st
import os
import pandas as pd
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
from utils.db import get_user, add_user

# Memuat variabel dari file .env
load_dotenv()

# Connect to MongoDB Atlas
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable not set")

client = MongoClient(mongo_uri)
db = client["sic5_belajar"]

# Fungsi untuk mengecek apakah pengguna sudah login
def is_logged_in():
    return st.session_state.get('logged_in', False)

# Fungsi untuk logout
def logout():
    st.session_state['logged_in'] = False
    st.experimental_rerun()

# Login atau Sign Up Page
def login_page():
    st.title("Welcome")
    choice = st.radio("Sign In or Sign Up", ["sign in", "sign up"])

    if choice == "sign up":
        st.title("Sign Up Page")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            if add_user(username, password):
                st.success("Account created successfully! Please go to the Login page to sign in.")
            else:
                st.error("Username already exists. Please choose a different username.")
            
    else:
        st.title("Sign In Page")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign In"):
            user = get_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

# Dashboard Page
def dashboard_page():
        st.sidebar.title(f"Welcome, {st.session_state.username}")
        selected_page = st.sidebar.radio("Navigation", ["Home", "Logout"])
        if selected_page == "Home":
            collection = db['data_anak']

            data_berat_tinggi = {
                "Usia (bulan)": [6, 12, 18, 24, 30, 36, 48, 60],
                "Berat Badan Rata-rata Laki-laki (kg)": [7.9, 9.6, 10.9, 12.2, 13.3, 14.3, 16.3, 18.3],
                "Berat Badan Rata-rata Perempuan (kg)": [7.3, 8.9, 10.2, 11.5, 12.6, 13.9, 15.5, 17.4],
                "Tinggi Badan Rata-rata Laki-laki (cm)": [61.0, 69.7, 76.0, 81.8, 87.1, 92.0, 101.7, 111.2],
                "Tinggi Badan Rata-rata Perempuan (cm)": [60.5, 68.7, 74.9, 80.3, 85.3, 90.4, 99.1, 108.2]
            }

            df_berat_tinggi = pd.DataFrame(data_berat_tinggi)

            st.title('Check Stunting Anak dari 6 Bulan hingga 5 Tahun')

            jenis_kelamin = st.radio("Jenis kelamin anak:", ["Laki-laki", "Perempuan"])
            usia_anak = st.number_input("Usia anak (bulan):", min_value=6, max_value=60, step=6)

            response = requests.get('https://iot.herolab.id/data')
            if response.status_code == 200:
                data_store = response.json()
                if data_store:
                    berat_badan_anak = data_store[-1]['weight']
                    tinggi_badan_anak = data_store[-1]['height']
                else:
                    berat_badan_anak = 0.0
                    tinggi_badan_anak = 0.0
            else:
                st.error("Gagal mengambil data dari server Flask")
                berat_badan_anak = 0.0
                tinggi_badan_anak = 0.0

            st.write(f"Usia anak: {usia_anak} bulan")
            st.write(f"Berat badan anak: {berat_badan_anak:.2f} kg")
            st.write(f"Tinggi badan anak: {tinggi_badan_anak:.2f} cm")

            if jenis_kelamin == "Laki-laki":
                berat_badan_rata_rata = df_berat_tinggi[df_berat_tinggi["Usia (bulan)"] == usia_anak]["Berat Badan Rata-rata Laki-laki (kg)"].values[0]
                tinggi_badan_rata_rata = df_berat_tinggi[df_berat_tinggi["Usia (bulan)"] == usia_anak]["Tinggi Badan Rata-rata Laki-laki (cm)"].values[0]
            else:
                berat_badan_rata_rata = df_berat_tinggi[df_berat_tinggi["Usia (bulan)"] == usia_anak]["Berat Badan Rata-rata Perempuan (kg)"].values[0]
                tinggi_badan_rata_rata = df_berat_tinggi[df_berat_tinggi["Usia (bulan)"] == usia_anak]["Tinggi Badan Rata-rata Perempuan (cm)"].values[0]

            keterangan = ""
            if berat_badan_anak < berat_badan_rata_rata - 2 and tinggi_badan_anak < tinggi_badan_rata_rata - 2:
                status = "Stunting"
                keterangan = "Berat badan dan tinggi badan anak di bawah rata-rata."
            elif berat_badan_anak < berat_badan_rata_rata - 2:
                status = "Stunting"
                keterangan = "Berat badan anak di bawah rata-rata."
            elif tinggi_badan_anak < tinggi_badan_rata_rata - 2:
                status = "Stunting"
                keterangan = "Tinggi badan anak di bawah rata-rata."
            else:
                status = "Tidak Stunting"

            st.write(f"Status anak: {status}")
            if keterangan:
                st.write(f"Keterangan: {keterangan}")

            st.subheader("Berat Badan Rata-rata Anak Berdasarkan Usia:")
            st.dataframe(df_berat_tinggi[["Usia (bulan)", "Berat Badan Rata-rata Laki-laki (kg)", "Berat Badan Rata-rata Perempuan (kg)"]])

            st.subheader("Tinggi Badan Rata-rata Anak Berdasarkan Usia:")
            st.dataframe(df_berat_tinggi[["Usia (bulan)", "Tinggi Badan Rata-rata Laki-laki (cm)", "Tinggi Badan Rata-rata Perempuan (cm)"]])

            if st.button("Post to MongoDB"):
                data_anak = {
                    "usia": usia_anak,
                    "berat_badan": berat_badan_anak,
                    "tinggi_badan": tinggi_badan_anak,
                    "jenis_kelamin": jenis_kelamin,
                    "status": status,
                    "keterangan": keterangan
                }
                collection = db['data_anak']
                collection.insert_one(data_anak)
                st.success("Data berhasil dikirim ke MongoDB!")
        elif selected_page == "Logout":
            st.title('Anda telah logout')
            st.session_state.logged_in = False
            st.session_state.username = ''

# Main function
def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if is_logged_in():
        dashboard_page()
    else:
        login_page()



if __name__ == '__main__':
    main()
