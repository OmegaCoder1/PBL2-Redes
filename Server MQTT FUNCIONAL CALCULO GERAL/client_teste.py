import paho.mqtt.client as mqtt
import logging
import time
import json
import random

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lista de portas dos brokers
portas_brokers = [1883, 1884, 1885]

# Escolhe uma porta aleatória
porta_escolhida = random.choice(portas_brokers)
logger.info(f"Conectando ao broker na porta {porta_escolhida}")

# Configuração do cliente MQTT
client = mqtt.Client()

# Callback quando um cliente se conecta
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Conectado ao broker na porta {porta_escolhida}")
        
        # Cria uma mensagem de teste
        mensagem = {
            "cliente_id": "cliente_teste",
            "data": "2024-03-20",
            "servico": "teste",
            "timestamp": int(time.time())
        }
        
        # Publica a mensagem no tópico
        client.publish("Solicitar/Reserva", json.dumps(mensagem))
        logger.info(f"Mensagem publicada no tópico 'Solicitar/Reserva': {mensagem}")
        
        # Desconecta após publicar
        client.disconnect()
    else:
        logger.error(f"Falha na conexão, código de retorno: {rc}")

# Registrando o callback
client.on_connect = on_connect

# Conectando ao broker
if __name__ == "__main__":
    try:
        # Conectando ao broker local
        logger.info("Conectando ao broker MQTT local...")
        client.connect("localhost", porta_escolhida, 60)
        
        # Iniciando o loop de eventos
        client.loop_forever()
        
    except KeyboardInterrupt:
        logger.info("Cliente de teste encerrado pelo usuário.")
    except Exception as e:
        logger.error(f"Erro ao iniciar o cliente: {e}")
    finally:
        client.disconnect() 