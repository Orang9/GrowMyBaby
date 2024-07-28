import openai
import streamlit as st
import os
import pandas as pd
import requests
import joblib
from pymongo import MongoClient
from typing import Generator
from PIL import Image
from utils.db import add_anak, cek_anak, delete_anak, add_user, get_session_ids_for_user, get_user, save_session_to_db, load_session_from_db, get_session_name, delete_session_from_db, update_anak
from models.test_models.test_stunting_classifier import stunting_classifier
import datetime

# Connect to MongoDB Atlas
mongo_uri = st.secrets["MONGO_URI"]
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
    st.rerun()

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
                st.rerun()
            else:
                st.error("Invalid username or password")

def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
    """Yield chat response content from the Groq API response."""
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def load_form():
    st.write("Tolong masukkan data berat dan tinggi badan anak:")
    weight = st.number_input("Berat Badan (kg)", min_value=0.0, max_value=100.0, step=0.1)
    height = st.number_input("Tinggi Badan (cm)", min_value=0.0, max_value=200.0, step=0.1)
    if st.button("Konfirmasi", key='submit_button'):
        data = {
            "weight": weight,
            "height": height
        }
        return data



# The Main App-----------------------------------------------------------------------------------
icon_png = Image.open("assets/images/GrowMyBaby Icon.png")
logo_png = Image.open("assets/images/GrowMyBaby Logo.png")
st.logo(logo_png, icon_image=icon_png)

# Dashboard Page
def dashboard_page():
        sidebar_placeholder = st.sidebar.empty()
        content_placeholder = st.empty()
        with sidebar_placeholder.container():
            st.sidebar.title(f"Welcome, {st.session_state.username}")
            selected_page = st.sidebar.radio("Navigation", ["Dashboard","You'r Baby" , "ChatBot", "Logout"])

            st.session_state.selected_page = selected_page

        if selected_page == "Dashboard":
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

            nama_anak = st.text_input("Nama anak:", key='nama_anak_input', placeholder="Nama anak")
            jenis_kelamin = st.radio("Jenis kelamin anak:", ["Laki-laki", "Perempuan"], key='jenis_kelamin_radio')
            usia_anak = st.number_input("Usia anak (bulan):", min_value=6, max_value=60, step=1, key='usia_anak_input')
            keterangan = st.text_area("Keterangan:", key='keterangan_input', placeholder="keterangan (opsional)")

            try: 
                response = requests.get('https://iot.herolab.id/data')
                if response.status_code == 200:
                    data_store = response.json()
                    if data_store:
                        berat_badan_anak = data_store[-1]['weight']
                        tinggi_badan_anak = data_store[-1]['height']
                    else:
                        berat_badan_anak = 0.0
                        tinggi_badan_anak = 0.0

            except requests.exceptions.RequestException as e:
                st.error("Gagal mengambil data dari server Flask")
                st.warning("Silakan masukkan data berat dan tinggi badan anak secara manual.")
                berat_badan_anak = 0.0
                tinggi_badan_anak = 0.0
                data_bb_tb_anak = load_form()
                if data_bb_tb_anak:
                    berat_badan_anak = data_bb_tb_anak["weight"]
                    tinggi_badan_anak = data_bb_tb_anak["height"]
                keterangan = st.text_input("Keterangan", key='keterangan_input', placeholder="Keterangan tambahan (opsional)")

            st.write(f"Usia anak: {usia_anak} bulan")
            st.write(f"Berat badan anak: {berat_badan_anak:.2f} kg")
            st.write(f"Tinggi badan anak: {tinggi_badan_anak:.2f} cm")

            # Load the saved model
            ml_model = joblib.load('models/saved_models/stunting_classifier.pkl')

            status = stunting_classifier(ml_model, usia_anak, jenis_kelamin, tinggi_badan_anak)

            if status == 0:
                status = "Normal"
            elif status == 1:
                status = "Severely Stunted"
            elif status == 2:
                status = "Stunted"
            elif status == 3:
                status = "Tinggi"

            st.subheader(f"Status Stunting Anak: {status}")
            if st.button("Simpan Data Anak", key='post_to_mongodb_button'):
                data_anak = {
                    "usia": usia_anak,
                    "berat_badan": berat_badan_anak,
                    "tinggi_badan": tinggi_badan_anak,
                    "jenis_kelamin": jenis_kelamin,
                    "status": status,
                    "keterangan": "" + keterangan
                }
                collection = db['data_anak']
                collection.insert_one(data_anak)
                waktu_pengambilan_data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                add_anak(nama_anak, usia_anak, jenis_kelamin, berat_badan_anak, tinggi_badan_anak, status, keterangan, waktu_pengambilan_data, st.session_state.username)
                st.success("Data berhasil terkirim")

            st.subheader("Berat Badan Rata-rata Anak Berdasarkan Usia:")
            st.dataframe(df_berat_tinggi[["Usia (bulan)", "Berat Badan Rata-rata Laki-laki (kg)", "Berat Badan Rata-rata Perempuan (kg)"]])

            st.subheader("Tinggi Badan Rata-rata Anak Berdasarkan Usia:")

            # Load the dataset
            df = pd.read_csv('models/dataset/Stunting_Classification.csv').drop(columns=['Status Gizi'])

            # Group by age and gender, then calculate the mean height
            grouped_df = df.groupby(['Umur (bulan)', 'Jenis Kelamin']).mean().reset_index()

            # Pivot the table to get the desired format
            pivot_df = grouped_df.pivot(index='Umur (bulan)', columns='Jenis Kelamin', values='Tinggi Badan (cm)').reset_index()

            pivot_df = pivot_df.fillna("Data belum tersedia")

            # Rename the columns for clarity
            pivot_df.columns = ['Umur (bulan)', 'Tinggi Badan Rata-rata Laki-laki (cm)', 'Tinggi Badan Rata-rata Perempuan (cm)']

            st.dataframe(pivot_df[["Umur (bulan)", "Tinggi Badan Rata-rata Laki-laki (cm)", "Tinggi Badan Rata-rata Perempuan (cm)"]])
            
        elif selected_page == "You'r Baby":
            st.title("You'r Baby")
            st.write("This is the page where you can see the data of your baby")
            user_id = st.session_state.username
            anak = db["anak"]
            data = anak.find({"user_id": user_id})
            df = pd.DataFrame(data)
            if not df.empty:
                df = df.drop(columns=["_id", "user_id"])
            st.write(df)

            # Radio button untuk memilih operasi
            operation = st.radio("Pilih operasi", ["Tambahkan", "Update", "Hapus"], key="operation_radio")

            if operation == "Tambahkan" or operation == "Update":
                st.write(f"{operation} data anak:")
                nama = st.text_input("Nama", key="nama_input", placeholder="Nama anak")
                umur = st.number_input("Umur Anak (bulan)", key="umur_input", placeholder="Umur anak", step=1)
                jenis_kelamin = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"], key="jenis_kelamin_radio")

                try: 
                    response = requests.get('https://iot.herolab.id/data')
                    if response.status_code == 200:
                        data_store = response.json()
                        if data_store:
                            berat_badan_anak = data_store[-1]['weight']
                            tinggi_badan_anak = data_store[-1]['height']
                        else:
                            berat_badan_anak = 0.0
                            tinggi_badan_anak = 0.0
                except requests.exceptions.RequestException as e:
                    st.error("Gagal mengambil data dari server Flask")
                    st.warning("Silakan masukkan data berat dan tinggi badan anak secara manual.")
                    berat_badan_anak = 0.0
                    tinggi_badan_anak = 0.0
                    data_bb_tb_anak = load_form()
                    if data_bb_tb_anak:
                        berat_badan_anak = data_bb_tb_anak["weight"]
                        tinggi_badan_anak = data_bb_tb_anak["height"]

                keterangan = st.text_area("Keterangan:", key='keterangan_input', placeholder="Keterangan (opsional)")
                waktu_pengambilan_data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                ml_model = joblib.load('models/saved_models/stunting_classifier.pkl')
                status = stunting_classifier(ml_model, umur, jenis_kelamin, tinggi_badan_anak)

                if status == 0:
                    status = "Normal"
                elif status == 1:
                    status = "Severely Stunted"
                elif status == 2:
                    status = "Stunted"
                elif status == 3:
                    status = "Tinggi"

                st.write(f"Status Stunting Anak: {status}")
                st.write(f"Berat badan anak: {berat_badan_anak:.2f} kg")
                st.write(f"Tinggi badan anak: {tinggi_badan_anak:.2f} cm")

                if operation == "Tambahkan" and st.button("Tambahkan", key="tambahkan_button"):
                    add_anak(nama, umur, jenis_kelamin, berat_badan_anak, tinggi_badan_anak, status, keterangan, waktu_pengambilan_data, user_id)
                    st.success("Data anak berhasil ditambahkan!")
                    st.rerun()

                if operation == "Update" and st.button("Update", key="update_button"):
                    if cek_anak(nama, user_id):
                        update_anak(nama, umur, jenis_kelamin, berat_badan_anak, tinggi_badan_anak, status, keterangan, waktu_pengambilan_data, user_id)
                        st.success("Data anak berhasil diupdate!")
                        st.rerun()
                    else:
                        st.error("Data anak tidak ada!")

            elif operation == "Hapus":
                st.write("Hapus data anak:")
                nama = st.text_input("Nama", key="nama_hapus_input", placeholder="Nama anak")
                if st.button("Hapus", key="hapus_button"):
                    if cek_anak(nama, user_id):
                        if delete_anak(nama, user_id):
                            st.success("Data anak berhasil dihapus!")
                            st.rerun()
                        else:
                            st.error("Terjadi kesalahan saat menghapus data anak!")
                    else:
                        st.error("Data anak tidak ada!")

                
        elif selected_page == "ChatBot":
            st.title("GrowMyBaby ChatBot")
            messages = []
            user_input = st.text_input("Ask GrowMyBaby ChatBot", key="user_input")

            if user_input:
                user_message = {"role": "user", "content": user_input}
                messages.append(user_message)
                save_session_to_db(db, st.session_state.username, user_message)

                st.markdown("#### Loading...")

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.6,
                    stream=True,
                )

                chat_responses = generate_chat_responses(response)
                for chat_response in chat_responses:
                    messages.append({"role": "assistant", "content": chat_response})
                    save_session_to_db(db, st.session_state.username, {"role": "assistant", "content": chat_response})
                    st.markdown(f"**Assistant:** {chat_response}")

            if st.button("Clear Chat History"):
                st.session_state["chat_history"] = []
                st.success("Chat history cleared")

            # Load and display saved sessions
            session_ids = get_session_ids_for_user(st.session_state.username, db)
            selected_session_id = st.selectbox("Select a chat session", session_ids)
            if selected_session_id:
                selected_session = load_session_from_db(db, selected_session_id)
                for message in selected_session:
                    if message['role'] == 'user':
                        st.markdown(f"**User:** {message['content']}")
                    elif message['role'] == 'assistant':
                        st.markdown(f"**Assistant:** {message['content']}")
                if st.button("Delete Session"):
                    delete_session_from_db(db, selected_session_id)
                    st.success("Chat session deleted")
                    st.experimental_rerun()
            elif selected_page == "Logout":
                # authenticator.logout("Logout", "unrendered")
                st.session_state.logged_in = False
                st.session_state.username = ''
                st.session_state.refresh = False
                st.session_state.has_session_name = False
                st.session_state.messages = []
                st.session_state.session_id = ''
                st.session_state.clear()
                st.rerun()

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