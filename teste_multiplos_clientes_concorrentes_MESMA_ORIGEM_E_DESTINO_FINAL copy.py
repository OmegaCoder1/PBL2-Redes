import paho.mqtt.client as mqtt
import json
import time
import random
import logging
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import math

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lista de portas disponíveis
PORTAS_MQTT = [1884, 1885, 1886]
MAX_TENTATIVAS = 3

# Dicionário para armazenar as respostas de cada cliente
respostas = {}
respostas_lock = threading.Lock()

def calcular_distancia(ponto1, ponto2):
    """Calcula a distância euclidiana entre dois pontos."""
    return math.sqrt((ponto2['x'] - ponto1['x'])**2 + (ponto2['y'] - ponto1['y'])**2)

def gerar_coordenadas():
    """Gera coordenadas aleatórias dentro dos ranges especificados."""
    x = random.randint(-3000, 3000)
    y = random.randint(-3000, 3000)
    return {"x": x, "y": y}

def on_connect(client, userdata, flags, rc):
    """Callback quando conecta ao broker."""
    if rc == 0:
        logger.info(f"Cliente {client._client_id} conectado ao broker MQTT na porta {client._port}")
        client.subscribe("Resposta/Reserva")
        logger.info(f"Cliente {client._client_id} inscrito no tópico: Resposta/Reserva na porta {client._port}")
    else:
        logger.error(f"Cliente {client._client_id} falha na conexão, código de retorno: {rc}")

def on_message(client, userdata, msg):
    """Callback quando recebe uma mensagem."""
    try:
        dados = json.loads(msg.payload.decode())
        logger.info(f"Cliente {client._client_id} recebeu mensagem na porta {client._port}")
        logger.info(f"Conteúdo da mensagem: {json.dumps(dados, indent=2)}")
        
        # Verifica se a resposta é para este cliente
        if dados.get('cliente_id') == client._client_id:
            with respostas_lock:
                respostas[client._client_id] = dados
                logger.info(f"Cliente {client._client_id} recebeu resposta: {dados['status']}")
    except json.JSONDecodeError:
        logger.error(f"Cliente {client._client_id} erro ao decodificar mensagem JSON")
    except Exception as e:
        logger.error(f"Cliente {client._client_id} erro ao processar mensagem: {e}")

def formatar_resposta(dados):
    """Formata a resposta para exibição no terminal."""
    if not dados or dados.get('status') != 'sucesso':
        return f"Erro ao processar a requisição: {dados.get('mensagem', 'Erro desconhecido')}"
    
    resultado = []
    resultado.append("\n=== ROTA CALCULADA ===")
    resultado.append(f"Status: {dados['status']}")
    resultado.append(f"Mensagem: {dados['mensagem']}")
    resultado.append("\nPostos Reservados:")
    
    for i, posto in enumerate(dados['detalhes_rota'], 1):
        if posto['tipo'] == 'posto':
            resultado.append(f"\n{i}. Posto: {posto['nome']}")
            resultado.append(f"   Coordenadas: ({posto['x']}, {posto['y']})")
            resultado.append(f"   Bateria na chegada: {posto['bateria_chegada']}%")
            resultado.append(f"   Horário de chegada: {posto['horario_chegada']}")
    
    # Exibe informações do destino final
    destino = dados['detalhes_rota'][-1]
    resultado.append(f"\nDestino Final:")
    resultado.append(f"Coordenadas: ({destino['x']}, {destino['y']})")
    resultado.append(f"Bateria restante: {destino['bateria_restante']:.2f}%")
    resultado.append(f"Horário de chegada: {destino['horario_chegada']}")
    resultado.append("\n=====================")
    
    return "\n".join(resultado)

def tentar_conexao(porta, client_id):
    """Tenta conectar ao broker MQTT na porta especificada."""
    try:
        client = mqtt.Client()
        client._port = porta
        client._client_id = client_id
        
        # Configura os callbacks
        client.on_connect = on_connect
        client.on_message = on_message
        
        # Conecta ao broker
        client.connect("localhost", porta, 60)
        client.loop_start()
        return client
    except Exception as e:
        logger.error(f"Cliente {client_id} erro ao conectar na porta {porta}: {str(e)}")
        return None

def executar_cliente(client_id, bateria, origem, destino):
    """Executa um cliente individual com origem, destino e bateria pré-definidos."""
    # Embaralha a lista de portas para tentar em ordem aleatória
    portas_disponiveis = PORTAS_MQTT.copy()
    random.shuffle(portas_disponiveis)
    
    # Usa as coordenadas fornecidas
    dados = {
        "cliente_id": client_id,
        "origem": origem,
        "destino": destino,
        "bateria_atual": bateria
    }
    
    logger.info(f"Cliente {client_id} - Dados:")
    logger.info(f"Origem: ({origem['x']}, {origem['y']})")
    logger.info(f"Destino: ({destino['x']}, {destino['y']})")
    logger.info(f"Bateria atual: {dados['bateria_atual']}%")
    
    # Tenta conectar em cada porta
    for tentativa in range(MAX_TENTATIVAS):
        for porta in portas_disponiveis:
            logger.info(f"Cliente {client_id} - Tentativa {tentativa + 1}: Tentando conectar na porta {porta}")
            client = tentar_conexao(porta, client_id)
            
            if client:
                try:
                    # Publica a mensagem
                    client.publish("Solicitar/Reserva", json.dumps(dados))
                    logger.info(f"Cliente {client_id} publicou mensagem para o tópico Solicitar/Reserva na porta {porta}")
                    
                    # Aguarda a resposta por 2 minutos
                    inicio = time.time()
                    while time.time() - inicio < 120:
                        with respostas_lock:
                            if client_id in respostas:
                                resposta = respostas[client_id]
                                print(f"\nResposta para Cliente {client_id}:")
                                print(formatar_resposta(resposta))
                                client.loop_stop()
                                client.disconnect()
                                return
                        time.sleep(0.1)
                    
                    logger.warning(f"Cliente {client_id} timeout: Nenhuma resposta recebida após 2 minutos")
                    client.loop_stop()
                    client.disconnect()
                except Exception as e:
                    logger.error(f"Cliente {client_id} erro ao publicar mensagem: {str(e)}")
                    client.loop_stop()
                    client.disconnect()
        
        if tentativa < MAX_TENTATIVAS - 1:
            logger.info(f"Cliente {client_id} aguardando 2 segundos antes da próxima tentativa...")
            time.sleep(2)
    
    logger.error(f"Cliente {client_id} todas as tentativas de conexão falharam")

def main():
    # Número de usuários a serem simulados
    num_usuarios = int(input("Digite o número de usuários a serem simulados: "))
    
    # Coordenadas fixas para todos os usuários
    origem = {"x": -3000, "y": -3000}
    destino = {"x": 3000, "y": 3000}
    
    print(f"\nCoordenadas para todos os usuários:")
    print(f"Origem: ({origem['x']}, {origem['y']})")
    print(f"Destino: ({destino['x']}, {destino['y']})")
    
    # Lista para armazenar as threads
    threads = []
    
    # Cria e inicia as threads para cada usuário
    with ThreadPoolExecutor(max_workers=num_usuarios) as executor:
        for i in range(num_usuarios):
            # Gera um ID único para cada usuário
            cliente_id = f"cliente_{i+1}"
            # Gera um nível de bateria aleatório entre 20 e 100
            bateria = random.randint(20, 100)
            
            # Inicia a thread para este usuário
            executor.submit(executar_cliente, cliente_id, bateria, origem, destino)

if __name__ == "__main__":
    main() 