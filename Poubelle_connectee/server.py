from flask import Flask, jsonify, request
import requests
import cv2
import torch
import torchvision.models as models
import torchvision.transforms as transforms
import numpy as np
import os
import threading

app = Flask(__name__)

ESP32_URL = "http://*.*.*.*" 

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Utilisation de: {device}")

model_lock = threading.Lock()

model = models.resnet18(weights=None)
model.fc = torch.nn.Linear(model.fc.in_features, 6)

class_names = ['carton', 'verre', 'alluminium', 'papier', 'plastique', 'rien']

last_image = None
last_prediction = None

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def load_model():
    try:
        state_dict = torch.load("model.pth", map_location=device)
        new_state_dict = {key.replace("resnet18.", ""): value for key, value in state_dict.items()}
        model.load_state_dict(new_state_dict, strict=False)
        model.to(device)
        model.eval()
        print("Modèle chargé avec succès")
    except Exception as e:
        print(f"Erreur lors du chargement du modèle : {e}")
        raise

def check_for_object(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.mean(gray_frame) <= 240

def predict(frame):
    global last_image, last_prediction
    try:
        if frame.shape[2] == 4:
            frame = frame[:, :, :3]

        last_image = frame.copy()
        image = transform(frame)
        image = image.unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = model(image)
        _, predicted = torch.max(outputs, 1)
        
        last_prediction = predicted.item()
        return last_prediction
    except Exception as e:
        print(f"Erreur dans predict : {e}")
        return -1

def update_model(correct_class_index):
    global model, last_image, last_prediction
    if last_image is None or last_prediction is None:
        return False

    try:
        with model_lock:
            torch.save(model.state_dict(), "model_backup.pth")

            image_tensor = transform(last_image).unsqueeze(0).to(device)
            label = torch.tensor([correct_class_index]).to(device)

            optimizer = torch.optim.SGD(model.parameters(), lr=0.001)
            criterion = torch.nn.CrossEntropyLoss()

            model.train()
            optimizer.zero_grad()
            outputs = model(image_tensor)
            loss = criterion(outputs, label)
            loss.backward()
            optimizer.step()
            model.eval()

            torch.save(model.state_dict(), "model.pth")
            print("Modèle mis à jour avec succès")
            return True

    except Exception as e:
        print(f"Erreur lors de la mise à jour du modèle : {e}")
        if os.path.exists("model_backup.pth"):
            model.load_state_dict(torch.load("model_backup.pth", map_location=device))
        return False

def control_servo(class_name):
    try:
        if class_name == "verre":
            requests.get(f"{ESP32_URL}/servo/right")
        elif class_name == "rien":
            requests.get(f"{ESP32_URL}/servo/center")
        else:
            requests.get(f"{ESP32_URL}/servo/left")
        return True
    except Exception as e:
        print(f"Erreur communication ESP32: {e}")
        return False

@app.route('/')
def home():
    return "Server is running!"

@app.route('/predict', methods=['GET'])
def get_prediction():
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return jsonify({'error': 'Caméra non accessible'}), 500

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return jsonify({'error': 'Échec de la capture d\'image'}), 500

        if not check_for_object(frame):
            return jsonify({'class': 'rien'})

        predicted_class_idx = predict(frame)

        if predicted_class_idx == -1:
            return jsonify({'error': 'Erreur de prédiction'}), 500
        elif 0 <= predicted_class_idx < len(class_names):
            predicted_class = class_names[predicted_class_idx]
            return jsonify({'class': predicted_class})
        else:
            return jsonify({'error': 'Classe inconnue'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['POST'])
def receive_feedback():
    try:
        data = request.json
        is_correct = data.get('is_correct', False)
        corrected_class = data.get('corrected_class')
        
        final_class = class_names[last_prediction] if is_correct else corrected_class

        control_servo(final_class)

        if not is_correct and corrected_class in class_names:
            correct_class_index = class_names.index(corrected_class)
            if not update_model(correct_class_index):
                return jsonify({'error': 'Erreur lors de la mise à jour du modèle'}), 500

        return jsonify({'message': 'Feedback traité avec succès'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Démarrage du serveur...")
    load_model()
    app.run(host='0.0.0.0', port=5000)