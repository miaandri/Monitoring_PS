#include <WiFi.h>
#include <PubSubClient.h>

const char* WIFI_SSID     = "realme7";
const char* WIFI_PASSWORD = "12345678";

const char* MQTT_SERVER   = "192.168.0.228"; 
const int   MQTT_PORT     = 1883;

const int NUM_SENSORS = 2;
const int LDR_PINS[NUM_SENSORS] = {32, 33};

# define PUBLISH_INTERVAL 5000

WiFiClient espClient;
PubSubClient mqttClient(espClient);

void setupWiFi() {
  delay(10);
  Serial.println();
  Serial.print("Connexion au réseau Wi-Fi : ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi connecté !");
  Serial.print("Adresse IP de l'ESP32 : ");
  Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Tentative de connexion au Broker MQTT...");
    
    String clientId = "ESP32_SolarParc_Client-";
    clientId += String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println(" Connecté !");
    } else {
      Serial.print(" Échec, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" nouvelle tentative dans 5 secondes...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(LDR_PINS[i], INPUT);
  }

  setupWiFi();
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  unsigned long now = millis();
  unsigned long lastPublishTime;
  if (now - lastPublishTime >= PUBLISH_INTERVAL) {
    lastPublishTime = now;

    Serial.println("--- Lecture et publication des capteurs ---");

    for (int i = 0; i < NUM_SENSORS; i++) {
      int rawValue = analogRead(LDR_PINS[i]);

      int luminosity = map(rawValue, 0, 4095, 0, 100);

      char topic[60];
      snprintf(topic, sizeof(topic), "parc_solaire/panneau_%d/luminosite", i + 1);

      char payload[10];
      snprintf(payload, sizeof(payload), "%d", luminosity);
      Serial.printf("Topic: %s | Luminosité: %d%%\n", topic, luminosity);
      bool published = mqttClient.publish(topic, payload);

      if (published) {
        Serial.printf("Topic: %s | Luminosité: %d%%\n", topic, luminosity);
      } else {
        Serial.printf("Échec d'envoi pour le topic %s\n", topic);
      }
    }
  }
}