import cv2
import numpy as np
import paho.mqtt.client as mqtt
import threading

# ... (Configurações iniciais e captura de vídeo)
tamanho_real_objeto_mm = 40
focal_length = 6700

# Função para calcular a distância com base no tamanho da bolinha na imagem
def calcular_distancia(tamanho_objeto_pixels):
    distancia_mm = (tamanho_real_objeto_mm * focal_length) / tamanho_objeto_pixels
    return distancia_mm

# Configurações do MQTT Broker
broker_address = "localhost"  # Substitua pelo endereço do seu broker MQTT
port = 1884
topics = ["on_off", "controller", "reference"]  # Substitua pelo tópico que você deseja usar
client_id = "camera"  # Escolha um ID de mqtt_client único

def on_message(client, userdata, message):
    mensagem = message.payload.decode("utf-8")
    print(f"Mensagem Recebida no Tópico '{message.topic}': {mensagem}")

# Crie um cliente MQTT
mqtt_client = mqtt.Client(client_id)

mqtt_client.on_message = on_message

mqtt_client.connect(broker_address, port, 60)

for topic in topics:
    mqtt_client.subscribe(topic)

def processar_video():
    # Capturar vídeo da câmera (0 é a câmera padrão)
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Converta a imagem para o espaço de cores HSV para detectar a bolinha azul
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Defina os limites de cor para a bolinha azul (esses valores podem variar)
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([130, 255, 255])

        # Crie uma máscara para a cor azul
        mask = cv2.inRange(hsv, lower_blue, upper_blue)

        # Encontre os contornos na máscara
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        maior_contorno = None
        maior_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < 100:
                continue

            if area > maior_area:
                maior_area = area
                maior_contorno = contour

        if maior_contorno is not None:
            M = cv2.moments(maior_contorno)
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            tamanho_objeto_pixels = np.sqrt(maior_area)
            distancia = 50 - (calcular_distancia(tamanho_objeto_pixels) / 100)

            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, f'Distancia: {distancia:.2f} cm', (cx - 50, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # Enviar a distância via MQTT
            distancia_str = f'{distancia:.2f}'  # Sem quebra de linha para o MQTT
            mqtt_client.publish("distancia_camera", distancia_str, qos=2)  # Publicar a distância no tópico MQTT

        cv2.imshow('Medição de Distância', frame)
      
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


# Inicie a thread para processar o vídeo
video_thread = threading.Thread(target=processar_video)
video_thread.daemon = True
video_thread.start()

# Inicie o loop MQTT
mqtt_client.loop_forever()