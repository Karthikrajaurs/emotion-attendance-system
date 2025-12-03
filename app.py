# FINAL FIXED VERSION - NO ERRORS + ADMIN ALERT PAGE ADDED
import streamlit as st
import cv2
import numpy as np
from deepface import DeepFace
import os
import shutil
from datetime import datetime, timedelta
from src.db import Person, Attendance, EmotionRecord
from config import KNOWN_FACES_DIR
import pandas as pd

os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

# ====================== LOGIN ======================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.camera_on = False
    st.session_state.alerts = []  # store alerts

if not st.session_state.logged_in:
    st.set_page_config(page_title="Login", layout="centered")
    st.markdown("<style>.stApp {background: linear-gradient(135deg, #667eea, #764ba2); color: white;}</style>", unsafe_allow_html=True)
    st.title("Smart Attendance System")
    st.markdown("### Faculty Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("LOGIN", type="primary"):
        if username == "admin" and password == "attendance123":
            st.session_state.logged_in = True
            st.success("Login Successful!")
            st.rerun()
        else:
            st.error("Wrong credentials")
    st.info("Username: **admin** | Password: **attendance123**")
    st.stop()

# ====================== MAIN APP ======================
st.set_page_config(page_title="Smart Attendance Pro", layout="wide")
st.markdown("""
<style>
    .stApp {background: linear-gradient(135deg, #e0f7fa, #fff3e0); color: #2d3436;}
    h1, h2 {color: #2d3436 !important; text-align: center;}
    .stButton>button {background: #74b9ff; color: white; padding: 14px; border-radius: 15px; font-weight: bold;}
    .happy {background: #dff9fb; color: #00d2d3; padding: 8px; border-radius: 10px; font-weight: bold;}
    .sad {background: #f8b4b4; color: #e74c3c; padding: 8px; border-radius: 10px; font-weight: bold;}
    .angry {background: #fab1a0; color: #c23616; padding: 8px; border-radius: 10px; font-weight: bold;}
    .neutral {background: #dfe4ea; color: #2f3542; padding: 8px; border-radius: 10px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.markdown("# Smart Attendance + Emotion Monitoring System")

with st.sidebar:
    st.markdown("### Menu")
    st.write("Logged in as **admin**")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.camera_on = False
        st.rerun()

# ALERT STORAGE FUNCTION
def check_emotion_alert(person):
    recent = EmotionRecord.select().where(EmotionRecord.person == person).order_by(EmotionRecord.timestamp.desc()).limit(3)
    if recent.count() >= 3:
        emotions = [r.dominant_emotion for r in recent]
        if all(e in ["sad", "neutral"] for e in emotions):
            msg = f"URGENT ALERT: {person.name} ({person.usn_id}) has been Sad/Neutral 3 times in a row."
            st.session_state["alerts"].append(msg)

# 1. REGISTER
with st.expander("Register New Student", expanded=False):
    st.markdown(f"**Total Registered Students: {Person.select().count()}**")
    with st.form("reg_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            usn = st.text_input("USN", placeholder="4AL22CS014")
            name = st.text_input("Full Name", placeholder="Anusha K N")
        with c2:
            section = st.text_input("Section", "A")
            email = st.text_input("Email (Optional)", "")
        photo = st.file_uploader("Upload Face Photo", type=["jpg","jpeg","png"])
        if st.form_submit_button("REGISTER"):
            if not usn or not name or not photo:
                st.error("Required fields missing!")
            elif Person.get_or_none(Person.usn_id == usn.upper()):
                st.error("USN already exists!")
            else:
                folder = os.path.join(KNOWN_FACES_DIR, usn.upper())
                os.makedirs(folder, exist_ok=True)
                with open(os.path.join(folder, "face.jpg"), "wb") as f:
                    f.write(photo.getbuffer())
                Person.create(usn_id=usn.upper(), name=name.title(), class_section=section, authorizer_email=email)
                st.success(f"{name.title()} registered!")
                st.balloons()

# 2. TAKE ATTENDANCE
with st.expander("Take Attendance", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Camera", type="primary"):
            st.session_state.camera_on = True
            st.rerun()
    with col2:
        if st.button("Stop Camera", type="secondary"):
            st.session_state.camera_on = False
            st.rerun()

    if st.session_state.camera_on:
        picture = st.camera_input("Camera ON - Click to Take Photo", key="cam")
        if picture:
            with st.spinner("Analyzing..."):
                img_data = picture.getvalue()
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                try:
                    faces = DeepFace.extract_faces(rgb, detector_backend="opencv", enforce_detection=False, align=True)
                    if faces:
                        face = (faces[0]["face"] * 255).astype(np.uint8)
                        cv2.imwrite("temp.jpg", cv2.cvtColor(face, cv2.COLOR_RGB2BGR))
                        result = DeepFace.find("temp.jpg", db_path=KNOWN_FACES_DIR, model_name="Facenet", enforce_detection=False, silent=True)

                        if len(result[0]) > 0 and result[0].iloc[0]["distance"] < 1.6:
                            usn = os.path.basename(os.path.dirname(result[0].iloc[0]["identity"]))
                            person = Person.get(Person.usn_id == usn)
                            today = datetime.now().date()

                            if not Attendance.get_or_none(Attendance.person == person, Attendance.date == today):
                                Attendance.create(person=person, date=today, timestamp=datetime.now())

                            emo = DeepFace.analyze("temp.jpg", actions=["emotion"], enforce_detection=False, silent=True)[0]
                            EmotionRecord.create(person=person, date=today, dominant_emotion=emo["dominant_emotion"],
                                                 confidence=emo["emotion"][emo["dominant_emotion"]], timestamp=datetime.now())

                            st.success(f"{person.name} PRESENT! Emotion: {emo['dominant_emotion'].title()}")
                            st.image(picture, width=400)

                            check_emotion_alert(person)  # silently stored, no popup
                        else:
                            st.warning("Face not recognized")
                    else:
                        st.error("No face detected")
                except:
                    st.error("Error")
    else:
        st.info("Camera is OFF")

# 3. MANAGE
with st.expander("Manage Students", expanded=False):
    for p in Person.select():
        c1, c2, c3, c4 = st.columns([3,2,2,1])
        c1.write(f"**{p.name}**")
        c2.write(p.usn_id)
        c3.write(p.class_section or "-")
        with c4:
            if st.button("Delete", key=p.id):
                shutil.rmtree(os.path.join(KNOWN_FACES_DIR, p.usn_id), ignore_errors=True)
                p.delete_instance(recursive=True)
                st.success("Deleted!")
                st.rerun()

# 4. REPORT
with st.expander("View Report", expanded=False):
    start = st.date_input("From", datetime.now() - timedelta(days=30))
    end = st.date_input("To", datetime.now())
    if start <= end:
        dates = [start + timedelta(i) for i in range((end-start).days + 1)]
        data = []
        for p in Person.select():
            present = sum(1 for d in dates if Attendance.get_or_none(Attendance.person == p, Attendance.date == d))
            total = len(dates)
            percent = round(present/total*100, 1) if total > 0 else 0
            emotions = [e.dominant_emotion for e in EmotionRecord.select().where((EmotionRecord.person == p) & (EmotionRecord.date.between(start, end)))]
            count = pd.Series(emotions).value_counts()
            data.append({
                "Name": p.name, "USN": p.usn_id,
                "Present": present, "Absent": total-present,
                "%": f"{percent}%",
                "Happy": f"<span class='happy'>Happy {count.get('happy',0)}</span>",
                "Sad": f"<span class='sad'>Sad {count.get('sad',0)}</span>",
                "Angry": f"<span class='angry'>Angry {count.get('angry',0)}</span>",
                "Neutral": f"<span class='neutral'>Neutral {count.get('neutral',0)}</span>",
            })
        df = pd.DataFrame(data)
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# 5. ADMIN ALERT PAGE
with st.expander("Admin Alerts", expanded=False):
    st.subheader("Emotion Alerts")
    if len(st.session_state["alerts"]) > 0:
        for alert in st.session_state["alerts"]:
            st.error(alert)
    else:
        st.info("No Alerts Yet")
