# src/admin.py
from .db import Person
import os
import shutil
from config import KNOWN_FACES_DIR

def register():
    print("\n=== Register New Person ===")
    usn = input("USN/ID: ").strip()
    if Person.get_or_none(Person.usn_id == usn):
        print("Already exists!")
        return

    name = input("Name: ").strip()
    section = input("Class/Section (optional): ").strip() or None
    email = input("Authorizer Email: ").strip()
    photo_path = input("Path to photo: ").strip()

    if not os.path.exists(photo_path):
        print("Photo not found!")
        return

    target_dir = os.path.join(KNOWN_FACES_DIR, usn)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "face.jpg")
    shutil.copy(photo_path, target_path)

    Person.create(
        usn_id=usn, name=name, class_section=section,
        authorizer_email=email, photo_path=target_path
    )
    print(f"Registered {name} ({usn})")

if __name__ == "__main__":
    register()