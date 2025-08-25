from flask import Flask, render_template, Response, request, jsonify
import cv2
import numpy as np
import os
from tensorflow.keras.models import model_from_json
from tensorflow.keras.preprocessing import image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- AI Model Configurations ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')

try:
    model_json_file = 'emotion_model.json'
    model_weights_file = 'emotion_model.weights.h5'
    with open(model_json_file, "r") as json_file:
        loaded_model_json = json_file.read()
        emotion_model = model_from_json(loaded_model_json)
    emotion_model.load_weights(model_weights_file)
    print("✅ Emotion model loaded successfully.")
except Exception as e:
    print(f"❌ Error loading emotion model: {e}")
    emotion_model = None

try:
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        raise IOError("Unable to load the haarcascade classifier xml file")
    print("✅ Haarcascade loaded successfully.")
except Exception as e:
    print(f"❌ Error loading haarcascade: {e}")
    face_cascade = None
    
emotions = ('angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise')

# **CHANGE 1: Create a global variable to store the last detected emotion**
last_detected_emotion = "neutral"

# --- Video Streaming and Emotion Detection ---

def generate_frames():
    global last_detected_emotion  # Declare that we want to modify the global variable
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("❌ Error: Could not open video stream.")
        return

    while True:
        success, frame = camera.read()
        if not success:
            break
        
        if face_cascade and not face_cascade.empty() and emotion_model:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)
            
            for (x, y, w, h) in faces:
                roi_gray = gray_frame[y:y + h, x:x + w]
                roi_gray = cv2.resize(roi_gray, (48, 48))
                img_pixels = image.img_to_array(roi_gray)
                img_pixels = np.expand_dims(img_pixels, axis=0)
                img_pixels /= 255.0

                predictions = emotion_model.predict(img_pixels, verbose=0)
                max_index = int(np.argmax(predictions))
                predicted_emotion = emotions[max_index]
                
                # **CHANGE 2: Update the global variable with the latest emotion**
                last_detected_emotion = predicted_emotion

                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, predicted_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        try:
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            break
            
    camera.release()

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/chat', methods=['POST'])
def chat():
    global last_detected_emotion # Access the global variable
    try:
        data = request.json
        user_message = data.get("message", "")
        gad7_score = data.get("gad7Score", 0)
        gad7_level = data.get("gad7Level", "not assessed")

        # **CHANGE 3: Use the global emotion variable in the prompt**
        prompt = f"""
        You are an empathetic and supportive mental health AI assistant named 'Aura'.
        Your user has provided the following context:
        - The user's most recently detected facial expression is '{last_detected_emotion}'.
        - Their GAD-7 anxiety score is {gad7_score}, indicating a level of '{gad7_level}'.
        - The user's message is: "{user_message}"

        Your task is to respond in a warm and helpful manner.
        1. Weave both the detected emotion ('{last_detected_emotion}') and the anxiety level ('{gad7_level}') into your response naturally. For example, "I can see you're looking {last_detected_emotion}, and it's completely understandable to feel that way when dealing with {gad7_level} anxiety."
        2. If the detected emotion seems to contradict the user's message (e.g., they look 'sad' but say 'I'm fine'), gently and kindly acknowledge this. For example, "You say you're doing fine, but it seems there might be some sadness present. It's okay to feel that way."
        3. Offer a simple, actionable coping strategy relevant to both the emotion and anxiety level.
        4. Keep your response concise and supportive.
        """
        
        response = gemini_model.generate_content(prompt)
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({"reply": f"Sorry, I encountered an error: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)