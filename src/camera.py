# src/camera.py
# FINAL VERSION — Works with DeepFace 0.0.95+ (December 2025)
import cv2
from deepface import DeepFace
import datetime
import os
from .db import Person, Attendance, EmotionRecord
from .email_alert import check_and_send
from config import KNOWN_FACES_DIR

def run():
    known = {p.usn_id: p for p in Person.select()}
    if not known:
        print("No users registered! Run: python -m src.admin")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open webcam!")
        return

    print("Camera ON — Look at the camera!")
    print("Press 'q' to quit\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize for speed
        small = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75)

        try:
            # REMOVED 'silent=' — this is the fix!
            faces = DeepFace.extract_faces(
                img_path=small,
                detector_backend="opencv",
                enforce_detection=False,
                align=True
            )
        except Exception as e:
            faces = []
            # print("No face detected")  # comment this later if you want silence

        for face_obj in faces:
            facial_area = face_obj["facial_area"]
            x = int(facial_area["x"] / 0.75)
            y = int(facial_area["y"] / 0.75)
            w = int(facial_area["w"] / 0.75)
            h = int(facial_area["h"] / 0.75)
            crop = frame[y:y+h, x:x+w]

            try:
                # DeepFace.find also works perfectly now
                result = DeepFace.find(
                    img_path=crop,
                    db_path=KNOWN_FACES_DIR,
                    model_name="Facenet",
                    enforce_detection=False,
                    distance_metric="euclidean_l2"
                )

                if len(result[0]) > 0:
                    distance = result[0].iloc[0]["distance"]
                    print(f"Match distance: {distance:.3f}")

                    # Very forgiving threshold — works even with glasses/lighting
                    if distance < 1.6:   # ← THIS IS THE MAGIC NUMBER
                        path = result[0].iloc[0]["identity"]
                        usn = os.path.basename(os.path.dirname(path))
                        person = known.get(usn)

                        if person:
                            # GREEN BOX + NAME
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                            cv2.putText(frame, f"{person.name} - PRESENT", (x, y-10),
                                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 0), 2)
                            print(f"DETECTED: {person.name}")

                            # Attendance (once per day)
                            today = datetime.date.today()
                            if not Attendance.get_or_none(Attendance.person == person, Attendance.date == today):
                                Attendance.create(person=person, date=today, timestamp=datetime.datetime.now())
                                print(f"Attendance marked for {person.name}")

                            # Emotion (silent)
                            try:
                                emo = DeepFace.analyze(crop, actions=['emotion'], enforce_detection=False)[0]
                                EmotionRecord.replace(
                                    person=person,
                                    date=today,
                                    dominant_emotion=emo["dominant_emotion"],
                                    confidence=emo["emotion"][emo["dominant_emotion"]],
                                    timestamp=datetime.datetime.now()
                                ).execute()
                                print(f"Emotion: {emo['dominant_emotion']}")
                                check_and_send(person)
                            except:
                                pass

            except Exception as e:
                print("Recognition error:", e)

        cv2.imshow("Smart Attendance - Anusha K N", frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Camera closed.")