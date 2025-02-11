import cv2
import os
import datetime
import face_recognition
import numpy as np
import csv

def capture_data(name, save_dir):
    video = cv2.VideoCapture(0)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    faces_data = []

    while True:
        ret, frame = video.read()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces using face_recognition
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # Draw rectangle for each detected face
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Display live feed with face count
        cv2.putText(frame, str(len(faces_data)), (50,50), cv2.FONT_HERSHEY_COMPLEX, 1, (50,50,255), 1)
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
    
    video.release()
    cv2.destroyAllWindows()

def face_embeddings(save_dir, embeddings_dir="embeddings", embeddings_filename="embeddings.txt"):
    if not os.path.exists(embeddings_dir):
        os.makedirs(embeddings_dir)

    # Load images from the dataset directory
    image_paths = [os.path.join(save_dir, f) for f in os.listdir(save_dir)]
    embeddings = []

    for image_path in image_paths:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Failed to load image at {image_path}")
            continue
        
        # Convert the image to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect faces in the image
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if len(face_encodings) == 1:  # Only append if exactly one face is found
            embeddings.append(face_encodings[0])
        else:
            print(f"Warning: {image_path} has {len(face_encodings)} faces (skipped).")

    if embeddings:
        embeddings_filepath = os.path.join(embeddings_dir, embeddings_filename)

        # If the file doesn't exist, create it and write embeddings
        if not os.path.exists(embeddings_filepath):
            np.savetxt(embeddings_filepath, embeddings)
            print(f"Embeddings saved to {embeddings_filepath}")
        else:
            # If file exists, append embeddings to it
            existing_embeddings = np.loadtxt(embeddings_filepath)
            all_embeddings = np.vstack((existing_embeddings, embeddings))
            np.savetxt(embeddings_filepath, all_embeddings)
            print(f"Embeddings updated in {embeddings_filepath}")
    else:
        print("No valid embeddings were generated.")

def detect_faces(embeddings_dir="embeddings", embeddings_filename="embeddings.txt", attendance_log="attendance_log.csv"):
    # Load saved embeddings
    embeddings = np.loadtxt(os.path.join(embeddings_dir, embeddings_filename))
    video = cv2.VideoCapture(0)
    known_face_encodings = embeddings
    # known_face_names = os.listdir(r'C:\Users\DHAIRYA\Face_recognition\data\captured_data')  # Assume each file corresponds to a person
    known_face_names = [f.split("_")[0] for f in os.listdir(r'C:\Users\DHAIRYA\Face_recognition\data\captured_data')]

    # Create an attendance log if not exists
    if not os.path.exists(attendance_log):
        with open(attendance_log, 'w', newline='') as file:
            # file.write("Name,Time\n")
            writer = csv.writer(file)
            writer.writerow(["Name", "Time"])
    
    # Track the people who have already had their attendance marked during this session
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
                name = known_face_names[first_match_index]
                
                # Mark attendance only if this person hasn't been marked already
                if name not in attended_names:
                    with open(attendance_log, 'a', newline='') as file:
                        writer = csv.writer(file)
                        # file.write(f"{name},{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        writer.writerow([name, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                    attended_names.add(name)  # Add name to the attended set to prevent re-logging

            # Draw rectangle around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Display the name of the recognized person above the rectangle
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Display the frame
        cv2.imshow("Video Feed", frame)

        # Quit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video.release()
    cv2.destroyAllWindows()

# Main execution
name = input("Enter your name: ")
save_dir = r"C:\Users\DHAIRYA\Face_recognition\data\captured_data"

capture_data(name, save_dir)
face_embeddings(save_dir)
detect_faces()
