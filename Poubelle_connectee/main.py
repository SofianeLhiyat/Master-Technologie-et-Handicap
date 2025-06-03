from machine import Pin, PWM
import network
import socket
import time
import gc

SERVO_PIN = 23
SSID = 'Souf'
PASSWORD = 'soufsouf'

servo = PWM(Pin(SERVO_PIN), freq=50)
CENTER = 77
RIGHT = 122
LEFT = 32

servo.duty(CENTER)

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connexion au WiFi...')
        wlan.connect(SSID, PASSWORD)
        timeout = 10  
        start_time = time.time()
        while not wlan.isconnected():
            if time.time() - start_time > timeout:
                print("Échec de connexion au WiFi.")
                return False
            time.sleep(1)
    print('Connecté au WiFi. IP:', wlan.ifconfig()[0])
    return True

def move_servo(position, duration=2):
    servo.duty(position)
    start_time = time.time()
    while time.time() - start_time < duration:
        pass  
    servo.duty(CENTER)

def web_server():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    s.bind(('', 80))
    s.listen(5)
    print("Serveur démarré et en attente de connexions...")
    
    while True:
        try:
            conn, addr = s.accept()
            print('Client connecté depuis:', addr)
            
            while True:
                try:
                    request = conn.recv(1024).decode()
                    if not request:  
                        break
                    
                    print("Requête reçue:", request)
                    
                    if 'servo/right' in request:
                        print("Mouvement vers la droite")
                        move_servo(RIGHT)
                        time.sleep(2)
                        servo.duty(CENTER)
                    elif 'servo/left' in request:
                        print("Mouvement vers la gauche")
                        move_servo(LEFT)
                        time.sleep(2)
                        servo.duty(CENTER)
                    else:
                        print("Position centrale")
                        servo.duty(CENTER)
                    
                    response = (
                        "HTTP/1.1 200 OK\n"
                        "Connection: keep-alive\n"
                        "Content-Type: text/plain\n\n"
                        "Servo command received"
                    )
                    conn.send(response.encode())
                
                except Exception as e:
                    print("Erreur de traitement :", e)
                    break
            
            conn.close()  
            
        except Exception as e:
            print("Erreur de connexion :", e)
            continue

def main():
    print("Démarrage du programme...")
    
    if not wifi_connect():
        print("Impossible de se connecter au WiFi. Réessayer dans 5 secondes...")
        time.sleep(5)
        return main()  
    
    while True:
        try:
            gc.collect()
            print("Mémoire libre :", gc.mem_free())
            web_server()
        except Exception as e:
            print("Erreur serveur :", e)
            time.sleep(5)  

if __name__ == '__main__':
    main()
