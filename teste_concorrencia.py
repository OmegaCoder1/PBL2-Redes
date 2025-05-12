import requests
import paho.mqtt.client as mqtt
import threading
import time
import random
import json
from datetime import datetime, timedelta

# Configuração dos clientes MQTT
client1 = mqtt.Client()
client2 = mqtt.Client()

# Variáveis globais para armazenar respostas
respostas = {}
respostas_lock = threading.Lock()
conexoes_estabelecidas = threading.Event()
ultimas_coordenadas = {}  # Armazena as últimas coordenadas usadas

# Configurações
MAX_RETRIES = 3
TIMEOUT = 30  # segundos
RETRY_DELAY = 2  # segundos

# Coordenadas fixas para teste
COORDENADAS_FIXAS = {
    "origem": {"x": -950, "y": 0},
    "destino": {"x": -50, "y": 0}
}

def on_connect1(client, userdata, flags, rc):
    if rc == 0:
        print("Cliente 1 conectado ao broker MQTT na porta 1883")
        client.subscribe("Resposta/Reserva")
        conexoes_estabelecidas.set()
    else:
        print(f"Falha na conexão do cliente 1, código: {rc}")

def on_connect2(client, userdata, flags, rc):
    if rc == 0:
        print("Cliente 2 conectado ao broker MQTT na porta 1884")
        client.subscribe("Resposta/Reserva")
        conexoes_estabelecidas.set()
    else:
        print(f"Falha na conexão do cliente 2, código: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        dados = json.loads(payload)
        cliente_id = dados.get('cliente_id')
        
        print(f"\nRecebida mensagem para cliente {cliente_id}:")
        print(f"Tópico: {msg.topic}")
        print(f"Payload: {payload}")
        
        with respostas_lock:
            respostas[cliente_id] = dados
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

def on_publish(client, userdata, mid):
    print(f"Mensagem publicada com sucesso (mid: {mid})")

def fazer_reserva(cliente_id, coordenadas, broker_num):
    """Faz uma solicitação de reserva via MQTT para o broker especificado."""
    mensagem = {
        "cliente_id": cliente_id,
        "origem": coordenadas["origem"],
        "destino": coordenadas["destino"],
        "bateria_atual": 30.0  # Bateria baixa para garantir necessidade de postos
    }
    
    print(f"\nEnviando reserva para cliente {cliente_id} no broker {broker_num}:")
    print(f"Mensagem: {json.dumps(mensagem, indent=2)}")
    
    # Armazena as coordenadas usadas
    ultimas_coordenadas[cliente_id] = coordenadas
    
    # Tenta enviar a mensagem com retry
    for tentativa in range(MAX_RETRIES):
        try:
            # Publica a mensagem no broker especificado
            if broker_num == 1:
                client1.publish("Solicitar/Reserva", json.dumps(mensagem))
            else:
                client2.publish("Solicitar/Reserva", json.dumps(mensagem))
            
            # Aguarda a resposta
            tempo_inicial = time.time()
            while time.time() - tempo_inicial < TIMEOUT:
                with respostas_lock:
                    if cliente_id in respostas:
                        resposta = respostas.pop(cliente_id)
                        # Verifica se houve conflito (erro 409)
                        if resposta.get('status') == 'erro' and '409' in str(resposta.get('mensagem', '')):
                            print(f"Conflito detectado para cliente {cliente_id} - Tentando novamente...")
                            time.sleep(RETRY_DELAY)
                            continue
                        return resposta
                time.sleep(0.1)
            
            print(f"Tentativa {tentativa + 1} falhou - Timeout aguardando resposta para cliente {cliente_id}")
            if tentativa < MAX_RETRIES - 1:
                print(f"Aguardando {RETRY_DELAY} segundos antes de tentar novamente...")
                time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"Erro na tentativa {tentativa + 1}: {e}")
            if tentativa < MAX_RETRIES - 1:
                print(f"Aguardando {RETRY_DELAY} segundos antes de tentar novamente...")
                time.sleep(RETRY_DELAY)
    
    print(f"Todas as tentativas falharam para cliente {cliente_id}")
    return {"status": "erro", "mensagem": "Falha após múltiplas tentativas"}

def testar_reservas_simultaneas(num_clientes=5):
    """Testa reservas simultâneas de múltiplos clientes em diferentes brokers."""
    threads = []
    resultados = []
    
    def thread_reserva(cliente_id, broker_num):
        resultado = fazer_reserva(cliente_id, COORDENADAS_FIXAS, broker_num)
        resultados.append((cliente_id, broker_num, resultado))
    
    # Cria e inicia as threads
    for i in range(num_clientes):
        # Alterna entre os brokers para cada thread
        broker_num = 1 if i % 2 == 0 else 2
        t = threading.Thread(target=thread_reserva, args=(f"cliente_{i}", broker_num))
        threads.append(t)
        t.start()
    
    # Aguarda todas as threads terminarem
    for t in threads:
        t.join()
    
    # Analisa os resultados
    print("\n=== Resultados das Reservas ===")
    for cliente_id, broker_num, resultado in resultados:
        print(f"\nCliente: {cliente_id} (Broker {broker_num})")
        print(f"Status: {resultado.get('status', 'N/A')}")
        print(f"Mensagem: {resultado.get('mensagem', 'N/A')}")
        if resultado.get('status') == 'sucesso':
            print(f"Postos Reservados: {resultado.get('postos_reservados', [])}")
            print(f"Detalhes da Rota: {json.dumps(resultado.get('detalhes_rota', []), indent=2)}")

def testar_reserva_mesmo_horario():
    """Testa tentativa de reserva no mesmo horário em diferentes brokers."""
    print("\n=== Teste de Reserva no Mesmo Horário ===")
    
    # Primeira reserva no broker 1
    resultado1 = fazer_reserva("cliente_1", COORDENADAS_FIXAS, 1)
    print("\nPrimeira Reserva (Broker 1):")
    print(f"Status: {resultado1.get('status', 'N/A')}")
    print(f"Mensagem: {resultado1.get('mensagem', 'N/A')}")
    
    if resultado1.get('status') == 'sucesso':
        # Tenta fazer a segunda reserva com as mesmas coordenadas no broker 2
        resultado2 = fazer_reserva("cliente_2", COORDENADAS_FIXAS, 2)
        print("\nSegunda Reserva (mesmas coordenadas, Broker 2):")
        print(f"Status: {resultado2.get('status', 'N/A')}")
        print(f"Mensagem: {resultado2.get('mensagem', 'N/A')}")
        
        # Verifica se a segunda reserva foi rejeitada
        if resultado2.get('status') == 'sucesso':
            print("\nAVISO: A segunda reserva foi aceita com as mesmas coordenadas!")
            print("Isso indica um problema no sistema de concorrência.")

def testar_cancelamento_reserva():
    """Testa o cancelamento de uma reserva."""
    print("\n=== Teste de Cancelamento de Reserva ===")
    
    # Faz uma reserva no broker 1
    resultado = fazer_reserva("cliente_cancel", COORDENADAS_FIXAS, 1)
    
    if resultado.get('status') == 'sucesso':
        postos_reservados = resultado.get('postos_reservados', [])
        if postos_reservados:
            posto = postos_reservados[0]
            horario_reserva = resultado['detalhes_rota'][0]['horario_chegada']
            
            # Tenta cancelar a reserva
            url = "http://localhost:5000/cancelar" if "Posto_Central1" in posto else "http://localhost:5001/cancelar"
            try:
                print(f"\nTentando cancelar reserva no posto {posto}")
                response = requests.post(url, json={
                    "nome_posto": posto,
                    "cliente_id": "cliente_cancel",
                    "horario_reserva": horario_reserva
                })
                print("\nResultado do Cancelamento:")
                print(f"Status: {response.json().get('status', 'N/A')}")
                print(f"Mensagem: {response.json().get('mensagem', 'N/A')}")
            except Exception as e:
                print(f"Erro ao cancelar reserva: {e}")
        else:
            print("Nenhum posto reservado para cancelar")
    else:
        print("Falha ao fazer a reserva inicial")

if __name__ == "__main__":
    # Configura os callbacks do MQTT
    client1.on_connect = on_connect1
    client2.on_connect = on_connect2
    client1.on_message = on_message
    client2.on_message = on_message
    client1.on_publish = on_publish
    client2.on_publish = on_publish
    
    # Conecta aos brokers
    print("Conectando aos brokers MQTT...")
    client1.connect("localhost", 1883, 60)  # Broker 1
    client2.connect("localhost", 1884, 60)  # Broker 2
    
    # Inicia os loops em threads separadas
    client1.loop_start()
    client2.loop_start()
    
    # Aguarda as conexões serem estabelecidas
    print("Aguardando conexões serem estabelecidas...")
    conexoes_estabelecidas.wait(timeout=10)
    
    if not conexoes_estabelecidas.is_set():
        print("Erro: Não foi possível estabelecer conexão com os brokers")
        client1.loop_stop()
        client2.loop_stop()
        client1.disconnect()
        client2.disconnect()
        exit(1)
    
    print("Iniciando testes...")
    
    # Teste 1: Reservas simultâneas
    print("\n=== Teste 1: Reservas Simultâneas ===")
    testar_reservas_simultaneas(3)
    
    # Teste 2: Tentativa de reserva no mesmo horário
    testar_reserva_mesmo_horario()
    
    # Teste 3: Cancelamento de reserva
    testar_cancelamento_reserva()
    
    print("\nTestes concluídos!")
    
    # Desconecta dos brokers
    client1.loop_stop()
    client2.loop_stop()
    client1.disconnect()
    client2.disconnect() 