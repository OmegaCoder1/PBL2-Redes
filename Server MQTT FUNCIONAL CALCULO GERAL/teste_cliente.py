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

# Função para gerar coordenadas aleatórias
def gerar_coordenadas():
    return random.randint(-1000, 1000), random.randint(-1000, 1000)

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

# Menu interativo
while True:
    print("\n=== Menu de Teste ===")
    print("1. Enviar solicitação com coordenadas aleatórias")
    print("2. Enviar solicitação com coordenadas específicas")
    print("3. Sair")
    
    opcao = input("Escolha uma opção: ")
    
    if opcao == "1":
        x_inicial, y_inicial = gerar_coordenadas()
        x_destino, y_destino = gerar_coordenadas()
        enviar_solicitacao(x_inicial, y_inicial, x_destino, y_destino)
    elif opcao == "2":
        try:
            x_inicial = float(input("Digite a coordenada X inicial: "))
            y_inicial = float(input("Digite a coordenada Y inicial: "))
            x_destino = float(input("Digite a coordenada X destino: "))
            y_destino = float(input("Digite a coordenada Y destino: "))
            enviar_solicitacao(x_inicial, y_inicial, x_destino, y_destino)
        except ValueError:
            print("Erro: Por favor, digite números válidos para as coordenadas.")
    elif opcao == "3":
        break
    else:
        print("Opção inválida. Tente novamente.")

# Encerra o cliente
client.loop_stop()
client.disconnect() 