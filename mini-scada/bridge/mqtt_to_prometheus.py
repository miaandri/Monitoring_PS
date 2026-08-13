import re
import time
import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Gauge, Counter

# ============================================================================
# PARAMÈTRES DE MODÉLISATION DU PARC SOLAIRE
# ============================================================================
PANEL_NOMINAL_POWER_W = 300.0  # Puissance crête par panneau (300 Wc)
INVERTER_EFFICIENCY = 0.96     # Rendement de l'onduleur (96%)
THERMAL_LOSS_FACTOR = 0.90     # Pertes thermiques en plein soleil (10%)
INVERTER_THRESHOLD = 5.0       # Seuil d'allumage de l'onduleur (5% de luminosité)

# Stockage interne de l'état des panneaux
panel_powers = {}
last_energy_update_time = time.time()

# ============================================================================
# MÉTRIQUES PROMETHEUS
# ============================================================================
# 1. Luminosité brute (0 à 100%)
SOLAR_LUMINOSITY = Gauge(
    'solar_panel_luminosity_percent',
    'Luminosite mesurée par la photoresistance (0 a 100%)',
    ['panel_id']
)

# 2. Puissance DC individuelle calculée (en Watts)
SOLAR_PANEL_POWER = Gauge(
    'solar_panel_power_watts',
    'Puissance DC calculee par panneau en Watts',
    ['panel_id']
)

# 3. Puissance AC globale produite par le parc (en Watts)
SOLAR_PARK_TOTAL_POWER = Gauge(
    'solar_park_total_power_watts',
    'Puissance AC totale produite par le parc en Watts'
)

# 4. Énergie totale cumulée (en kWh)
SOLAR_PARK_ENERGY_KWH = Counter(
    'solar_park_energy_kwh_total',
    'Energie totale produite par le parc en kWh'
)


def update_park_energy():
    """Calcule et accumule l'énergie produite (en kWh) en fonction du temps écoulé."""
    global last_energy_update_time

    current_time = time.time()
    dt = current_time - last_energy_update_time
    last_energy_update_time = current_time

    total_power_ac = sum(panel_powers.values())
    SOLAR_PARK_TOTAL_POWER.set(total_power_ac)

    # Convertit les Watts.secondes en kWh : (P * dt) / 3600000
    if total_power_ac > 0 and dt > 0:
        energy_kwh = (total_power_ac * dt) / 3600000.0
        SOLAR_PARK_ENERGY_KWH.inc(energy_kwh)


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connecté au Broker avec le code : {rc}")
    client.subscribe("parc_solaire/+/luminosite")


def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        luminosity = float(msg.payload.decode('utf-8'))

        match = re.search(r'parc_solaire/(panneau_\d+)/luminosite', topic)
        if match:
            panel_id = match.group(1)

            # --- TRAITEMENT 1 : Luminosité brute (0-100%) ---
            SOLAR_LUMINOSITY.labels(panel_id=panel_id).set(luminosity)

            # --- TRAITEMENT 2 : Puissance DC individuelle ---
            power_dc = PANEL_NOMINAL_POWER_W * (luminosity / 100.0)
            SOLAR_PANEL_POWER.labels(panel_id=panel_id).set(power_dc)

            # --- TRAITEMENT 3 : Puissance AC avec rendement et pertes ---
            if luminosity >= INVERTER_THRESHOLD:
                power_ac = power_dc * INVERTER_EFFICIENCY * THERMAL_LOSS_FACTOR
            else:
                power_ac = 0.0

            panel_powers[panel_id] = power_ac

            # --- TRAITEMENT 4 : Mise à jour globale & Énergie ---
            update_park_energy()

            print(
                f"[METRIC] {panel_id} | Lum: {luminosity:.1f}% | "
                f"P_DC: {power_dc:.1f}W | P_AC: {power_ac:.1f}W"
            )

    except Exception as e:
        print(f"[ERREUR] Impossible de parser le message : {e}")


if __name__ == '__main__':
    # Démarre le serveur HTTP Prometheus sur le port 8000
    start_http_server(8000)
    print("[PROMETHEUS] Serveur de métriques prêt sur http://localhost:8000/metrics")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    time.sleep(2)
    # Si le script tourne dans Docker avec mosquitto, mettez "mosquitto" en host, sinon "localhost"
    client.connect("mosquitto", 1883, 60)
    client.loop_forever()