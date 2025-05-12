import paho.mqtt.client as mqtt
import json
import time
import random
import logging
from datetime import datetime

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClienteMQTT:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback chamado quando o cliente se conecta ao broker."""
        if rc == 0:
            logger.info("Conectado ao broker MQTT com sucesso")
            # Inscreve no tópico de respostas
            client.subscribe("Resposta/Reserva")
            logger.info("Inscrito no tópico: Resposta/Reserva")
        else:
            logger.error(f"Falha na conexão. Código de retorno: {rc}")
            
    def on_message(self, client, userdata, msg):
        """Callback chamado quando uma mensagem é recebida."""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"""
            ===== Resposta Recebida =====
            Tópico: {msg.topic}
            Status: {payload.get('status', 'N/A')}
            Mensagem: {payload.get('mensagem', 'N/A')}
            Postos Reservados: {payload.get('postos_reservados', [])}
            Detalhes da Rota: {payload.get('detalhes_rota', [])}
            ============================
            """)
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            
    def on_publish(self, client, userdata, mid):
        """Callback chamado quando uma mensagem é publicada."""
        logger.info(f"Mensagem publicada com ID: {mid}")
        
    def on_disconnect(self, client, userdata, rc):
        """Callback chamado quando o cliente se desconecta."""
        if rc != 0:
            logger.warning("Desconexão inesperada do broker")
        else:
            logger.info("Desconectado do broker")
            
    def gerar_coordenadas(self):
        """Gera coordenadas aleatórias para origem e destino."""
        origem = {
            "x": -3000,
            "y": -3000
        }
        destino = {
            "x": 3000,
            "y": 3000
        }
        return origem, destino
        
    def enviar_solicitacao(self):
        """Envia uma solicitação de reserva para o servidor."""
        try:
            # Gera coordenadas aleatórias
            origem, destino = self.gerar_coordenadas()
            
            # Gera ID do cliente
            cliente_id = f"cliente_{int(time.time())}"
            
            # Prepara a mensagem
            mensagem = {
                "tipo": "solicitar_reserva",
                "cliente_id": cliente_id,
                "origem": origem,
                "destino": destino,
                "bateria_atual": 100  # Bateria inicial em porcentagem
            }
            
            # Publica a mensagem
            self.client.publish("Solicitar/Reserva", json.dumps(mensagem))
            logger.info(f"""
            ===== Solicitação Enviada =====
            Cliente ID: {cliente_id}
            Origem: ({origem['x']}, {origem['y']})
            Destino: ({destino['x']}, {destino['y']})
            Bateria: 100%
            ============================
            """)
            
        except Exception as e:
            logger.error(f"Erro ao enviar solicitação: {e}")
            
    def iniciar(self):
        """Inicia o cliente MQTT e envia uma solicitação."""
        try:
            # Conecta ao broker
            self.client.connect("localhost", 1883, 60)
            self.client.loop_start()
            
            # Envia a solicitação
            self.enviar_solicitacao()
            
            # Aguarda um tempo para receber a resposta
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Erro durante a execução: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    cliente = ClienteMQTT()
    cliente.iniciar() 