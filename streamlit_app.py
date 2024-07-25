import streamlit as st
import os
import pandas as pd
import requests
import streamlit_authenticator as stauth
from streamlit_modal import Modal
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import Generator
from PIL import Image
from utils.db import get_user, add_user, fetch_users, get_session_ids_for_user, save_session_to_db, load_session_from_db, get_session_name

# Load Environment Variables------------------------------------------------------------------------

load_dotenv()



# Connect to MongoDB Atlas--------------------------------------------------------------------------

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable not set")

client = MongoClient(mongo_uri)
db = client["sic5_belajar"]



# Authentication-----------------------------------------------------------------------------------

cookie_hash_key = os.getenv("COOKIE_HASH_KEY")
credentials = fetch_users()
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="GrowMyBaby_Cookie",
    cookie_key=cookie_hash_key,
    cookie_expiry_days=1,
)



# Helper Functions-----------------------------------------------------------------------------------

def login():
    fields = {
        'Form name': 'Login',
        'Username': 'Username',
        'Password': 'Password',
        'Login': 'Login'
    }

    # Perform login
    name, authentication_status, username = authenticator.login(
        location='main',
        max_concurrent_users=None,
        max_login_attempts=None,
        fields=fields,
        clear_on_submit=False
    )

    if authentication_status:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.experimental_rerun()
    elif authentication_status is False:
        st.error('Username/password is incorrect')
    elif authentication_status is None:
        st.warning('Please enter your username and password')

def signup():
    st.title("Sign Up")
    username = st.text_input("Username").lower()
    password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        if add_user(username, password):
            st.success("Account created successfully! Please go to the Login page to sign in.")
        else:
            st.error("Username already exists. Please choose a different username.")

def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
    """Yield chat response content from the Groq API response."""
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content



# The Main App-----------------------------------------------------------------------------------
icon_png = Image.open("assets/images/GrowMyBaby Icon.png")
logo_png = Image.open("assets/images/GrowMyBaby Logo.png")
st.logo(logo_png, icon_image=icon_png)


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ''

if st.session_state.logged_in:
    sidebar_placeholder = st.sidebar.empty()
    content_placeholder = st.empty()
    with sidebar_placeholder.container():
        st.sidebar.title(f"Welcome, {st.session_state.username}")
        selected_page = st.sidebar.radio("Navigation", ["Home", "ChatBot", "Logout"])

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

        jenis_kelamin = st.radio("Jenis kelamin anak:", ["Laki-laki", "Perempuan"], key='jenis_kelamin_radio')
        usia_anak = st.number_input("Usia anak (bulan):", min_value=6, max_value=60, step=6, key='usia_anak_input')

        response = requests.get('http://127.0.0.1:5000/data')
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

        if st.button("Post to MongoDB", key='post_to_mongodb_button'):
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

        # Set the app title
        st.title("🤖 Chatbot Demo")

        username = st.session_state.username

        # Display session buttons with unique keys
        sidebar_placeholder = st.sidebar.empty()
        with sidebar_placeholder.container():
            st.sidebar.title("Chat Sessions")
            
            if st.button("Create New Session", key="new_session_button", use_container_width=True):
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.session_state.has_session_name = False

            for idx, sid in enumerate(get_session_ids_for_user(username)):
                session_name = get_session_name(sid)  # Retrieve session name from database
                if session_name:
                    if st.sidebar.button(session_name, key=f"button_{sid}", use_container_width=True):
                        st.session_state.session_id = sid
                        st.session_state.messages = load_session_from_db(sid)
                        st.session_state.has_session_name = True

        st.session_state.refresh = False

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
                    model = model_from_groq,
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
                        model = model_from_groq,
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
            if st.session_state.refresh:
                st.experimental_rerun()
    elif selected_page == "Logout":
        authenticator.logout("Logout", "unrendered")
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.session_state.refresh = False
        st.session_state.has_session_name = False
        st.session_state.messages = []
        st.session_state.session_id = ''
        st.rerun()

else:
    st.sidebar.title("Navigation")
    selected_page = st.sidebar.radio("Navigation", ["Login", "Sign Up"], key='nav_radio')
    if selected_page == "Login":
        login()
    elif selected_page == "Sign Up":
        signup()