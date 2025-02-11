import os
import datetime
import cv2
import numpy as np
import face_recognition
import csv
from flask import Flask, render_template, Response, request, redirect, url_for, jsonify
import threading

app = Flask(__name__)

# Directories and paths
save_dir = r"C:\Users\DHAIRYA\Face_recognition\data\captured_data"
EMBEDDINGS_DIR = r"C:\Users\DHAIRYA\Face_recognition\embeddings"
ATTENDANCE_LOG = r"C:\Users\DHAIRYA\Face_recognition\attendance_log.csv"

# Video capture object
video_capture = cv2.VideoCapture(0)

# Initialize threading lock for the camera
lock = threading.Lock()

def capture_data(name):
    # Create the save directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    faces_data = []

    while True:
        ret, frame = video_capture.read()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces using face_recognition
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # Draw rectangle for each detected face
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Display live feed with face count
        # Display live feed with face count
        cv2.putText(frame, str(len(faces_data)), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 255), 1)
        cv2.imshow("Frame:", frame)

        k = cv2.waitKey(1)
        if k == ord("q"):  # Quit on 'q'
            break
        if k == ord("s"):  # Save image on 's'
            if len(face_locations) > 0:
                image_path = os.path.join(save_dir, f'{name}_{len(faces_data)+1}.jpg')
                cv2.imwrite(image_path, frame)
                faces_data.append(frame)
            else:
                print("No faces detected in the frame.")

    # video_capture.release()
    # cv2.destroyAllWindows()
    stop_video_capture()

def face_embeddings():
    if not os.path.exists(EMBEDDINGS_DIR):
        os.makedirs(EMBEDDINGS_DIR)

    # Load images from the dataset directory
    image_paths = [os.path.join(save_dir, f) for f in os.listdir(save_dir)]
    embeddings = []

    for image_path in image_paths:
        image = cv2.imread(image_path)
        if image is None:
            continue
        
        # Convert the image to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect faces in the image
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if len(face_encodings) == 1:  # Only append if exactly one face is found
            embeddings.append(face_encodings[0])

    embeddings_filepath = os.path.join(EMBEDDINGS_DIR, "embeddings.txt")
    if embeddings:
        np.savetxt(embeddings_filepath, embeddings)
        print(f"Embeddings saved to {embeddings_filepath}")
    else:
        print("No valid embeddings were generated.")

def detect_faces():
    # Load saved embeddings
    embeddings = np.loadtxt(os.path.join(EMBEDDINGS_DIR, "embeddings.txt"))
    video = cv2.VideoCapture(0)
    known_face_encodings = embeddings
    known_face_names = [f.split("_")[0] for f in os.listdir(save_dir)]

    if not os.path.exists(ATTENDANCE_LOG):
        with open(ATTENDANCE_LOG, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Time"])
    
    attended_names = set()

    while True:
        ret, frame = video.read()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            
            if True in matches:
                first_match_index = matches.index(True)
                # if first_match_index < len(known_face_names):
                name = known_face_names[first_match_index]
                # else:
                #     print(f"Error: No matching name found for this face.")
                #     continue
                
                if name not in attended_names:
                    print(f"Marking attendance for {name}")
                    with open(ATTENDANCE_LOG, 'a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([name, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                    attended_names.add(name)

            # Draw rectangle around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Display the name of the recognized person
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Video Feed", frame)

        # Quit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    stop_video_capture()
    # video.release()
    # cv2.destroyAllWindows()

video_capture = None
is_video_open = False

# Function to start the webcam
def start_video_capture():
    global video_capture, is_video_open
    if not is_video_open:
        video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        is_video_open = True

# Function to release the webcam
def stop_video_capture():
    global video_capture, is_video_open
    if is_video_open:
        video_capture.release()
        is_video_open = False
        cv2.destroyAllWindows()

@app.route('/video_feed')
def video_feed():
    print("Video_feed")
    def generate():
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            # Encode the frame in JPEG format
            _, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()

            # Yield the frame as a multipart response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route for Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    start_video_capture()
    if request.method == 'POST':
        name = request.form['name']
        if name:
            capture_data(name)
            face_embeddings()
            return redirect(url_for('register_success'))
    return render_template('register.html')

# Success page after registering
@app.route('/register_success')
def register_success():
    return render_template('register_success.html')

# Route for Mark Attendance Page
@app.route('/mark_attendance')
def mark_attendance():
    start_video_capture()
    def run_face_detection():
        detect_faces()

    # Start face detection in a separate thread
    threading.Thread(target=run_face_detection, daemon=True).start()

    return render_template('mark_attendance.html', video_feed_url=url_for('video_feed'))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
