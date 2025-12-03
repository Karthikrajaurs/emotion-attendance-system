# src/email_alert.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .db import Person, EmotionRecord, AlertLog
from config import SMTP_EMAIL, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
from datetime import datetime, timedelta

def send_alert(person, reason, history):
    if AlertLog.get_or_none(person=person, trigger_date=datetime.now().date()):
        return  # Already sent today

    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = person.authorizer_email
    msg['Subject'] = f"Wellbeing Alert: {person.name}"

    body = f"""
ALERT: Possible emotional concern detected

Name: {person.name} ({person.usn_id})
Reason: {reason}

Recent emotions (last 14 days):
"""
    for h in history[-10:]:
        body += f"{h.date}: {h.dominant_emotion} ({h.confidence:.1f}%)\n"

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, person.authorizer_email, msg.as_string())
        server.quit()
        print(f"Email alert sent for {person.name}")
    except Exception as e:
        print("Email failed:", e)

    AlertLog.create(person=person, trigger_date=datetime.now().date(), reason=reason)

def check_and_send(person):
    emotions = EmotionRecord.select().where(EmotionRecord.person == person).order_by(EmotionRecord.date.desc()).limit(14)
    sad_fear = [e for e in emotions if e.dominant_emotion in ['sad', 'fear']]
    dates = {e.date for e in emotions}

    if len(dates) >= 7 and len(sad_fear) >= 7:
        send_alert(person, f"{len(sad_fear)} sad/fear days in last 14", list(emotions))