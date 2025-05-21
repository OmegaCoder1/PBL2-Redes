import paho.mqtt.client as mqtt
import json
from datetime import datetime
import time

# Configuração do cliente MQTT
client = mqtt.Client()

# Conectar ao broker
client.connect("localhost", 1884)  # Usando a porta do primeiro broker

# Criar uma resposta de erro simulada
resposta_erro = {
    "cliente_id": "teste_erro_001",
    "status": "erro",
    "mensagem": "Não foi possível calcular a rota devido a bateria insuficiente",
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "detalhes_erro": {
        "codigo": "BAT_001",
        "descricao": "Bateria atual (15%) insuficiente para chegar ao destino",
        "bateria_atual": 15,
        "bateria_minima_necessaria": 45
    }
}

# Publicar a resposta no tópico
client.publish("Resposta/Reserva", json.dumps(resposta_erro))

print("Resposta de erro publicada:")
print(json.dumps(resposta_erro, indent=2))

# Aguardar um pouco para garantir que a mensagem seja enviada
time.sleep(1)

# Desconectar do broker
client.disconnect() 