import speech_recognition as sr
import pywhatkit
import pytz
from datetime import datetime
import sqlite3
import requests
import tkinter as tk
from tkinter import messagebox
import cv2

# Set up speech recognition
r = sr.Recognizer()

# Set up microphone
mic = sr.Microphone()

# Set up emergency numbers
emergency_number = "+91"#enter emergency number
guardian_numbers = ["+91"]#enter guardians number

# Set up database connection
conn = sqlite3.connect("cesa_database.db")
cursor = conn.cursor()

# Create table with the correct schema
cursor.execute("""
     CREATE TABLE IF NOT EXISTS cesarecord_db (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        location TEXT,
        latitude REAL,
        longitude REAL,
        audio BLOB,
        video BLOB
    )
""")

def record_audio():
    """
    Record audio from the microphone for a limited duration.
    """
    with mic as source:
        print("Say an emergency phrase to activate emergency response...")
        audio = r.listen(source, phrase_time_limit=5)
        print("Recording...")
        try:
            text = r.recognize_google(audio, language="en-IN")
            emergency_phrases = ["help me", "help help", "kapadandi kapadandi", "kapadi kapadi", "bachao bachao"]# here used 4 languages
            if text.lower() in emergency_phrases:
                print("Emergency response activated. Recording audio...")
                audio_data = []
                start_time = datetime.now()
                
                while (datetime.now() - start_time).seconds < 10:  # Limit recording to 10 seconds
                    audio_chunk = r.record(source, duration=10)
                    audio_data.append(audio_chunk.get_wav_data())
                    print("Recording audio...")
                
                return b"".join(audio_data)
            else:
                print("Invalid command. Try again.")
                return None
        except sr.UnknownValueError:
            print("Sorry, I didn't understand. Try again.")
            return None

def record_video(filename):
    """
    Record video from the webcam for a limited duration.
    """
    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

    start_time = datetime.now()
    while (datetime.now() - start_time).seconds < 10:  # Limit recording to 10 seconds
        ret, frame = cap.read()
        if ret:
            out.write(frame)
            cv2.imshow('Recording Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # Return the filename of the recorded video
    return filename

def read_video_as_blob(filename):
    """
    Read the video file and return it as a binary blob.
    """
    with open(filename, 'rb') as file:
        video_blob = file.read()
    return video_blob

def send_sms(number, message):
    """
    Send an SMS using pywhatkit.
    """
    pywhatkit.sendwhatmsg_instantly(number, message, 15, tab_close=True)

def sos_response():
    """
    Main SOS response function.
    """
    audio = record_audio()
    if audio:
        # Set fixed location data
        latitude = 16.252392
        longitude = 77.362317
        location = "7926+XW4, Raichur, Karnataka 584135, India"
        
        # Send SMS to emergency number and guardians
        message = f"Hey there..Please help me! I am in trouble! I need your helppp!! Current location: {location} (Lat: {latitude}, Long: {longitude})"
        send_sms(emergency_number, message)
        for number in guardian_numbers:
            send_sms(number, message)
        
        # Record video
        video_filename = f"sos_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
        record_video(video_filename)
        
        # Read video as BLOB
        video_blob = read_video_as_blob(video_filename)
        
        timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO cesarecord_db (timestamp, location, latitude, longitude, audio, video) VALUES (?, ?, ?, ?, ?, ?)",
                       (timestamp, location, latitude, longitude, audio, video_filename))
        conn.commit()
        
        messagebox.showinfo("Success", "Emergency alert sent successfully!")

def start_sos():
    """
    Start the SOS process when the button is pressed.
    """
    sos_response()

# Set up the GUI
root = tk.Tk()
root.title("CESA Alert System")

frame = tk.Frame(root)
frame.pack(pady=20)

sos_button = tk.Button(frame, text="Activate CESA", command=start_sos, width=20, height=2)
sos_button.pack()

root.mainloop()

# Close database connection
conn.close()
