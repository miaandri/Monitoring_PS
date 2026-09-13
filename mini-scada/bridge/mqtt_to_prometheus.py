import time
import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Gauge

MQTT_BROKER = "mosquitto" 
MQTT_PORT = 1883
MQTT_TOPIC = "parc_solaire/+/luminosite"

MAX_POWER_PER_PANEL = 250.0 


LUMINOSITY_GAUGE = Gauge('solar_panel_luminosity_percent', 'Luminosité mesurée (%)', ['panel'])
POWER_GAUGE = Gauge('solar_panel_power_watts', 'Puissance estimée (W)', ['panel'])
TOTAL_POWER_GAUGE = Gauge('solar_park_total_power_watts', 'Puissance totale du parc (W)')

current_power = {"1": 0.0, "2": 0.0}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté avec succès au broker Mosquitto !")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Échec de la connexion, code : {rc}")

def on_message(client, userdata, msg):
    try:
        parts = msg.topic.split('/')
        panel_id = parts[1].split('_')[1]

        luminosity = float(msg.payload.decode('utf-8'))

        power = (luminosity / 100.0) * MAX_POWER_PER_PANEL
        
        LUMINOSITY_GAUGE.labels(panel=panel_id).set(luminosity)
        POWER_GAUGE.labels(panel=panel_id).set(power)
        
        current_power[panel_id] = power
        total_power = sum(current_power.values())
        TOTAL_POWER_GAUGE.set(total_power)
        
        print(f"Panneau {panel_id} : {luminosity}% -> {power:.1f}W | Total Parc: {total_power:.1f}W")
        
    except Exception as e:
        print(f"Erreur lors du traitement du message : {e}")

if __name__ == '__main__':
    start_http_server(8000)
    print("Serveur Prometheus prêt sur le port 8000. En attente de MQTT...")
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception:
            print("Broker MQTT introuvable, nouvelle tentative dans 5 secondes...")
            time.sleep(5)
            
    client.loop_forever()