#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <MPU6050.h>

const char* ssid = "DESKTOP-20S6VHV 7477";
const char* password = "12345678";
WiFiClient wifiClient;
char* topics[] = { "on_off", "axle" };
bool on_off = false;
int selectedAxis = 0;

const char* mqttServer = "192.168.137.1";
const int mqttPort = 1883;
const char* clientId = "18741155-810b-4ab7-9c81-93a63352a132";

PubSubClient MQTT(wifiClient);

// Defina o tamanho do buffer
const int bufferSize = 20;  // Ajuste o tamanho conforme necessário

float dataBuffer[bufferSize];  // Crie um buffer como uma matriz de ponto flutuante
int bufferIndex = 0;  // Variável para controlar a posição atual no buffer

unsigned long lastUpdateTime = 0;

MPU6050 mpu;

int16_t accelX, accelY, accelZ;

void setup(void) {
  Serial.begin(115200);
  MQTT.setServer(mqttServer, mqttPort);
  MQTT.setKeepAlive(3);
  MQTT.setCallback(receivePackage);

  Wire.begin();
  mpu.initialize();
  mpu.setFullScaleAccelRange(3); // Defina o valor apropriado para o alcance do acelerômetro
}

void loop(void) {
  keepConnections();
 
  int timeNow = millis(); 
  if (timeNow - lastUpdateTime < 1) return;
  lastUpdateTime = timeNow;
  
  if (on_off && selectedAxis > 0) {

    mpu.getAcceleration(&accelX, &accelY, &accelZ);

    // Coleta os dados com base na escolha do eixo
    float rawData;
    if (selectedAxis == 1) {
      rawData = accelX;
    } else if (selectedAxis == 2) {
      rawData = accelY;
    } else if (selectedAxis == 3) {
      rawData = accelZ;
    }

    // Coloca os dados no buffer
    dataBuffer[bufferIndex] = rawData;

    // Incrementa o índice do buffer
    bufferIndex++;

    // Verifique se o buffer está cheio
    if (bufferIndex >= bufferSize) {
      // Envie os dados do buffer via MQTT
      String concatenatedString = "";
      for (int i = 0; i < bufferSize; i++) {
          concatenatedString += String(dataBuffer[i]).c_str();
          
          // Adicione uma vírgula após cada valor, exceto o último
          if (i < bufferSize - 1) {
              concatenatedString += ",";
          }
      }
      MQTT.publish("vibration_value", concatenatedString.c_str(), 2);
            
      // Reinicie o índice do buffer para 0
      bufferIndex = 0;
    }
  }
}

void keepConnections() {
  connectWiFi();
  connectMQTT();
  MQTT.loop();
}

void connectMQTT() {
  while (!MQTT.connected()) {
    Serial.print("Conectando ao Broker MQTT: ");
    Serial.println(mqttServer);

    if (MQTT.connect(clientId)) {
      Serial.println("Conectado ao Broker com sucesso!");
      subscribeTopics();
    } else {
      Serial.println("A conexão ao broker não pôde ser estabelecida! Faremos uma nova tentativa em 5 segundos.");
      delay(5000);
    }
  }
}

void subscribeTopics() {
  for (char* topic : topics) {
    MQTT.subscribe(topic);
  }
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED)
    return;

  Serial.print("Conectando-se na rede...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
    delay(10);

  Serial.println();
  Serial.print("Conectado com sucesso, na rede: ");
  Serial.println(ssid);
}

void receivePackage(char* topic, byte* payload, unsigned int length) {
  String msg;

  for (int i = 0; i < length; i++) {
    char c = (char)payload[i];
    msg += c;
  }

  String topicString = (String)topic;

  Serial.print(topicString + ": ");
  Serial.println(msg);

  if (topicString == "on_off") {
    if (msg == "true")
      on_off = true;
    else {
      on_off = false;
      selectedAxis = 0; // Desliga a transmissão quando on_off é falso
    }
    Serial.println(on_off);
  }

  if (topicString == "axle") {
    int axleValue = msg.toInt();

    if (axleValue >= 1 && axleValue <= 3) {
      selectedAxis = axleValue; // Define o eixo selecionado com base no valor recebido
    }
  }
}
