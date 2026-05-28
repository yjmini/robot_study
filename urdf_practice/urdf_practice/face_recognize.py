import cv2

# 1. Load the Haar Cascade Classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# 2. Capture video from the webcam
cap = cv2.VideoCapture(4)

if not cap.isOpened():
    print("Cannot open the camera.")
    exit()

print("Real-time face detection is running...")

while True:
    # 3. Read the current frame from the webcam
    ret, frame = cap.read()
    if not ret:
        print("Cannot read frame.")
        break

    # 4. Convert frame to grayscale for better face detection
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # 5. Draw a rectangle around detected faces and add 'Face Detected' text
    for (x, y, w, h) in faces:
        # Draw rectangle around the face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Add text 'Face Detected' above the face
        cv2.putText(frame, 'Face Detected', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    # 6. Display the number of detected faces on the frame
    num_faces = len(faces)
    cv2.putText(frame, f'Faces detected: {num_faces}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    # 7. Show the processed frame
    cv2.imshow('Face Detection', frame)

    # 8. Save the frame when 's' key is pressed and at least one face is detected
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s') and num_faces > 0:
        cv2.imwrite('detected_face.png', frame)
        print("Frame with detected face saved as 'detected_face.png'.")

    # 9. Exit the loop when 'q' key is pressed
    if key == ord('q'):
        break

# 10. Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
