import board
import digitalio
import time
import wifi
import socketpool
import adafruit_requests
import ssl
import rtc
from adafruit_ntp import NTP
import json
from random import randint

WIFI_SSID = "****"  
WIFI_PASSWORD = "*****"  

FLASK_SERVER = "*.*.*.*"  
FLASK_PORT = 5000
FLASK_TAPIS_ENDPOINT = f"http://{FLASK_SERVER}:{FLASK_PORT}/tapis_detection"

print("Initialisation du système de détection de chute par tapis...")

def connecter_wifi():
    print(f"Connexion au réseau WiFi: {WIFI_SSID}...")
    wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
    print(f"Connecté! Adresse IP: {wifi.radio.ipv4_address}")

def configurer_horloge():
    pool = socketpool.SocketPool(wifi.radio)
    ntp = NTP(pool, tz_offset=1) 
    
    try:
        rtc.RTC().datetime = ntp.datetime
        print(f"Horloge synchronisée: {obtenir_horodatage()}")
    except Exception as e:
        print(f"Erreur de synchronisation NTP: {e}")

def obtenir_horodatage():
    t = time.localtime()
    return f"{t.tm_mday:02d}/{t.tm_mon:02d}/{t.tm_year} {t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"

tapis_pins = [
    board.A0,
    board.A1,
    board.A2, 
    board.A3,
    board.A4,   
    board.A5,   
    board.D5,  
    board.D6,  
    board.D9,  
    board.D10, 
    board.D11  
]

def configurer_tapis(pin):
    tapis = digitalio.DigitalInOut(pin)
    tapis.direction = digitalio.Direction.INPUT
    tapis.pull = digitalio.Pull.UP  
    return tapis

tapis_list = [configurer_tapis(pin) for pin in tapis_pins]
tapis_noms = [f"Tapis {i+1}" for i in range(len(tapis_pins))]
tapis_emojis = ["🟥", "🟦", "🟩", "🟨", "🟪", "🟧", "🟫", "⬛", "⚪", "🔴", "🔵"]

debut_detection = None      
notification_envoyee = False 
nb_tapis_min = 4           
duree_min_secondes = 5      
delai_entre_alertes = 60   
derniere_notification = 0  

en_attente_confirmation = False 
temps_attente_confirmation = 30  

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

def clignoter_led(n, duree=0.2):
    """Fait clignoter la LED n fois"""
    for _ in range(n):
        led.value = True
        time.sleep(duree)
        led.value = False
        time.sleep(duree)

def notifier_detection_tapis():
    global derniere_notification, en_attente_confirmation
    
    
    if time.time() - derniere_notification < delai_entre_alertes:
        print(f"Délai entre notifications non écoulé, notification ignorée")
        return False
    
    try:
        horodatage = obtenir_horodatage()
        print(f"NOTIFICATION: Chute potentielle détectée à {horodatage}")

        clignoter_led(3, 0.1)
        
        pool = socketpool.SocketPool(wifi.radio)
        requests = adafruit_requests.Session(pool, ssl.create_default_context())
        
        response = requests.get(FLASK_TAPIS_ENDPOINT)
        
        if response.status_code == 200:
            print("Notification envoyée avec succès!")

            try:
                reponse_json = response.json()
                status = reponse_json.get("status", "")
                
                if status == "confirmed":
                    print("CONFIRMATION! La caméra a également détecté une chute!")
                    clignoter_led(5, 0.1) 
                    en_attente_confirmation = False
                
                elif status == "waiting":
                    print("En attente de confirmation par la caméra...")
                    en_attente_confirmation = True
                    clignoter_led(2, 0.3)  
                
                else:
                    print(f"Statut de détection: {status}")
                    en_attente_confirmation = False
                
            except ValueError:
                print("Impossible de décoder la réponse JSON")
                en_attente_confirmation = False
            
            derniere_notification = time.time()
            return True
            
        else:
            print(f"Échec d'envoi de la notification. Code: {response.status_code}")
            clignoter_led(2, 0.5) 
            return False
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification: {e}")
        clignoter_led(2, 0.5)  
        return False

try:
    connecter_wifi()
    clignoter_led(2)

    configurer_horloge()
    clignoter_led(3)
    
    print("Système prêt! Surveillance des tapis en cours...")
    
except Exception as e:
    print(f"Erreur lors de l'initialisation: {e}")
    while True:
        clignoter_led(10, 0.1)
        time.sleep(1)

while True:
    tapis_actifs = []
    tapis_noms_actifs = []
    
    for i, tapis in enumerate(tapis_list):
        if not tapis.value:  
            tapis_actifs.append(i)
            tapis_noms_actifs.append(tapis_noms[i])
            print(f"{tapis_emojis[i]} {tapis_noms[i]} pressé!")

    nb_tapis_actifs = len(tapis_actifs)

    if nb_tapis_actifs >= nb_tapis_min and debut_detection is None:
        debut_detection = time.time()
        print(f" Début de détection de chute: {nb_tapis_actifs} tapis actifs")
        led.value = True
        
    elif nb_tapis_actifs < nb_tapis_min and debut_detection is not None:
        debut_detection = None
        notification_envoyee = False
        led.value = False  
        print("Détection annulée: nombre de tapis insuffisant")

    elif nb_tapis_actifs >= nb_tapis_min and debut_detection is not None:
        duree_actuelle = time.time() - debut_detection

        if duree_actuelle >= duree_min_secondes and not notification_envoyee:
            if notifier_detection_tapis():
                notification_envoyee = True
                print(f"Détection pendant {duree_actuelle:.1f} secondes")
                if not en_attente_confirmation:
                    led.value = False
                    debut_detection = None 
    
    if en_attente_confirmation and debut_detection is not None:
        temps_attente = time.time() - derniere_notification
        if temps_attente > temps_attente_confirmation:
            print(f"Délai d'attente de confirmation caméra dépassé ({temps_attente:.1f}s > {temps_attente_confirmation}s)")
            en_attente_confirmation = False
            notification_envoyee = False
            debut_detection = None
            led.value = False

    time.sleep(0.5)

    if not wifi.radio.connected:
        print("Perte de connexion WiFi. Tentative de reconnexion...")
        try:
            connecter_wifi()
            clignoter_led(2)
        except Exception as e:
            print(f"Échec de reconnexion: {e}")