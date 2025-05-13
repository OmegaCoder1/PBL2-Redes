import paho.mqtt.client as mqtt
import logging
import time
import json
import requests
import random
import string
import math
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from threading import Lock, Condition
from flask_cors import CORS

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Locks para controle de concorrência
lock = Lock()  # Lock principal
cond = Condition(lock)  # Condição para sincronização
leitores = 0  # Contador de leitores
escritor = False  # Flag indicando se há escritor ativo

# Constantes
BATERIA_INICIAL = 100  # Bateria inicial em porcentagem
BATERIA_MINIMA = 20    # Bateria mínima para solicitar reserva
UNIDADES_POR_PORCENTAGEM = 10  # Unidades que o carro pode percorrer por 1% de bateria
TEMPO_BATERIA_TOTAL = 3 * 60 * 60  # 3 horas em segundos

# Ranges de geração de postos para esta central
X_MIN = -1000
X_MAX = 0
Y_MIN = -1000
Y_MAX = 0

# Dicionário global para armazenar os postos desta central
postos_central = {}

def adquirir_lock_leitura():
    """Adquire o lock para leitura."""
    global leitores
    with lock:
        while escritor:  # Espera se houver escritor ativo
            cond.wait()
        leitores += 1

def liberar_lock_leitura():
    """Libera o lock de leitura."""
    global leitores
    with lock:
        leitores -= 1
        if leitores == 0:
            cond.notify_all()  # Notifica escritores em espera

def adquirir_lock_escrita():
    """Adquire o lock para escrita."""
    global escritor
    with lock:
        while escritor or leitores > 0:  # Espera se houver escritor ou leitores
            cond.wait()
        escritor = True

def liberar_lock_escrita():
    """Libera o lock de escrita."""
    global escritor
    with lock:
        escritor = False
        cond.notify_all()  # Notifica todos os leitores e escritores em espera

def calcular_distancia(x1, y1, x2, y2):
    """Calcula a distância Euclidiana entre dois pontos."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def calcular_tempo_viagem(distancia, bateria_gasta):
    """Calcula o tempo de viagem baseado na distância e bateria gasta."""
    # Velocidade média do veículo (unidades por segundo)
    VELOCIDADE_MEDIA = 10  # unidades por segundo
    
    # Tempo baseado na distância e velocidade
    tempo_segundos = distancia / VELOCIDADE_MEDIA
    
    # Adiciona tempo de carregamento (5 minutos = 300 segundos)
    tempo_segundos += 300
    
    return tempo_segundos

def calcular_horario_chegada(horario_saida, tempo_viagem):
    """Calcula o horário de chegada baseado no horário de saída e tempo de viagem."""
    horario_chegada = horario_saida + timedelta(seconds=tempo_viagem)
    return horario_chegada

def calcular_tempo_espera(posto):
    """Calcula o tempo de espera baseado nas reservas existentes."""
    if not posto['reservas']:
        return 0  # Sem reservas, sem espera
        
    # Ordena as reservas por horário
    reservas_ordenadas = sorted(posto['reservas'], key=lambda x: x['horario'])
    
    # Encontra o primeiro horário disponível após a última reserva
    ultima_reserva = reservas_ordenadas[-1]
    horario_reserva = datetime.strptime(ultima_reserva['horario'], "%Y-%m-%d %H:%M:%S")
    tempo_espera = (horario_reserva - datetime.now()).total_seconds()
    
    return max(0, tempo_espera)  # Retorna 0 se o tempo de espera for negativo

def encontrar_posto_mais_proximo(x, y, postos_disponiveis, bateria_atual):
    """
    Encontra o posto mais próximo baseado no tempo de espera e distância.
    Retorna o nome do posto e seus dados.
    """
    posto_mais_proximo = None
    menor_tempo = float('inf')
    
    # Usa apenas a bateria mínima (20%) para calcular a distância máxima
    distancia_maxima = BATERIA_MINIMA * UNIDADES_POR_PORCENTAGEM
    
    logger.info(f"Procurando posto mais próximo de ({x}, {y}) com distância máxima de {distancia_maxima:.2f} unidades")
    
    # Lista para armazenar postos candidatos
    postos_candidatos = []
    
    for nome_posto, dados_posto in postos_disponiveis.items():
        tempo_espera = calcular_tempo_espera(dados_posto)
        distancia = calcular_distancia(x, y, dados_posto["x"], dados_posto["y"])
        
        # Verifica se o posto está dentro do alcance da bateria
        if distancia <= distancia_maxima:
            tempo_total = tempo_espera + distancia
            
            logger.info(f"""
            Analisando posto {nome_posto}:
            - Posição: ({dados_posto['x']}, {dados_posto['y']})
            - Distância até o posto: {distancia:.2f} unidades
            - Bateria necessária: {distancia/UNIDADES_POR_PORCENTAGEM:.2f}%
            - Tempo de espera: {tempo_espera:.2f} segundos
            - Tempo total: {tempo_total:.2f} segundos
            """)
            
            # Adiciona o posto à lista de candidatos
            postos_candidatos.append({
                "nome": nome_posto,
                "dados": dados_posto,
                "distancia": distancia,
                "tempo_total": tempo_total
            })
    
    # Ordena os candidatos por distância
    postos_candidatos.sort(key=lambda x: x["distancia"])
    
    # Escolhe o melhor posto (mais próximo)
    if postos_candidatos:
        melhor_posto = postos_candidatos[0]  # Pega o mais próximo
        posto_mais_proximo = (melhor_posto["nome"], melhor_posto["dados"])
        logger.info(f"Posto escolhido: {melhor_posto['nome']} com tempo total de {melhor_posto['tempo_total']:.2f} segundos")
    else:
        logger.info("Nenhum posto adequado encontrado dentro do alcance")
    
    return posto_mais_proximo

def calcular_ponto_parada(x_inicial, y_inicial, x_destino, y_destino, bateria_atual):
    """
    Calcula o ponto onde o carro estará quando atingir a bateria mínima.
    Retorna as coordenadas (x, y) do ponto de parada.
    """
    distancia_total = calcular_distancia(x_inicial, y_inicial, x_destino, y_destino)
    distancia_percorrida = (bateria_atual - BATERIA_MINIMA) * UNIDADES_POR_PORCENTAGEM
    
    logger.info(f"""
    ===== Cálculo do Ponto de Parada =====
    Posição Inicial: ({x_inicial}, {y_inicial})
    Destino Final: ({x_destino}, {y_destino})
    Distância Total: {distancia_total:.2f} unidades
    Bateria Atual: {bateria_atual}%
    Distância que pode percorrer: {distancia_percorrida:.2f} unidades
    """)
    
    if distancia_percorrida >= distancia_total:
        logger.info("Pode chegar ao destino sem parar!")
        return x_destino, y_destino
    
    # Calcula a proporção da distância percorrida
    proporcao = distancia_percorrida / distancia_total
    
    # Calcula o ponto de parada mantendo a mesma direção
    x_parada = x_inicial + (x_destino - x_inicial) * proporcao
    y_parada = y_inicial + (y_destino - y_inicial) * proporcao
    
    # Verifica se a distância real não excede o máximo permitido
    distancia_real = calcular_distancia(x_inicial, y_inicial, x_parada, y_parada)
    
    logger.info(f"""
    Ponto de Parada Calculado:
    Coordenadas: ({x_parada:.2f}, {y_parada:.2f})
    Distância Real Percorrida: {distancia_real:.2f} unidades
    Proporção da Distância: {proporcao:.2f}
    """)
    
    if distancia_real > distancia_percorrida:
        # Ajusta o ponto para garantir que não exceda a distância máxima
        fator_ajuste = distancia_percorrida / distancia_real
        x_parada = x_inicial + (x_parada - x_inicial) * fator_ajuste
        y_parada = y_inicial + (y_parada - y_inicial) * fator_ajuste
        
        distancia_real = calcular_distancia(x_inicial, y_inicial, x_parada, y_parada)
        logger.info(f"""
        Ponto de Parada Ajustado:
        Coordenadas: ({x_parada:.2f}, {y_parada:.2f})
        Distância Real Ajustada: {distancia_real:.2f} unidades
        Fator de Ajuste: {fator_ajuste:.2f}
        """)
    
    return x_parada, y_parada

def gerar_codigo_aleatorio(tamanho=6):
    """Gera um código aleatório de tamanho especificado."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(tamanho))

def inicializar_postos_ficticios(num_postos=5000):
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
        nome_posto = f"Posto_Central3_{timestamp}_{random_code}"
        
        # Adiciona o posto ao dicionário
        postos_central[nome_posto] = {
            "x": x,
            "y": y,
            "ocupado": False,
            "id": None,
            "reservas": []  # Lista de reservas com horários
        }
        
        logger.info(f"""
        ===== Novo Posto Criado =====
        Nome: {nome_posto}
        Posição: ({x}, {y})
        Status: Disponível
        ===========================
        """)
    
    logger.info(f"""
    ===== Postos da Central 1 =====
    Total de postos: {len(postos_central)}
    Postos disponíveis:
    {json.dumps(postos_central, indent=2)}
    ===========================
    """)
    return postos_central

# Rota Flask para retornar o dicionário de postos
@app.route('/postos', methods=['GET'])
def get_postos():
    """Rota para consultar os postos disponíveis."""
    try:
        adquirir_lock_leitura()
        try:
            return jsonify(postos_central)
        finally:
            liberar_lock_leitura()
    except Exception as e:
        logger.error(f"Erro ao consultar postos: {e}")
        return jsonify({
            "status": "erro",
            "mensagem": f"Erro ao consultar postos: {str(e)}"
        }), 500

# Rota Flask para reservar um posto
@app.route('/reservar', methods=['POST'])
def reservar_posto():
    """Rota para reservar um posto."""
    try:
        dados = request.get_json()
        nome_posto = dados.get('nome_posto')
        cliente_id = dados.get('cliente_id')
        horario_reserva = dados.get('horario_reserva')
        
        if not nome_posto or not cliente_id or not horario_reserva:
            return jsonify({
                "status": "erro",
                "mensagem": "Parâmetros 'nome_posto', 'cliente_id' e 'horario_reserva' são obrigatórios"
            }), 400
            
        adquirir_lock_escrita()
        try:
            logger.info(f"Iniciando reserva para o posto {nome_posto} - Cliente {cliente_id}")
            
            # Simula um processamento demorado (5 segundos)
            logger.info("Processando reserva...")
            time.sleep(2)
            
            if nome_posto not in postos_central:
                return jsonify({
                    "status": "erro",
                    "mensagem": f"Posto {nome_posto} não encontrado"
                }), 404
                
            # Verifica se o posto está disponível no horário solicitado
            for reserva in postos_central[nome_posto]["reservas"]:
                if reserva["horario"] == horario_reserva:
                    return jsonify({
                        "status": "erro",
                        "mensagem": f"Posto {nome_posto} já está reservado para o horário {horario_reserva}"
                    }), 409
                
            # Adiciona a reserva
            postos_central[nome_posto]["reservas"].append({
                "cliente_id": cliente_id,
                "horario": horario_reserva
            })
            
            # Se for a primeira reserva, marca como ocupado
            if len(postos_central[nome_posto]["reservas"]) == 1:
                postos_central[nome_posto]["ocupado"] = True
                postos_central[nome_posto]["id"] = cliente_id
            
            logger.info(f"Posto {nome_posto} reservado para o cliente {cliente_id} no horário {horario_reserva}")
            
            return jsonify({
                "status": "sucesso",
                "mensagem": f"Posto {nome_posto} reservado com sucesso para o horário {horario_reserva}",
                "postos": postos_central
            })
        finally:
            liberar_lock_escrita()
            
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {e}")
        return jsonify({
            "status": "erro",
            "mensagem": f"Erro ao processar requisição: {str(e)}"
        }), 500

# Rota Flask para cancelar a reserva de um posto
@app.route('/cancelar', methods=['POST'])
def cancelar_reserva():
    """Rota para cancelar uma reserva."""
    try:
        dados = request.get_json()
        nome_posto = dados.get('nome_posto')
        cliente_id = dados.get('cliente_id')
        horario_reserva = dados.get('horario_reserva')
        
        if not nome_posto or not cliente_id or not horario_reserva:
            return jsonify({
                "status": "erro",
                "mensagem": "Parâmetros 'nome_posto', 'cliente_id' e 'horario_reserva' são obrigatórios"
            }), 400
            
        adquirir_lock_escrita()
        try:
            if nome_posto not in postos_central:
                return jsonify({
                    "status": "erro",
                    "mensagem": f"Posto {nome_posto} não encontrado"
                }), 404
                
            # Procura a reserva específica
            reserva_encontrada = False
            for reserva in postos_central[nome_posto]["reservas"]:
                if reserva["cliente_id"] == cliente_id and reserva["horario"] == horario_reserva:
                    postos_central[nome_posto]["reservas"].remove(reserva)
                    reserva_encontrada = True
                    break
            
            if not reserva_encontrada:
                return jsonify({
                    "status": "erro",
                    "mensagem": f"Reserva não encontrada para o cliente {cliente_id} no horário {horario_reserva}"
                }), 404
                
            # Se não houver mais reservas, marca como desocupado
            if len(postos_central[nome_posto]["reservas"]) == 0:
                postos_central[nome_posto]["ocupado"] = False
                postos_central[nome_posto]["id"] = None
            
            logger.info(f"Reserva do posto {nome_posto} cancelada para o cliente {cliente_id} no horário {horario_reserva}")
            
            return jsonify({
                "status": "sucesso",
                "mensagem": f"Reserva do posto {nome_posto} cancelada com sucesso",
                "postos": postos_central
            })
        finally:
            liberar_lock_escrita()
            
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {e}")
        return jsonify({
            "status": "erro",
            "mensagem": f"Erro ao processar requisição: {str(e)}"
        }), 500

# Rota Flask para adicionar um posto manualmente
@app.route('/adicionar_posto', methods=['POST'])
def adicionar_posto():
    """Rota para adicionar um posto manualmente."""
    try:
        dados = request.get_json()
        
        # Validação dos dados obrigatórios
        if not all(key in dados for key in ['x', 'y']):
            return jsonify({
                "status": "erro",
                "mensagem": "Parâmetros 'x' e 'y' são obrigatórios"
            }), 400
            
        adquirir_lock_escrita()
        try:
            # Gera nome do posto
            timestamp = int(time.time())
            random_code = gerar_codigo_aleatorio()
            nome_posto = f"Posto_Central3_{timestamp}_{random_code}"
            
            # Adiciona o posto ao dicionário mantendo o padrão existente
            postos_central[nome_posto] = {
                "x": float(dados['x']),
                "y": float(dados['y']),
                "ocupado": False,
                "id": None,
                "reservas": []
            }
            
            logger.info(f"""
            ===== Novo Posto Adicionado Manualmente =====
            Nome: {nome_posto}
            Posição: ({dados['x']}, {dados['y']})
            Status: Disponível
            =========================================
            """)
            
            return jsonify({
                "status": "sucesso",
                "mensagem": f"Posto {nome_posto} adicionado com sucesso",
                "posto": postos_central[nome_posto]
            })
            
        finally:
            liberar_lock_escrita()
            
    except Exception as e:
        logger.error(f"Erro ao adicionar posto: {e}")
        return jsonify({
            "status": "erro",
            "mensagem": f"Erro ao adicionar posto: {str(e)}"
        }), 500

# Configuração do cliente MQTT
client = mqtt.Client()

# Callback quando um cliente se conecta
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Conectado ao broker MQTT local")
        # Inscrevendo nos tópicos
        client.subscribe("Solicitar/Reserva")
        client.subscribe("Resposta/Reserva")
        logger.info("Inscrito nos tópicos: Solicitar/Reserva e Resposta/Reserva")
    else:
        logger.error(f"Falha na conexão, código de retorno: {rc}")

# Callback quando uma mensagem é recebida
def on_message(client, userdata, msg):
    try:
        logger.info(f"""
        ===== Nova Mensagem Recebida =====
        Tópico: {msg.topic}
        Payload: {msg.payload.decode()}
        ===============================
        """)
        
        # Só processa mensagens do tópico Solicitar/Reserva
        if msg.topic != "Solicitar/Reserva":
            return
            
        # Tenta converter para JSON
        try:
            dados = json.loads(msg.payload.decode())
            logger.info(f"""
            ===== Nova Solicitação de Reserva =====
            Cliente ID: {dados.get('cliente_id', 'N/A')}
            Origem: ({dados.get('origem', {}).get('x', 'N/A')}, {dados.get('origem', {}).get('y', 'N/A')})
            Destino: ({dados.get('destino', {}).get('x', 'N/A')}, {dados.get('destino', {}).get('y', 'N/A')})
            Bateria: {dados.get('bateria_atual', 'N/A')}%
            ======================================
            """)
            
            # Extrai as coordenadas
            x_inicial = float(dados.get('origem', {}).get('x'))
            y_inicial = float(dados.get('origem', {}).get('y'))
            x_destino = float(dados.get('destino', {}).get('x'))
            y_destino = float(dados.get('destino', {}).get('y'))
            bateria_atual = float(dados.get('bateria_atual'))
            
            # Horário de saída
            horario_saida = datetime.now()
            
            # Dicionário para armazenar todos os postos disponíveis
            todos_postos = {}
            
            # Adiciona os postos desta central
            todos_postos.update(postos_central)
            logger.info(f"""
            ===== Postos Disponíveis =====
            Postos desta central: {len(postos_central)}
            Detalhes dos postos:
            {json.dumps(postos_central, indent=2)}
            ===========================
            """)
            
            # Faz requisições para os outros servidores
            try:
                # Requisição para o servidor 1
                response1 = requests.get("http://localhost:5000/postos", timeout=15)
                if response1.status_code == 200:
                    postos_servidor1 = response1.json()
                    todos_postos.update(postos_servidor1)
                    logger.info(f"""
                    ===== Postos do Servidor 1 =====
                    Total: {len(postos_servidor1)}
                    Detalhes:
                    {json.dumps(postos_servidor1, indent=2)}
                    ===========================
                    """)
                    
                # Requisição para o servidor 2
                response2 = requests.get("http://localhost:5001/postos", timeout=15)
                if response2.status_code == 200:
                    postos_servidor2 = response2.json()
                    todos_postos.update(postos_servidor2)
                    logger.info(f"""
                    ===== Postos do Servidor 2 =====
                    Total: {len(postos_servidor2)}
                    Detalhes:
                    {json.dumps(postos_servidor2, indent=2)}
                    ===========================
                    """)
                
            except requests.exceptions.Timeout:
                logger.error("Timeout ao tentar acessar o servidor")
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro ao fazer requisição para outros servidores: {e}")
            
            logger.info(f"""
            ===== Resumo dos Postos =====
            Total de postos disponíveis: {len(todos_postos)}
            Detalhes de todos os postos:
            {json.dumps(todos_postos, indent=2)}
            ===========================
            """)
            
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
            horario_atual = horario_saida
            
            while True:
                # Calcula a distância até o destino
                distancia_restante = calcular_distancia(x_atual, y_atual, x_destino, y_destino)
                logger.info(f"Distância restante até o destino: {distancia_restante:.2f} unidades")
                logger.info(f"Bateria atual: {bateria_atual}%")
                
                # Verifica se pode chegar ao destino com a bateria atual
                distancia_maxima = (bateria_atual - BATERIA_MINIMA) * UNIDADES_POR_PORCENTAGEM
                logger.info(f"Distância máxima possível com bateria atual: {distancia_maxima:.2f} unidades")
                
                if distancia_restante <= distancia_maxima:
                    logger.info("Pode chegar ao destino sem paradas!")
                    tempo_viagem_final = calcular_tempo_viagem(distancia_restante, distancia_restante/UNIDADES_POR_PORCENTAGEM)
                    horario_chegada_final = calcular_horario_chegada(horario_atual, tempo_viagem_final)
                    detalhes_rota.append({
                        "tipo": "destino",
                        "x": x_destino,
                        "y": y_destino,
                        "bateria_restante": bateria_atual - (distancia_restante / UNIDADES_POR_PORCENTAGEM),
                        "horario_chegada": horario_chegada_final.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    break
                
                # Calcula o ponto onde o carro estará com 20% de bateria
                x_parada, y_parada = calcular_ponto_parada(x_atual, y_atual, x_destino, y_destino, bateria_atual)
                logger.info(f"Ponto de parada calculado: ({x_parada:.2f}, {y_parada:.2f})")
                
                # Encontra o posto mais próximo desse ponto que esteja dentro do alcance
                posto_mais_proximo = encontrar_posto_mais_proximo(x_parada, y_parada, todos_postos, bateria_atual)
                
                if posto_mais_proximo is None:
                    logger.error("Não foi possível encontrar um posto adequado para completar a rota")
                    resposta = {
                        "cliente_id": dados.get('cliente_id'),
                        "postos_reservados": [],
                        "status": "erro",
                        "mensagem": "Não foi possível encontrar um posto adequado para completar a rota",
                        "timestamp": time.time()
                    }
                    client.publish("Resposta/Reserva", json.dumps(resposta))
                    return
                
                nome_posto, dados_posto = posto_mais_proximo
                distancia_posto = calcular_distancia(x_atual, y_atual, dados_posto["x"], dados_posto["y"])
                logger.info(f"Posto mais próximo encontrado: {nome_posto} em ({dados_posto['x']}, {dados_posto['y']})")
                logger.info(f"Distância até o posto: {distancia_posto:.2f} unidades")
                
                # Calcula o tempo de viagem até este posto
                tempo_viagem = calcular_tempo_viagem(distancia_posto, distancia_posto/UNIDADES_POR_PORCENTAGEM)
                horario_chegada = calcular_horario_chegada(horario_atual, tempo_viagem)
                
                postos_reservados.append(nome_posto)
                detalhes_rota.append({
                    "tipo": "posto",
                    "nome": nome_posto,
                    "x": dados_posto["x"],
                    "y": dados_posto["y"],
                    "bateria_chegada": BATERIA_MINIMA,
                    "horario_chegada": horario_chegada.strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Atualiza a posição atual e o horário para o próximo cálculo
                x_atual = dados_posto["x"]
                y_atual = dados_posto["y"]
                bateria_atual = 100  # Bateria recarregada
                horario_atual = horario_chegada
            
            # Tenta reservar todos os postos necessários
            for i, nome_posto in enumerate(postos_reservados):
                try:
                    # Determina qual servidor possui o posto
                    if nome_posto.startswith("Posto_Central1"):
                        url = f"http://localhost:5000/reservar"
                    elif nome_posto.startswith("Posto_Central2"):
                        url = f"http://localhost:5001/reservar"
                    else:
                        url = f"http://localhost:5002/reservar"
                    
                    # Obtém o horário de chegada deste posto
                    horario_chegada = detalhes_rota[i]["horario_chegada"]
                    
                    # Faz a requisição para reservar o posto
                    response = requests.post(url, json={
                        "nome_posto": nome_posto,
                        "cliente_id": dados.get('cliente_id'),
                        "horario_reserva": horario_chegada
                    }, timeout=15)
                    
                    if response.status_code == 200:
                        logger.info(f"Posto {nome_posto} reservado com sucesso para o horário {horario_chegada}")
                    else:
                        logger.error(f"Falha ao reservar posto {nome_posto}")
                        # Cancela todas as reservas anteriores
                        for j in range(i):
                            try:
                                nome_posto_anterior = postos_reservados[j]
                                if nome_posto_anterior.startswith("Posto_Central1"):
                                    url = f"http://localhost:5000/cancelar"
                                elif nome_posto_anterior.startswith("Posto_Central2"):
                                    url = f"http://localhost:5001/cancelar"
                                else:
                                    url = f"http://localhost:5002/cancelar"
                                
                                requests.post(url, json={
                                    "nome_posto": nome_posto_anterior,
                                    "cliente_id": dados.get('cliente_id'),
                                    "horario_reserva": detalhes_rota[j]["horario_chegada"]
                                }, timeout=15)
                            except:
                                pass
                        
                        resposta = {
                            "cliente_id": dados.get('cliente_id'),
                            "postos_reservados": [],
                            "status": "erro",
                            "mensagem": f"Falha ao reservar posto {nome_posto}",
                            "timestamp": time.time()
                        }
                        client.publish("Resposta/Reserva", json.dumps(resposta))
                        return
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Erro ao reservar posto {nome_posto}: {e}")
                    # Cancela todas as reservas anteriores
                    for j in range(i):
                        try:
                            nome_posto_anterior = postos_reservados[j]
                            if nome_posto_anterior.startswith("Posto_Central1"):
                                url = f"http://localhost:5000/cancelar"
                            elif nome_posto_anterior.startswith("Posto_Central2"):
                                url = f"http://localhost:5001/cancelar"
                            else:
                                url = f"http://localhost:5002/cancelar"
                            
                            requests.post(url, json={
                                "nome_posto": nome_posto_anterior,
                                "cliente_id": dados.get('cliente_id'),
                                "horario_reserva": detalhes_rota[j]["horario_chegada"]
                            }, timeout=15)
                        except:
                            pass
                    
                    resposta = {
                        "cliente_id": dados.get('cliente_id'),
                        "postos_reservados": [],
                        "status": "erro",
                        "mensagem": f"Erro ao reservar posto {nome_posto}: {str(e)}",
                        "timestamp": time.time()
                    }
                    client.publish("Resposta/Reserva", json.dumps(resposta))
                    return
            
            # Publica a resposta com os detalhes da rota
            resposta = {
                "cliente_id": dados.get('cliente_id'),
                "postos_reservados": postos_reservados,
                "status": "sucesso",
                "mensagem": "Todos os postos necessários foram reservados com sucesso",
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
        client.connect("localhost", 1885, 60)  # Usando a porta 1883
        
        # Iniciando o loop de eventos MQTT em uma thread separada
        client.loop_start()
        
        # Iniciando o servidor Flask
        logger.info("""
        ============================================
        Servidor Central 1 Iniciado
        Flask rodando na porta 5002
        MQTT escutando no tópico: Solicitar/Reserva
        Broker: localhost:1885
        ============================================
        """)
        app.run(host='0.0.0.0', port=5002)
        
    except KeyboardInterrupt:
        logger.info("Servidor Central 1 encerrado pelo usuário.")
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor: {e}")
    finally:
        client.disconnect() 