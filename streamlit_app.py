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
                add_anak(nama_anak, usia_anak, jenis_kelamin, berat_badan_anak, tinggi_badan_anak, status, keterangan, waktu_pengambilan_data, st.session_state.username)
                st.success("Data berhasil dikirim ke MongoDB!")

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

            waktu_pengambilan_data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
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
                    st.experimental_rerun()

                if operation == "Update" and st.button("Update", key="update_button"):
                    if cek_anak(nama, user_id):
                        update_anak(nama, umur, jenis_kelamin, berat_badan_anak, tinggi_badan_anak, status, keterangan, waktu_pengambilan_data, user_id)
                        st.success("Data anak berhasil diupdate!")
                        st.experimental_rerun()
                    else:
                        st.error("Data anak tidak ada!")

            elif operation == "Hapus":
                st.write("Hapus data anak:")
                nama = st.text_input("Nama", key="nama_hapus_input", placeholder="Nama anak")
                if st.button("Hapus", key="hapus_button"):
                    if cek_anak(nama, user_id):
                        if delete_anak(nama, user_id):
                            st.success("Data anak berhasil dihapus!")
                            st.experimental_rerun()
                        else:
                            st.error("Terjadi kesalahan saat menghapus data anak!")
                    else:
                        st.error("Data anak tidak ada!")

                
        elif selected_page == "ChatBot":
            from groq import Groq
            import uuid
            from huggingface_hub import InferenceClient
            from openai import OpenAI

            # LLM Client setup--------------------------------------------------------------------------

            # Load the model from the Hugging Face Hub
            repo_id = "meta-llama/Meta-Llama-3-8B"
            hf_client = InferenceClient(repo_id) 

            # Load the Groq API key from the Streamlit secrets
            groq_client = Groq(
                api_key = os.getenv("GROQ_API_KEY"),
            )
            model_from_groq = "llama-3.1-8b-instant"

            # Load the NVIDIA API key from the Streamlit secrets
            nvidia_client = OpenAI(
            base_url = "https://integrate.api.nvidia.com/v1", 
            api_key = os.getenv("OPENAI_API_KEY")
            )
            model_from_nvidia = "meta/llama-3.1-70b-instruct"

            # Initialize session state variables if they don't exist
            if 'session_id' not in st.session_state:
                st.session_state.session_id = ''
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            if 'has_session_name' not in st.session_state:
                st.session_state.has_session_name = False
            if 'refresh' not in st.session_state:
                st.session_state.refresh = False
            if 'session_name' not in st.session_state:
                st.session_state.session_name = ''

            # Set the app title
            st.title("🤖 Chatbot Demo")

            username = st.session_state.username

            # Display session buttons with unique keys
            sidebar_placeholder = st.sidebar.empty()
            content_placeholder = st.empty()
            with sidebar_placeholder.container():
                st.sidebar.title("Chat Sessions")
                
                
                if st.button("Create New Session", key="new_session_button", use_container_width=True):
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.messages = []
                    st.session_state.has_session_name = False
                    st.session_state.session_name = ''

                for idx, sid in enumerate(get_session_ids_for_user(username)):
                    session_name = get_session_name(sid)  # Retrieve session name from database
                    if session_name:
                        if st.sidebar.button(session_name, key=f"button_{sid}", use_container_width=True):
                            st.session_state.session_id = sid
                            st.session_state.messages = load_session_from_db(sid)
                            st.session_state.has_session_name = True
                            st.session_state.session_name = session_name
            
            if st.session_state.messages != []:
                with content_placeholder.container():
                    st.header(f":blue[{st.session_state.session_name}]")
                    if st.button("Delete Session", key="delete_session_button"):
                        delete_session_from_db(st.session_state.session_id)
                        st.session_state.clear()
                        selected_page = "ChatBot"
                        st.session_state.refresh = True

            # Generate a unique session ID if it doesn't exist
            if "session_id" not in st.session_state:
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.has_session_name = False

            # Initialize the messages list if it doesn't exist
            if "messages" not in st.session_state:
                st.session_state.messages = []
                st.session_state.has_session_name = False

            for message in st.session_state.messages:
                avatar = '🤖' if message["role"] == "assistant" else '👨‍💻'
                with st.chat_message(message["role"], avatar=avatar):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Enter your prompt here..."):
                user_message = {"role": "user", "content": prompt}
                st.session_state.messages.append(user_message)

                with st.chat_message("user", avatar='👨‍💻'):
                    st.markdown(prompt)

                save_session_to_db(st.session_state.session_id, username, st.session_state.session_id, st.session_state.messages)

                try:
                    chat_completion = groq_client.chat.completions.create(
                        model=model_from_groq,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "Anda adalah asisten medis yang membantu, hormat, dan jujur."
                                    "Hanya jawab pada hal yang berkaitan dengan kesehatan dan medis."
                                    "Jawab dalam bahasa Indonesia."
                                    "Jawaban Anda tidak boleh mengandung konten yang berbahaya, tidak etis, rasis, seksis, beracun, berbahaya, atau ilegal. "
                                    "Pastikan bahwa respons Anda tidak bias secara sosial dan positif. Jika sebuah pertanyaan tidak masuk akal, atau tidak faktual, jelaskan alasannya daripada menjawab sesuatu yang tidak benar. "
                                    "Jika Anda tidak tahu jawaban atas sebuah pertanyaan, jangan bagikan informasi yang salah."
                                )
                            }
                        ] + [
                            {
                                "role": m["role"],
                                "content": m["content"]
                            } for m in st.session_state.messages
                        ],
                        stream=True
                    )

                    # Use the generator function with st.write_stream
                    with st.chat_message("assistant", avatar="🤖"):
                        chat_responses_generator = generate_chat_responses(chat_completion)
                        full_response = st.write_stream(chat_responses_generator)
                except Exception as e:
                    st.error(e, icon="🚨")

                # Append the full response to session_state.messages
                assistant_message = {"role": "assistant", "content": full_response}
                st.session_state.messages.append(assistant_message)

                if not st.session_state.has_session_name:
                    try:
                        session_name_completion = groq_client.chat.completions.create(
                            model=model_from_groq,
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "Anda adalah asisten yang membantu membuat judul untuk sesi obrolan."
                                        "Judul harus singkat, jelas, dan menggambarkan topik obrolan."
                                        "Jawab dalam bahasa Indonesia."
                                        "Hanya berikan jawaban tidak lebih dari 50 karakter."
                                        "Contoh jawaban yang baik: 'Obrolan tentang kesehatan anak'."
                                    )
                                },
                                {
                                    "role": "user",
                                    "content": f"""
                                    Tolong ringkas judul obrolan ini.

                                    User: {prompt}
                                    Assistant: {full_response}
                                    """
                                }
                            ],
                            stream=True
                        )

                        # Use the generator function with st.write_stream
                        session_name_response = generate_chat_responses(session_name_completion)
                        session_name = st.write_stream(session_name_response)
                        st.session_state.has_session_name = True
                        st.session_state.refresh = True

                    except Exception as e:
                        st.error(e, icon="🚨")

                save_session_to_db(st.session_state.session_id, username, session_name, st.session_state.messages)
            if st.session_state.refresh == True:
                st.session_state.refresh = False
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
            st.experimental_rerun()

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