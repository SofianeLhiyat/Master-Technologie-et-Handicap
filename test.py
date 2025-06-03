import cv2 as cv
import mediapipe as mp
import numpy as np
import time
import requests
from gtts import gTTS
import threading
from datetime import datetime
from collections import deque
from sklearn.ensemble import IsolationForest
import os
from flask import Flask, send_file, request, jsonify
import multiprocessing
import logging
import pygame
import sys
from pydub import AudioSegment
import tensorflow as tf
from keras.models import load_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/toto/detection_chute.log')  
    ]
)
logger = logging.getLogger(__name__)

CAMERA_RESOLUTION = (640, 480)  
CAMERA_FPS = 15 
ENABLE_GPU = True

FALLING_CONFIDENCE_MULTIPLIER = 1.0

def set_falling_multiplier(factor: float):
    global FALLING_CONFIDENCE_MULTIPLIER
    FALLING_CONFIDENCE_MULTIPLIER = factor
    logger.info(f"Multiplicateur pour 'falling' mis à jour: {FALLING_CONFIDENCE_MULTIPLIER}")

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running"}), 200

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/tapis_detection', methods=['GET'])
def tapis_detection():
    try:
        set_falling_multiplier(1.2)
        logger.info("Multiplicateur de détection de chute augmenté à 1.2 (tapis détecté)")
        return jsonify({"status": "confirmed", "multiplier": 1.2}), 200
    except Exception as e:
        logger.error(f"Erreur lors de l'ajustement du multiplicateur: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset_history', methods=['POST'])
def reset_history():
    try:
        return jsonify({"status": "ok", "new_audio": True}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_audio')
def get_audio():
    try:
        if os.path.exists('vocal_test.wav'):
            logger.info("Envoi du fichier audio à l'application Android")
            file_size = os.path.getsize('vocal_test.wav')
            logger.info(f"Taille du fichier audio: {file_size} octets")
            
            if file_size == 0:
                logger.error("Le fichier audio est vide")
                return "Fichier audio vide", 500
                
            return send_file(
                'vocal_test.wav', 
                mimetype='audio/wav',
                download_name='vocal_test.wav',
                as_attachment=True
            )
        else:
            logger.warning("Fichier audio non trouvé")
            return "Fichier audio non trouvé", 404
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du fichier audio: {e}")
        return str(e), 500
    
@app.route('/alert_available', methods=['GET'])
def alert_available():
    try:
        timestamp = request.args.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        reason = request.args.get('reason', 'chute')
        
        logger.info(f"Nouvelle alerte disponible : {reason} à {timestamp}")
        
        
        return jsonify({"status": "received", "timestamp": timestamp}), 200
    except Exception as e:
        logger.error(f"Erreur lors de la notification d'alerte : {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/notify_listened', methods=['POST'])
def notify_listened():
    try:
        global detecteur_global
        
        logger.info("Notification reçue: l'aidant a pris en compte la chute")
        
        message = "Votre aidant a bien pu prendre en compte votre chute"
        tts = gTTS(text=message, lang='fr')
        tts.save("temp_notification.mp3")

        audio = AudioSegment.from_file("temp_notification.mp3", format="mp3")
        audio = audio.set_frame_rate(44100)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)
        
        audio.export(
            "notification.wav",
            format="wav",
            parameters=[
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "1"
            ]
        )

        if os.path.exists("temp_notification.mp3"):
            os.remove("temp_notification.mp3")

        thread = threading.Thread(target=audio_player.play_audio, args=("notification.wav",))
        thread.start()
        
        logger.info("Message de confirmation envoyé - système toujours en pause en attente d'action manuelle")
        
        return "Notification envoyée - système en attente de réinitialisation manuelle", 200

    except Exception as e:
        error_msg = f"Erreur lors de la notification: {str(e)}"
        logger.error(error_msg)
        return error_msg, 500

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        if 'audio' not in request.files:
            return "Aucun fichier audio reçu", 400
        
        file = request.files['audio']
        temp_filename = 'temp_received'
        filename = 'aidant_message.wav'
        
        original_ext = file.filename.split('.')[-1].lower()
        temp_input = f"{temp_filename}.{original_ext}"
        file.save(temp_input)
        
        try:
            audio = AudioSegment.from_file(
                temp_input,
                format=original_ext,
                parameters=["-y"]
            )
        except:
            try:
                audio = AudioSegment.from_file(temp_input)
            except Exception as e:
                logger.error(f"Impossible de lire le fichier audio: {e}")
                raise
        
        audio = audio.set_frame_rate(44100)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)
        
        audio.export(
            filename,
            format="wav",
            parameters=[
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "1",
                "-y"
            ]
        )
        
        logger.info(f"Audio de l'aidant converti avec succès: {file.filename} -> {filename}")
        
        if os.path.exists(temp_input):
            os.remove(temp_input)
        
        if not os.path.exists(filename):
            raise Exception("Le fichier WAV n'a pas été créé")
            
        if os.path.getsize(filename) == 0:
            raise Exception("Le fichier WAV est vide")
        
        thread = threading.Thread(target=audio_player.play_audio, args=(filename,))
        thread.start()
        
        return "Message vocal reçu et en cours de lecture", 200
        
    except Exception as e:
        error_msg = f"Erreur lors du traitement audio: {str(e)}"
        logger.error(error_msg)
        for temp_file in [f"{temp_filename}.{original_ext}", filename]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        return error_msg, 500

def run_flask_server():
    app.run(host='0.0.0.0', port=5000)

def setup_camera(camera_id="/dev/video0"):
    try:
        camera = cv.VideoCapture(camera_id)
        if not camera.isOpened():
            camera = cv.VideoCapture(0)
            if not camera.isOpened():
                raise ValueError("Impossible d'ouvrir la caméra")

        camera.set(cv.CAP_PROP_FRAME_WIDTH, CAMERA_RESOLUTION[0])
        camera.set(cv.CAP_PROP_FRAME_HEIGHT, CAMERA_RESOLUTION[1])
        camera.set(cv.CAP_PROP_FPS, CAMERA_FPS)
        
        camera.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*'MJPG'))
        camera.set(cv.CAP_PROP_BUFFERSIZE, 1)  # Réduire la latence

        logger.info(f"Caméra initialisée: {CAMERA_RESOLUTION}, {CAMERA_FPS} FPS")
        return camera

    except Exception as e:
        logger.error(f"Erreur d'initialisation caméra: {e}")
        raise

class VisualisationDetection:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        
        self.drawing_spec = self.mp_drawing.DrawingSpec(
            color=(0, 255, 0),
            thickness=2,
            circle_radius=4
        )
        
        self.connection_spec = self.mp_drawing.DrawingSpec(
            color=(255, 255, 0),
            thickness=2
        )
        
        self.points_cles = {
            'NOSE': self.mp_pose.PoseLandmark.NOSE.value,
            'LEFT_HIP': self.mp_pose.PoseLandmark.LEFT_HIP.value,
            'RIGHT_HIP': self.mp_pose.PoseLandmark.RIGHT_HIP.value,
            'LEFT_ANKLE': self.mp_pose.PoseLandmark.LEFT_ANKLE.value,
            'RIGHT_ANKLE': self.mp_pose.PoseLandmark.RIGHT_ANKLE.value
        }

    def dessiner_landmarks(self, image, results, chute_detectee=False):
        if results and hasattr(results, 'pose_landmarks') and results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.drawing_spec,
                connection_drawing_spec=self.connection_spec
            )

            h, w, _ = image.shape
            landmarks = results.pose_landmarks.landmark
            
            for nom_point, index in self.points_cles.items():
                landmark = landmarks[index]
                position = (int(landmark.x * w), int(landmark.y * h))
                couleur = (0, 0, 255) if chute_detectee else (0, 255, 0)
                cv.circle(image, position, 8, couleur, -1)
                cv.putText(image, nom_point, 
                          (position[0] + 10, position[1]),
                          cv.FONT_HERSHEY_SIMPLEX, 0.5, couleur, 1)

            if all(index in landmarks for index in [self.points_cles['NOSE'], 
                                                  self.points_cles['LEFT_HIP'],
                                                  self.points_cles['LEFT_ANKLE']]):
                angle = self.calculer_angle_corps(landmarks)
                cv.putText(image, f"Angle: {angle:.1f}°",
                          (10, 60), cv.FONT_HERSHEY_SIMPLEX,
                          1, (255, 255, 255), 2)

            self.afficher_boite_etat(image, chute_detectee)

        return image

    def calculer_angle_corps(self, landmarks):
        nose = landmarks[self.points_cles['NOSE']]
        hip = landmarks[self.points_cles['LEFT_HIP']]
        ankle = landmarks[self.points_cles['LEFT_ANKLE']]
        
        angle = np.degrees(np.arctan2(hip.x - nose.x, hip.y - nose.y))
        return abs(angle)

    def afficher_boite_etat(self, image, chute_detectee):
        h, w, _ = image.shape
        
        overlay = image.copy()
        cv.rectangle(overlay, (w-200, 10), (w-10, 90),
                    (0, 0, 0), -1)
        cv.addWeighted(overlay, 0.6, image, 0.4, 0, image)
        
        etat = "CHUTE DETECTEE!" if chute_detectee else "Normal"
        couleur = (0, 0, 255) if chute_detectee else (0, 255, 0)
        
        cv.putText(image, "Etat:", (w-190, 35),
                  cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv.putText(image, etat, (w-190, 70),
                  cv.FONT_HERSHEY_SIMPLEX, 0.8, couleur, 2)

class CommunicationServeur:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.alert_notification_url = f"{server_url}/alert_available"
        self.session = requests.Session()
        self.dernier_envoi = 0
        self.delai_min_entre_alertes = 300
        self.reset_audio_file()  

    def reset_audio_file(self):
        try:
            fichier_audio = "vocal_test.wav"
            if not os.path.exists(fichier_audio):
                logging.info("Création d'un fichier audio initial")
                texte = "Ceci est un message de test du système de détection de chute."
                tts = gTTS(text=texte, lang='fr')
                tts.save("temp_init.mp3")
                
                audio = AudioSegment.from_file("temp_init.mp3", format="mp3")
                audio = audio.set_frame_rate(44100)
                audio = audio.set_channels(1)
                audio = audio.set_sample_width(2)
                
                audio.export(
                    fichier_audio,
                    format="wav",
                    parameters=[
                        "-acodec", "pcm_s16le",
                        "-ar", "44100",
                        "-ac", "1"
                    ]
                )
                
                if os.path.exists("temp_init.mp3"):
                    os.remove("temp_init.mp3")
        except Exception as e:
            logging.error(f"Erreur lors de la création du fichier audio initial: {e}")

    def verifier_serveur(self):
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            logger.warning("Serveur Flask inaccessible")
            return False

    def envoyer_alerte(self, message_personnalise=None):
        temps_actuel = time.time()
        
        if temps_actuel - self.dernier_envoi < self.delai_min_entre_alertes:
            logging.info("Délai minimum entre les alertes non atteint")
            return False

        try:
            timestamp = datetime.now().strftime("%H heures %M minutes")
            timestamp_url = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            texte = message_personnalise or f"Attention ! Une chute a été détectée à {timestamp}. Veuillez vérifier rapidement."

            temp_mp3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp.mp3")
            fichier_audio = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocal_test.wav")
            
            tts = gTTS(text=texte, lang='fr')
            tts.save(temp_mp3)
            
            if not os.path.exists(temp_mp3):
                logging.error(f"Le fichier temporaire {temp_mp3} n'a pas été créé")
                return False
            
            try:
                audio = AudioSegment.from_mp3(temp_mp3)
                audio = audio.set_frame_rate(44100)
                audio = audio.set_channels(1)
                audio = audio.set_sample_width(2)
                
                audio.export(
                    fichier_audio,
                    format="wav"
                )
                
                if not os.path.exists(fichier_audio):
                    logging.error(f"Échec de création du fichier wav {fichier_audio}")
                    return False
                    
            except Exception as e:
                logging.error(f"Erreur lors de la conversion audio: {e}")
                
                try:
                    logging.info("Tentative de conversion avec ffmpeg en ligne de commande")
                    import subprocess
                    cmd = f"ffmpeg -y -i {temp_mp3} -acodec pcm_s16le -ar 44100 -ac 1 {fichier_audio}"
                    subprocess.run(cmd, shell=True, check=True)
                    
                    if not os.path.exists(fichier_audio):
                        logging.error("Échec de la conversion ffmpeg")
                        return False
                except Exception as e2:
                    logging.error(f"Échec de la conversion de secours: {e2}")
                    return False

            file_size = os.path.getsize(fichier_audio)
            if file_size == 0:
                logging.error("Le fichier audio généré est vide")
                return False
                
            logging.info(f"Fichier audio créé avec succès: {file_size} octets")
            
            try:
                if os.path.exists(temp_mp3):
                    os.remove(temp_mp3)
            except Exception as e:
                logging.warning(f"Impossible de supprimer le fichier temporaire: {e}")
            
            try:
                notification_url = f"{self.alert_notification_url}?timestamp={timestamp_url}&reason=chute"
                response = self.session.get(notification_url, timeout=5)
                
                if response.status_code == 200:
                    logging.info("Notification d'alerte envoyée avec succès")
                else:
                    logging.warning(f"Notification d'alerte non confirmée: {response.status_code}")
            except Exception as e:
                logging.error(f"Erreur lors de la notification d'alerte: {e}")
            
            time.sleep(1)
            
            try:
                with open(fichier_audio, 'a') as f:
                    f.write(" ")  
            except Exception as e:
                logging.error(f"Erreur lors de la modification du fichier: {e}")
            
            logging.info(f"Fichier audio '{fichier_audio}' créé avec succès et disponible pour l'app Android")
            self.dernier_envoi = temps_actuel
            return True

        except Exception as e:
            logging.error(f"Erreur lors de la création de l'alerte : {e}")
            return False

class DNNFallDetector:
    def __init__(self, model_path):
        try:
            if model_path.endswith(".h5"):
                self.model = load_model(model_path)
            else:
                self.model = tf.saved_model.load(model_path)
            
            logger.info("Modèle DNN chargé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            raise

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
            model_complexity=0,
            enable_segmentation=False
        )

        self.prediction_buffer = deque(maxlen=5)
        self.classes = ['Debout', 'Marche', 'Squat', 'Chute']

    def _extract_keypoints(self, results):
        """Extrait les points clés du corps depuis les résultats MediaPipe"""
        if not results.pose_landmarks:
            return None
            
        keypoints = []
        for landmark in results.pose_landmarks.landmark:
            keypoints.extend([landmark.x, landmark.y, landmark.z])
            
        return np.array(keypoints)

    def _normalize_keypoints(self, keypoints):
        return (keypoints - np.mean(keypoints)) / np.std(keypoints)

    def detect(self, frame):
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)

        if not results.pose_landmarks:
            return {
                'is_fall': False,
                'pose_detected': False,
                'confidence': 0.0,
                'current_pose': None,
                'mediapipe_results': results
            }

        keypoints = self._extract_keypoints(results)
        if keypoints is None:
            return {
                'is_fall': False,
                'pose_detected': False,
                'confidence': 0.0,
                'current_pose': None,
                'mediapipe_results': results
            }

        keypoints_normalized = self._normalize_keypoints(keypoints)
        keypoints_batch = np.expand_dims(keypoints_normalized, axis=0)

        predictions = self.model.predict(keypoints_batch, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = predictions[0][class_idx]

        if class_idx == self.classes.index('Chute'):
            confidence = min(confidence * FALLING_CONFIDENCE_MULTIPLIER, 1.0)
            logger.debug(f"Confiance ajustée pour 'falling': {confidence} (multiplicateur: {FALLING_CONFIDENCE_MULTIPLIER})")

        self.prediction_buffer.append(class_idx)

        final_prediction = max(set(self.prediction_buffer), 
                             key=self.prediction_buffer.count)
        is_fall = final_prediction == self.classes.index('Chute')

        return {
            'is_fall': is_fall,
            'pose_detected': True,
            'confidence': float(confidence),
            'current_pose': self.classes[final_prediction],
            'mediapipe_results': results
        }

class DetectionChuteAutomatique:
    def __init__(self, model_path=None, server_url="http://localhost:5000", camera_id="/dev/video0"):
        self.camera_id = camera_id
        self.serveur = CommunicationServeur(server_url)
        self.visualisation = VisualisationDetection()
        
        self.use_dnn = model_path is not None
        
        if self.use_dnn:
            try:
                self.detecteur_dnn = DNNFallDetector(model_path)
                logger.info("Mode détection: DNN")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du détecteur DNN: {e}")
                logger.warning("Repli sur IsolationForest")
                self.use_dnn = False
                self.initialiser_isolationforest()
        else:
            self.initialiser_isolationforest()
            logger.info("Mode détection: IsolationForest")
        
        self.en_pause = False
        self.chute_confirmee = threading.Event()
        self.chute_en_cours = False
        self.alerte_envoyee = False
        
        self.compteur_confirmation = 0
        self.seuil_confirmation = 3  

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.6, 
            min_tracking_confidence=0.6,
            model_complexity=0,  
            enable_segmentation=False
        )

    def initialiser_isolationforest(self):
        self.detecteur_anomalies = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=50 
        )
        
        self.buffer_positions = deque(maxlen=5)  
        self.historique_mouvements = deque(maxlen=50)
        self.stats_mouvement = {
            'vitesse_moyenne': 0,
            'acceleration_moyenne': 0,
            'vitesse_max': 0,
            'acceleration_max': 0
        }
        
    def forcer_reset_complet(self):
        self.en_pause = False
        self.chute_confirmee.set()
        self.chute_en_cours = False
        self.alerte_envoyee = False
        self.compteur_confirmation = 0
        
        if not self.use_dnn:
            self.historique_mouvements.clear()
            self.buffer_positions.clear()
        
            self.detecteur_anomalies = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=50
            )
        
            self.stats_mouvement = {
                'vitesse_moyenne': 0,
                'acceleration_moyenne': 0,
                'vitesse_max': 0,
                'acceleration_max': 0
            }
        
        logger.info("Réinitialisation complète du système de détection effectuée")
        
        return True

    def reinitialiser_detection(self):
        self.en_pause = False
        self.chute_confirmee.set()
        self.chute_en_cours = False
        self.alerte_envoyee = False
        self.compteur_confirmation = 0
    
        if not self.use_dnn:
            self.historique_mouvements.clear()
        
            self.buffer_positions.clear()
        
            self.stats_mouvement = {
                'vitesse_moyenne': 0,
                'acceleration_moyenne': 0,
                'vitesse_max': 0,
                'acceleration_max': 0
            }
        
            self.detecteur_anomalies = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=50
            )
    
        logger.info("État de détection réinitialisé complètement pour permettre nouvelles détections")
        
    def forcer_reset_etat(self):
        self.en_pause = False
        self.chute_confirmee.set()
        self.chute_en_cours = False
        self.alerte_envoyee = False
        self.compteur_confirmation = 0
        
        if not self.use_dnn:
            self.historique_mouvements.clear()
            self.buffer_positions.clear()
    
        logger.info("État de détection réinitialisé de force après confirmation")
        
    def calculer_metriques_mouvement(self, landmarks):
        if not landmarks:
            return None
            
        points_cles = {
            'tete': (landmarks[self.mp_pose.PoseLandmark.NOSE.value].x,
                    landmarks[self.mp_pose.PoseLandmark.NOSE.value].y),
            'hanche': ((landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x +
                       landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].x) / 2,
                      (landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y +
                       landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y) / 2),
            'pieds': ((landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x +
                      landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value].x) / 2,
                     (landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y +
                      landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value].y) / 2)
        }

        hauteur_corps = abs(points_cles['tete'][1] - points_cles['pieds'][1])
        angle_vertical = np.arctan2(points_cles['tete'][1] - points_cles['hanche'][1],
                                  points_cles['tete'][0] - points_cles['hanche'][0])

        self.buffer_positions.append((points_cles['hanche'], time.time()))

        if len(self.buffer_positions) >= 2:
            pos1, t1 = self.buffer_positions[-2]
            pos2, t2 = self.buffer_positions[-1]
            dt = t2 - t1

            if dt > 0:
                vitesse = np.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2) / dt
                if len(self.buffer_positions) >= 3:
                    pos0, t0 = self.buffer_positions[-3]
                    dt_prev = t1 - t0
                    vitesse_prev = np.sqrt((pos1[0] - pos0[0])**2 + (pos1[1] - pos0[1])**2) / dt_prev
                    acceleration = (vitesse - vitesse_prev) / dt
                else:
                    acceleration = 0
            else:
                vitesse = 0
                acceleration = 0

            return np.array([hauteur_corps, angle_vertical, vitesse, acceleration, points_cles['hanche'][1]])

        return None

    def detecter_chute_isolationforest(self, metriques):
        if metriques is None:
            return False

        self.historique_mouvements.append(metriques)
    
        if len(self.historique_mouvements) < 15:  
            return False

        X = np.array(list(self.historique_mouvements))
        self.detecteur_anomalies.fit(X)
        prediction = self.detecteur_anomalies.predict(metriques.reshape(1, -1))

        if prediction[0] == -1:
            vitesse = metriques[2]
            acceleration = metriques[3]
            position_verticale = metriques[4]

            seuil_vitesse = np.mean([m[2] for m in self.historique_mouvements]) * 1.8  
            seuil_acceleration = np.mean([m[3] for m in self.historique_mouvements]) * 1.8
        
            chute_detectee = (vitesse > seuil_vitesse and
                        acceleration > seuil_acceleration and
                        position_verticale > 0.6)  
        
            if chute_detectee:
                logger.info(f"Valeurs de chute - vitesse: {vitesse:.2f}/{seuil_vitesse:.2f}, " +
                    f"accel: {acceleration:.2f}/{seuil_acceleration:.2f}, " +
                    f"pos_vert: {position_verticale:.2f}/0.6")
        
            return chute_detectee

        return False

    def demarrer_detection(self):
        logger.info(f"Démarrage de la détection sur Raspberry Pi 5 - Mode {'DNN' if self.use_dnn else 'IsolationForest'}")
    
        try:
            camera = setup_camera(self.camera_id)
        except Exception as e:
            logger.error(f"Erreur caméra: {e}")
            return
    
        self.chute_en_cours = False
        self.alerte_envoyee = False
        frames_sans_detection = 0
        derniere_frame_temps = time.time()
        frame_count = 0
    
        self.en_pause = False
        self.chute_confirmee.clear()
        
    
        try:
            while True:
                try:
                    if self.en_pause:
                        blank_frame = np.zeros((CAMERA_RESOLUTION[1], CAMERA_RESOLUTION[0], 3), dtype=np.uint8)
                    
                        cv.putText(blank_frame, "CHUTE DETECTEE", 
                                  (30, CAMERA_RESOLUTION[1]//2 - 60),
                                  cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                    
                        cv.putText(blank_frame, "Systeme en pause", 
                                  (30, CAMERA_RESOLUTION[1]//2 - 20),
                                  cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 240, 255), 2)
                              
                        cv.putText(blank_frame, "1. L'aidant doit confirmer sur l'app", 
                                  (30, CAMERA_RESOLUTION[1]//2 + 20),
                                  cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                              
                        cv.putText(blank_frame, "2. Appuyez sur 'R' pour redemarrer le systeme", 
                                  (30, CAMERA_RESOLUTION[1]//2 + 50),
                                  cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                              
                        cv.putText(blank_frame, "Redemarrage manuel obligatoire apres confirmation", 
                                  (30, CAMERA_RESOLUTION[1]//2 + 90),
                                  cv.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 1)
                    
                        cv.imshow('Detection Chute - RPI5', blank_frame)
                    
                        key = cv.waitKey(100) & 0xFF
                        if key == ord('r') or key == ord('R'):
                            logger.info("Reprise forcée par l'utilisateur")
                            self.en_pause = False
                            self.chute_en_cours = False
                            self.alerte_envoyee = False
                            self.chute_confirmee.clear()
                            self.compteur_confirmation = 0
                            
                            if not self.use_dnn:
                                self.historique_mouvements.clear()
                                self.buffer_positions.clear()
                                
                                self.detecteur_anomalies = IsolationForest(
                                    contamination=0.1,
                                    random_state=42,
                                    n_estimators=50
                                )
                    
                        continue
                        
                    frame_count += 1
                    if frame_count % 2 != 0: 
                        continue
                        
                    ret, frame = camera.read()
                    if not ret:
                        logger.error("Erreur lecture frame")
                        continue
                    
                    frame = cv.resize(frame, CAMERA_RESOLUTION)
                    
                    temps_actuel = time.time()
                    fps = 1 / (temps_actuel - derniere_frame_temps)
                    derniere_frame_temps = temps_actuel
                    
                    if self.use_dnn:
                        resultats = self.detecteur_dnn.detect(frame)
                        
                        if resultats['pose_detected']:
                            frames_sans_detection = 0
                            
                            if resultats['is_fall']:
                                self.compteur_confirmation += 1
                                if self.compteur_confirmation >= self.seuil_confirmation and not self.chute_en_cours:
                                    logger.warning("CHUTE DETECTÉE par DNN!")
                                    self.chute_en_cours = True
                                    if not self.alerte_envoyee:
                                        if self.serveur.envoyer_alerte():
                                            logger.info("Alerte audio créée pour l'application Android")
                                        self.alerte_envoyee = True
                                        
                                        logger.info("Mise en pause de la détection jusqu'à confirmation")
                                        self.en_pause = True
                            else:
                                self.compteur_confirmation = 0
                                
                            frame = self.visualisation.dessiner_landmarks(
                                frame, resultats['mediapipe_results'], self.chute_en_cours)
                                
                            cv.putText(frame, f"Pose: {resultats['current_pose']}", (10, 90),
                                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            cv.putText(frame, f"Conf: {resultats['confidence']:.2f}", (10, 120),
                                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            
                        else:
                            frames_sans_detection += 1
                    else:
                        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                        results = self.pose.process(frame_rgb)
                        
                        if results.pose_landmarks:
                            frames_sans_detection = 0
                            metriques = self.calculer_metriques_mouvement(
                                results.pose_landmarks.landmark)
                                
                            if metriques is not None:
                                est_chute = self.detecter_chute_isolationforest(metriques)
                                if est_chute and not self.chute_en_cours:
                                    logger.warning("CHUTE DETECTÉE par IsolationForest!")
                                    self.chute_en_cours = True
                                    if not self.alerte_envoyee:
                                        if self.serveur.envoyer_alerte():
                                            logger.info("Alerte audio créée pour l'application Android")
                                        self.alerte_envoyee = True
                                        
                                        logger.info("Mise en pause de la détection jusqu'à confirmation")
                                        self.en_pause = True
                                        
                                elif not est_chute:
                                    self.chute_en_cours = False
                                    
                            frame = self.visualisation.dessiner_landmarks(
                                frame, results, self.chute_en_cours)
                        else:
                            frames_sans_detection += 1
                    
                    if frames_sans_detection > 15:  
                        frames_sans_detection = 0
                        logger.warning("Perte de détection prolongée")
                    
                    cv.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                              cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    mode_detection = "DNN" if self.use_dnn else "IsolationForest"
                    cv.putText(frame, f"Mode: {mode_detection}", (10, 60),
                              cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    status_serveur = "Serveur : OK" if self.serveur.verifier_serveur() else "Serveur : KO"
                    cv.putText(frame, status_serveur, (10, frame.shape[0] - 20),
                              cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    cv.imshow('Detection Chute - RPI5', frame)
                    
                    if cv.waitKey(1) & 0xFF == ord('q'):
                        break
                        
                except Exception as e:
                    logger.error(f"Erreur traitement: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Arrêt surveillance")
        finally:
            camera.release()
            cv.destroyAllWindows()

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init(
            frequency=44100,  
            size=-16,          
            channels=1,        
            buffer=1024       
        )
        self.is_playing = False

    def play_audio(self, audio_file):
        try:
            if not os.path.exists(audio_file):
                logger.error(f"Fichier audio non trouvé: {audio_file}")
                return
                
            if os.path.getsize(audio_file) == 0:
                logger.error(f"Fichier audio vide: {audio_file}")
                return
                
            try:
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                self.is_playing = True
                
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                self.is_playing = False
                
            except Exception as e:
                logger.error(f"Erreur lors de la lecture audio: {e}")
                self.is_playing = False
                
                try:
                    logger.info("Tentative de reconversion du fichier problématique")
                    temp_audio = AudioSegment.from_file(audio_file)
                    temp_audio = temp_audio.set_frame_rate(44100)
                    temp_audio = temp_audio.set_channels(1)
                    
                    backup_file = audio_file + ".backup.wav"
                    temp_audio.export(backup_file, format="wav")
                    
                    pygame.mixer.music.load(backup_file)
                    pygame.mixer.music.play()
                    self.is_playing = True
                    
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                    
                    self.is_playing = False
                    
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                        
                except Exception as e2:
                    logger.error(f"Échec de la solution alternative: {e2}")
                    self.is_playing = False
                
        except Exception as e:
            logger.error(f"Erreur globale lors de la lecture audio: {e}")
            self.is_playing = False

audio_player = AudioPlayer()

detecteur_global = None

def main():
    multiprocessing.set_start_method('spawn')
    
    try:
        server_process = multiprocessing.Process(
            target=run_flask_server,
            daemon=True  
        )
        server_process.start()
        logger.info("Serveur Flask démarré")
        
        time.sleep(2)
        
        model_path = "/home/toto/Documents/fall_detection/models/fall_detection_model/fall_classifier.h5"
        
        if os.path.exists(model_path):
            logger.info(f"Utilisation du modèle DNN: {model_path}")
            use_model = model_path
        else:
            logger.warning(f"Modèle non trouvé: {model_path}. Utilisation de IsolationForest")
            use_model = None
        
        global detecteur_global
        detecteur_global = DetectionChuteAutomatique(model_path=use_model)
        detecteur_global.demarrer_detection()
        
    except KeyboardInterrupt:
        logger.info("Arrêt programme")
    except Exception as e:
        logger.error(f"Erreur: {e}")
    finally:
        if 'server_process' in locals():
            server_process.terminate()
            server_process.join(timeout=1)

if __name__ == "__main__":
    main()