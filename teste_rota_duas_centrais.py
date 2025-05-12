import paho.mqtt.client as mqtt
import json
import time
import random

# Configuração do cliente MQTT
client = mqtt.Client()

# Callback quando conectado
def on_connect(client, userdata, flags, rc):
    print("Conectado ao broker MQTT")
    # Inscreve no tópico de resposta
    client.subscribe("Resposta/Reserva")

# Callback quando recebe uma mensagem
def on_message(client, userdata, msg):
    print(f"\nResposta recebida no tópico {msg.topic}:")
    try:
        dados = json.loads(msg.payload.decode())
        print(f"\n=== Informações da Rota ===")
        print(f"Cliente ID: {dados['cliente_id']}")
        print(f"Status: {dados['status']}")
        print(f"Mensagem: {dados['mensagem']}")
        
        if dados['status'] == 'sucesso':
            print("\n=== Postos Reservados ===")
            for i, posto in enumerate(dados['postos_reservados'], 1):
                print(f"{i}. {posto}")
            
            print("\n=== Detalhes da Rota ===")
            for etapa in dados['detalhes_rota']:
                if etapa['tipo'] == 'posto':
                    print(f"Posto: {etapa['nome']}")
                    print(f"  Localização: ({etapa['x']}, {etapa['y']})")
                    print(f"  Tempo de espera: {etapa['tempo_espera']} segundos")
                    print(f"  Bateria na chegada: {etapa['bateria_chegada']}%")
                else:  # destino
                    print(f"Destino Final: ({etapa['x']}, {etapa['y']})")
                    print(f"  Bateria restante: {etapa['bateria_restante']:.1f}%")
        else:
            print("\n=== Erro na Rota ===")
            print(f"Motivo: {dados['mensagem']}")
            if dados.get('detalhes_rota'):
                print("\nRota parcial calculada:")
                for etapa in dados['detalhes_rota']:
                    if etapa['tipo'] == 'posto':
                        print(f"Posto: {etapa['nome']} em ({etapa['x']}, {etapa['y']})")
        
        print(f"\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(dados['timestamp']))}")
    except json.JSONDecodeError:
        print(f"Mensagem recebida: {msg.payload.decode()}")

# Registra os callbacks
client.on_connect = on_connect
client.on_message = on_message

# Conecta ao broker
client.connect("localhost", 1883, 60)

# Inicia o loop em background
client.loop_start()

# Função para enviar solicitação de reserva
def enviar_solicitacao(x_inicial, y_inicial, x_destino, y_destino):
    mensagem = {
        "cliente_id": f"cliente_{random.randint(1000, 9999)}",
        "x_inicial": x_inicial,
        "y_inicial": y_inicial,
        "x_destino": x_destino,
        "y_destino": y_destino,
        "timestamp": time.time()
    }
    
    print("\nEnviando solicitação de reserva:")
    print(f"Origem: ({x_inicial}, {y_inicial})")
    print(f"Destino: ({x_destino}, {y_destino})")
    
    client.publish("Solicitar/Reserva", json.dumps(mensagem))

# Coordenadas para teste
# Central 1: X entre -1000 e -500
# Central 2: X entre -500 e 0
# Vamos fazer uma rota que cruza as duas áreas

# Origem: Ponto no extremo oeste da área da Central 1
x_inicial = -950
y_inicial = 0

# Destino: Ponto no extremo leste da área da Central 2
x_destino = -50
y_destino = 0

print("=== Teste de Rota entre Duas Centrais ===")
print(f"Origem: ({x_inicial}, {y_inicial}) - Área da Central 1")
print(f"Destino: ({x_destino}, {y_destino}) - Área da Central 2")
print("Esta rota deve passar por postos de ambas as centrais")

# Envia a solicitação
enviar_solicitacao(x_inicial, y_inicial, x_destino, y_destino)

# Aguarda a resposta
time.sleep(10)

# Encerra o cliente
client.loop_stop()
client.disconnect() 