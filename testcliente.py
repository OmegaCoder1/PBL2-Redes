import paho.mqtt.client as mqtt
import json
import time
import random
import logging
from datetime import datetime

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lista de portas disponíveis
PORTAS_MQTT = [1884, 1885, 1886]

# Variável global para armazenar a resposta
resposta_recebida = None
resposta_recebida_event = None

def on_connect(client, userdata, flags, rc):
    """Callback quando conecta ao broker."""
    if rc == 0:
        logger.info(f"Conectado ao broker MQTT na porta {client._port}")
        # Inscreve no tópico de resposta na mesma porta
        client.subscribe("Resposta/Reserva")
        logger.info(f"Inscrito no tópico: Resposta/Reserva na porta {client._port}")
    else:
        logger.error(f"Falha na conexão, código de retorno: {rc}")

def on_message(client, userdata, msg):
    """Callback quando recebe uma mensagem."""
    global resposta_recebida, resposta_recebida_event
    
    try:
        dados = json.loads(msg.payload.decode())
        logger.info(f"Mensagem recebida na porta {client._port}: {dados}")
        
        # Verifica se a resposta é para este cliente
        if dados.get('cliente_id') == client._client_id:
            resposta_recebida = dados
            if resposta_recebida_event:
                resposta_recebida_event.set()
    except json.JSONDecodeError:
        logger.error("Erro ao decodificar mensagem JSON")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")

def formatar_resposta(dados):
    """Formata a resposta para exibição no terminal."""
    if not dados or dados.get('status') != 'sucesso':
        return "Erro ao processar a requisição"
    
    print("\n=== ROTA CALCULADA ===")
    print(f"Status: {dados['status']}")
    print(f"Mensagem: {dados['mensagem']}")
    print("\nPostos Reservados:")
    
    for i, posto in enumerate(dados['detalhes_rota'], 1):
        if posto['tipo'] == 'posto':
            print(f"\n{i}. Posto: {posto['nome']}")
            print(f"   Coordenadas: ({posto['x']}, {posto['y']})")
            print(f"   Bateria na chegada: {posto['bateria_chegada']}%")
            print(f"   Horário de chegada: {posto['horario_chegada']}")
    
    # Exibe informações do destino final
    destino = dados['detalhes_rota'][-1]
    print(f"\nDestino Final:")
    print(f"Coordenadas: ({destino['x']}, {destino['y']})")
    print(f"Bateria restante: {destino['bateria_restante']:.2f}%")
    print(f"Horário de chegada: {destino['horario_chegada']}")
    print("\n=====================")

def main():
    global resposta_recebida_event
    
    # Sorteia uma porta
    porta = random.choice(PORTAS_MQTT)
    logger.info(f"Porta MQTT selecionada: {porta}")
    
    # Cria o cliente MQTT
    client = mqtt.Client()
    client._port = porta  # Armazena a porta no objeto do cliente
    
    # Gera um ID único para o cliente
    client_id = f"cliente_{int(time.time())}"
    client._client_id = client_id
    
    # Configura os callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Conecta ao broker na porta selecionada
        client.connect("localhost", porta, 60)
        client.loop_start()
        
        # Cria o evento para sincronização
        resposta_recebida_event = threading.Event()
        
        # Dados da requisição
        dados = {
            "cliente_id": client_id,
            "origem": {
                "x": -3000,
                "y": -3000
            },
            "destino": {
                "x": 3000,
                "y": 3000
            },
            "bateria_atual": 100
        }
        
        # Publica a mensagem
        client.publish("Solicitar/Reserva", json.dumps(dados))
        logger.info(f"Mensagem publicada para o tópico Solicitar/Reserva na porta {porta}")
        
        # Aguarda a resposta por 2 minutos
        if resposta_recebida_event.wait(timeout=120):
            formatar_resposta(resposta_recebida)
        else:
            print("Timeout: Nenhuma resposta recebida após 2 minutos")
            
    except Exception as e:
        logger.error(f"Erro: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    import threading
    main() 