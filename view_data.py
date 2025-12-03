# view_data.py - Run this anytime to see your data!
from src.db import Person, Attendance, EmotionRecord
from datetime import datetime

print("\nREGISTERED STUDENTS")
print("-" * 70)
for p in Person.select():
    print(f"{p.usn_id} → {p.name} ({p.class_section or 'No section'})")

print("\nTODAY'S ATTENDANCE")
print("-" * 70)
today = datetime.now().date()
att_today = Attendance.select().where(Attendance.date == today)
if att_today:
    for a in att_today:
        time = a.timestamp.strftime("%I:%M:%S %p")
        print(f"PRESENT → {a.person.name} at {time}")
else:
    print("No one marked present today yet")

print("\nLATEST 10 EMOTION RECORDS")
print("-" * 70)
for e in EmotionRecord.select().order_by(EmotionRecord.id.desc()).limit(10):
    emo = e.dominant_emotion.upper()
    time = e.timestamp.strftime("%I:%M:%S %p")
    print(f"{e.person.name} → {emo} ({e.confidence:.1f}%) {time}")

print("\nData shown successfully!\n")