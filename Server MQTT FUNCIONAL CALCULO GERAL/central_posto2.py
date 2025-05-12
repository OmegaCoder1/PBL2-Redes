import paho.mqtt.client as mqtt
import logging
import time
import json
import requests
import random
import string
import math
from datetime import datetime
from flask import Flask, jsonify

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Flask
app = Flask(__name__)

# Constantes
BATERIA_INICIAL = 100  # Bateria inicial em porcentagem
BATERIA_MINIMA = 20    # Bateria mínima para solicitar reserva
UNIDADES_POR_PORCENTAGEM = 10  # Unidades que o carro pode percorrer por 1% de bateria

# Ranges de geração de postos para esta central
X_MIN = -500
X_MAX = 0
Y_MIN = -1000
Y_MAX = 1000

# Dicionário global para armazenar os postos desta central
postos_central = {}

def calcular_distancia(x1, y1, x2, y2):
    """Calcula a distância Euclidiana entre dois pontos."""
    distancia = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distancia

def calcular_ponto_parada(x_inicial, y_inicial, x_destino, y_destino, bateria_atual):
    """
    Calcula o ponto onde o carro estará quando atingir a bateria mínima.
    Retorna as coordenadas (x, y) do ponto de parada.
    """
    distancia_total = calcular_distancia(x_inicial, y_inicial, x_destino, y_destino)
    distancia_percorrida = (bateria_atual - BATERIA_MINIMA) * UNIDADES_POR_PORCENTAGEM
    
    if distancia_percorrida >= distancia_total:
        return x_destino, y_destino
    
    # Calcula a proporção da distância percorrida
    proporcao = distancia_percorrida / distancia_total
    
    # Calcula o ponto de parada
    x_parada = x_inicial + (x_destino - x_inicial) * proporcao
    y_parada = y_inicial + (y_destino - y_inicial) * proporcao
    
    return x_parada, y_parada

def encontrar_posto_mais_proximo(x, y, postos_disponiveis):
    """
    Encontra o posto mais próximo baseado no tempo de espera e distância.
    Retorna o nome do posto e seus dados.
    """
    posto_mais_proximo = None
    menor_tempo = float('inf')
    
    for nome_posto, dados_posto in postos_disponiveis.items():
        tempo_espera = len(dados_posto["queue"]) * 120
        distancia = calcular_distancia(x, y, dados_posto["x"], dados_posto["y"])
        tempo_total = tempo_espera + distancia
        
        if tempo_total < menor_tempo:
            menor_tempo = tempo_total
            posto_mais_proximo = (nome_posto, dados_posto)
    
    return posto_mais_proximo

def gerar_codigo_aleatorio(tamanho=6):
    """Gera um código aleatório de tamanho especificado."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(tamanho))

def inicializar_postos_ficticios(num_postos=4):
    """Inicializa o dicionário com postos fictícios."""
    global postos_central
    
    # Limpa o dicionário se já existir
    postos_central = {}
    
    # Gera postos fictícios
    for i in range(num_postos):
        # Gera coordenadas aleatórias dentro do range definido
        x = round(random.uniform(X_MIN, X_MAX), 2)
        y = round(random.uniform(Y_MIN, Y_MAX), 2)
        
        # Gera nome do posto
        timestamp = int(time.time())
        random_code = gerar_codigo_aleatorio()
        nome_posto = f"Posto_Central2_{timestamp}_{random_code}"
        
        # Adiciona o posto ao dicionário
        postos_central[nome_posto] = {
            "x": x,
            "y": y,
            "ocupado": False,
            "tempo_expiracao": {},
            "id": None,
            "queue": []
        }
        
        logger.info(f"Posto fictício criado: {nome_posto} em ({x}, {y})")
    
    logger.info(f"Total de {len(postos_central)} postos fictícios inicializados")
    return postos_central

# Rota Flask para retornar o dicionário de postos
@app.route('/postos', methods=['GET'])
def get_postos():
    return jsonify(postos_central)

# Configuração do cliente MQTT
client = mqtt.Client()

# Callback quando um cliente se conecta
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Conectado ao broker MQTT local")
        # Inscrevendo no tópico de reservas
        client.subscribe("Solicitar/Reserva")
        logger.info("Inscrito no tópico: Solicitar/Reserva")
    else:
        logger.error(f"Falha na conexão, código de retorno: {rc}")

# Callback quando uma mensagem é recebida
def on_message(client, userdata, msg):
    try:
        logger.info(f"Mensagem recebida no tópico {msg.topic}")
        payload = msg.payload.decode()
        logger.info(f"Payload recebido: {payload}")
        
        # Tenta converter para JSON
        try:
            dados = json.loads(payload)
            logger.info(f"""
            ===== Nova Solicitação de Reserva =====
            De: Cliente ID {dados.get('cliente_id', 'N/A')}
            Origem: ({dados.get('x_inicial', 'N/A')}, {dados.get('y_inicial', 'N/A')})
            Destino: ({dados.get('x_destino', 'N/A')}, {dados.get('y_destino', 'N/A')})
            Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dados.get('timestamp', 0)))}
            ======================================
            """)
            
            # Extrai as coordenadas
            x_inicial = float(dados.get('x_inicial'))
            y_inicial = float(dados.get('y_inicial'))
            x_destino = float(dados.get('x_destino'))
            y_destino = float(dados.get('y_destino'))
            
            # Dicionário para armazenar todos os postos disponíveis
            todos_postos = {}
            
            # Adiciona os postos desta central
            todos_postos.update(postos_central)
            logger.info(f"Postos desta central: {len(postos_central)}")
            
            # Faz requisições para os outros servidores
            try:
                # Requisição para o servidor 1
                response1 = requests.get("http://localhost:5000/postos", timeout=5)
                if response1.status_code == 200:
                    postos_servidor1 = response1.json()
                    todos_postos.update(postos_servidor1)
                    logger.info(f"Postos do servidor 1 adicionados: {len(postos_servidor1)}")
                
                # Requisição para o servidor 3
                response3 = requests.get("http://localhost:5002/postos", timeout=5)
                if response3.status_code == 200:
                    postos_servidor3 = response3.json()
                    todos_postos.update(postos_servidor3)
                    logger.info(f"Postos do servidor 3 adicionados: {len(postos_servidor3)}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro ao fazer requisição para outros servidores: {e}")
            
            logger.info(f"Total de postos disponíveis: {len(todos_postos)}")
            
            if len(todos_postos) == 0:
                logger.error("Nenhum posto disponível para cálculo da rota")
                resposta = {
                    "cliente_id": dados.get('cliente_id'),
                    "postos_reservados": [],
                    "status": "erro",
                    "mensagem": "Nenhum posto disponível para cálculo da rota",
                    "timestamp": time.time()
                }
                client.publish("Resposta/Reserva", json.dumps(resposta))
                return
            
            # Lista para armazenar os postos que serão reservados
            postos_reservados = []
            detalhes_rota = []
            
            # Ponto atual do carro
            x_atual = x_inicial
            y_atual = y_inicial
            bateria_atual = BATERIA_INICIAL
            
            while True:
                # Calcula a distância até o destino
                distancia_restante = calcular_distancia(x_atual, y_atual, x_destino, y_destino)
                logger.info(f"Distância restante até o destino: {distancia_restante:.2f} unidades")
                logger.info(f"Bateria atual: {bateria_atual}%")
                
                # Verifica se pode chegar ao destino com a bateria atual
                distancia_maxima = (bateria_atual - BATERIA_MINIMA) * UNIDADES_POR_PORCENTAGEM
                logger.info(f"Distância máxima possível com bateria atual: {distancia_maxima:.2f} unidades")
                
                if distancia_restante <= distancia_maxima:
                    logger.info("Rota calculada com sucesso! Pode chegar ao destino sem paradas adicionais.")
                    detalhes_rota.append({
                        "tipo": "destino",
                        "x": x_destino,
                        "y": y_destino,
                        "bateria_restante": bateria_atual - (distancia_restante / UNIDADES_POR_PORCENTAGEM)
                    })
                    break
                
                # Calcula o ponto onde o carro estará com 20% de bateria
                x_parada, y_parada = calcular_ponto_parada(x_atual, y_atual, x_destino, y_destino, bateria_atual)
                logger.info(f"Ponto de parada calculado: ({x_parada:.2f}, {y_parada:.2f})")
                
                # Encontra o posto mais próximo desse ponto
                posto_mais_proximo = encontrar_posto_mais_proximo(x_parada, y_parada, todos_postos)
                
                if posto_mais_proximo is None:
                    logger.error("Não foi possível encontrar um posto adequado para a rota")
                    resposta = {
                        "cliente_id": dados.get('cliente_id'),
                        "postos_reservados": postos_reservados,
                        "status": "erro",
                        "mensagem": "Não foi possível encontrar um posto adequado para completar a rota",
                        "detalhes_rota": detalhes_rota,
                        "timestamp": time.time()
                    }
                    client.publish("Resposta/Reserva", json.dumps(resposta))
                    return
                
                nome_posto, dados_posto = posto_mais_proximo
                distancia_posto = calcular_distancia(x_parada, y_parada, dados_posto["x"], dados_posto["y"])
                logger.info(f"Posto mais próximo encontrado: {nome_posto} em ({dados_posto['x']}, {dados_posto['y']})")
                logger.info(f"Distância até o posto: {distancia_posto:.2f} unidades")
                
                postos_reservados.append(nome_posto)
                detalhes_rota.append({
                    "tipo": "posto",
                    "nome": nome_posto,
                    "x": dados_posto["x"],
                    "y": dados_posto["y"],
                    "tempo_espera": len(dados_posto["queue"]) * 120,
                    "bateria_chegada": BATERIA_MINIMA
                })
                
                # Atualiza a posição atual e a bateria
                x_atual = dados_posto["x"]
                y_atual = dados_posto["y"]
                bateria_atual = BATERIA_INICIAL
                
                # Remove o posto da lista de disponíveis para evitar duplicatas
                todos_postos.pop(nome_posto, None)
            
            # Publica a resposta com os postos reservados
            resposta = {
                "cliente_id": dados.get('cliente_id'),
                "postos_reservados": postos_reservados,
                "status": "sucesso",
                "mensagem": "Rota calculada com sucesso",
                "detalhes_rota": detalhes_rota,
                "timestamp": time.time()
            }
            
            client.publish("Resposta/Reserva", json.dumps(resposta))
            logger.info(f"Resposta publicada: {resposta}")
            
        except json.JSONDecodeError:
            logger.error("Erro ao decodificar o JSON da mensagem")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")

# Callback quando uma mensagem é publicada
def on_publish(client, userdata, mid):
    logger.info(f"Mensagem publicada com ID: {mid}")

# Callback quando uma mensagem é entregue
def on_message_delivered(client, userdata, mid):
    logger.info(f"Mensagem entregue com ID: {mid}")

# Registrando os callbacks
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_message_delivered = on_message_delivered

# Inicializa os postos fictícios
inicializar_postos_ficticios()

# Conectando ao broker
if __name__ == "__main__":
    try:
        # Conectando ao broker local
        logger.info("Conectando ao broker MQTT local...")
        client.connect("localhost", 1883, 60)  # Usando a porta 1883
        
        # Iniciando o loop de eventos MQTT em uma thread separada
        client.loop_start()
        
        # Iniciando o servidor Flask
        logger.info("""
        ============================================
        Servidor Central 2 Iniciado
        Flask rodando na porta 5001
        MQTT escutando no tópico: Solicitar/Reserva
        Broker: localhost:1883
        ============================================
        """)
        app.run(host='0.0.0.0', port=5001)
        
    except KeyboardInterrupt:
        logger.info("Servidor Central 2 encerrado pelo usuário.")
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor: {e}")
    finally:
        client.disconnect()