import streamlit as st
from model import query_policy
import io
import csv
from datetime import datetime
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="📘 Policy Q&A Bot", layout="centered")

# ---------- EMAIL FUNC ----------
def send_email(recipient, subject, body):
    EMAIL = "pratikshasingh923@gmail.com"  
    PASSWORD = "dsfi lhlj qxlk vsmc" 

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ---------- SESSION ----------
if "name" not in st.session_state:
    st.session_state.name = ""
if "email" not in st.session_state:
    st.session_state.email = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- LOGIN ----------
if not st.session_state.name or not st.session_state.email:
    st.title("🔐 Welcome to Policy Q&A Bot")
    st.markdown("Please enter your details to continue:")

    with st.form("login_form"):
        name = st.text_input("👤 Your Name")
        email = st.text_input("📧 Your Email")
        submitted = st.form_submit_button("Start Chatting")

        if submitted:
            if name and email:
                st.session_state.name = name
                st.session_state.email = email

                #Log user info
                with open("users_log.csv", "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([name, email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

                st.success(f"Welcome, {name}!")
                st.rerun()
            else:
                st.warning("Please enter both name and email.")

# ---------- MAIN APP ----------
else:
    #Sidebar
    with st.sidebar:
        st.markdown(f"👤 Logged in as: `{st.session_state.name}`")
        if st.button("🚪 Logout"):
            st.session_state.name = ""
            st.session_state.email = ""
            st.session_state.chat_history = []
            st.rerun()

    # personalized name
    st.title(f"📘 Hello, {st.session_state.name}!")
    st.markdown("Ask any question based on the Environment Policy document.")

    with st.form("chat_form"):
        user_input = st.text_input("🔎 Enter your query:")
        submitted = st.form_submit_button("Send")
    if submitted and user_input:
        with st.spinner("Thinking..."):
            response = query_policy(user_input)


            personalized_response = f"{response}\n\n— Answered for {st.session_state.name}"

        # Store in chat history
            st.session_state.chat_history.append(("You", user_input))
            st.session_state.chat_history.append(("Bot", personalized_response))

            st.success(personalized_response)


    # ---------- CHAT HISTORY ----------
    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### 🧠 Your Chat This Session")
        for speaker, message in st.session_state.chat_history:
            st.markdown(f"**{speaker}:** {message}")

        # Prepare chat text
        chat_text = ""
        for speaker, message in st.session_state.chat_history:
            chat_text += f"{speaker}: {message}\n\n"

        # Download
        st.download_button(
            label="📥 Download This Chat",
            data=chat_text,
            file_name=f"{st.session_state.name}_policy_chat.txt",
            mime="text/plain"
        )

        # Email button
        if st.button("📧 Email Me This Chat"):
            subject = f"Your Policy Chat History - {datetime.now().strftime('%Y-%m-%d')}"
            body = f"Hi {st.session_state.name},\n\nHere is your chat with the Policy Q&A Bot:\n\n{chat_text}"
            success = send_email(st.session_state.email, subject, body)
            if success:
                st.success("✅ Chat history emailed successfully!")
            else:
                st.error("❌ Failed to send email. Please check credentials.")
