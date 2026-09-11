import time
import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Gauge

# --- CONFIGURATION ---
# Si le script tourne dans Docker, l'hôte est le nom du service "mosquitto"
# S'il tourne directement sur votre PC, remplacez par "localhost"
MQTT_BROKER = "mosquitto" 
MQTT_PORT = 1883
MQTT_TOPIC = "parc_solaire/+/luminosite" # Le '+' permet d'écouter tous les panneaux

# Définition de la puissance maximale d'un panneau (ex: 250 Watts)
MAX_POWER_PER_PANEL = 250.0 

# --- MÉTRIQUES PROMETHEUS ---
# Les 'labels' (étiquettes) permettent de différencier les panneaux dans Grafana
LUMINOSITY_GAUGE = Gauge('solar_panel_luminosity_percent', 'Luminosité mesurée (%)', ['panel'])
POWER_GAUGE = Gauge('solar_panel_power_watts', 'Puissance estimée (W)', ['panel'])
TOTAL_POWER_GAUGE = Gauge('solar_park_total_power_watts', 'Puissance totale du parc (W)')

# Dictionnaire pour garder en mémoire la dernière puissance de chaque panneau
current_power = {"1": 0.0, "2": 0.0}

# --- FONCTIONS MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté avec succès au broker Mosquitto !")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Échec de la connexion, code : {rc}")

def on_message(client, userdata, msg):
    try:
        # msg.topic ressemble à "parc_solaire/panneau_1/luminosite"
        # On découpe la chaîne pour extraire le numéro du panneau
        parts = msg.topic.split('/')
        panel_id = parts[1].split('_')[1] # Récupère "1" ou "2"

        # Récupération de la luminosité
        luminosity = float(msg.payload.decode('utf-8'))
        
        # --- CALCUL DE LA PUISSANCE ---
        # Simulation basique : Puissance = (Luminosité / 100) * Puissance_Max
        power = (luminosity / 100.0) * MAX_POWER_PER_PANEL
        
        # Mise à jour des jauges individuelles pour ce panneau
        LUMINOSITY_GAUGE.labels(panel=panel_id).set(luminosity)
        POWER_GAUGE.labels(panel=panel_id).set(power)
        
        # Calcul et mise à jour de la puissance totale du parc
        current_power[panel_id] = power
        total_power = sum(current_power.values())
        TOTAL_POWER_GAUGE.set(total_power)
        
        print(f"Panneau {panel_id} : {luminosity}% -> {power:.1f}W | Total Parc: {total_power:.1f}W")
        
    except Exception as e:
        print(f"Erreur lors du traitement du message : {e}")

# --- LANCEMENT ---
if __name__ == '__main__':
    # Démarre le serveur web Prometheus sur le port 8000
    start_http_server(8000)
    print("Serveur Prometheus prêt sur le port 8000. En attente de MQTT...")
    
    # Configuration du client MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Boucle de tentative de connexion (utile si Mosquitto démarre en même temps)
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception:
            print("Broker MQTT introuvable, nouvelle tentative dans 5 secondes...")
            time.sleep(5)
            
    # Laisse le script tourner en boucle
    client.loop_forever()