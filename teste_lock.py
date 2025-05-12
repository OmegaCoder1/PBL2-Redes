import requests
import threading
import time
import json
from datetime import datetime

# URL do servidor
URL_SERVIDOR = "http://localhost:5002"

# Posto que será usado para teste
POSTO_TESTE = "Posto_Central3_1"

def get_timestamp():
    """Retorna o timestamp atual formatado."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def fazer_reserva(nome_posto, cliente_id, horario_reserva):
    """Faz uma reserva no servidor."""
    try:
        timestamp_inicio = get_timestamp()
        print(f"\n[ESCRITA] [{timestamp_inicio}] Cliente {cliente_id} tentando reservar o posto {nome_posto}...")
        
        response = requests.post(
            f"{URL_SERVIDOR}/reservar",
            json={
                "nome_posto": nome_posto,
                "cliente_id": cliente_id,
                "horario_reserva": horario_reserva
            }
        )
        
        timestamp_fim = get_timestamp()
        print(f"[ESCRITA] [{timestamp_fim}] Resposta para cliente {cliente_id}:")
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Reserva bem-sucedida para {cliente_id} (início: {timestamp_inicio}, fim: {timestamp_fim})")
        elif response.status_code == 409:
            print(f"❌ Conflito de reserva para {cliente_id} (início: {timestamp_inicio}, fim: {timestamp_fim})")
        else:
            print(f"❌ Erro na reserva para {cliente_id} (início: {timestamp_inicio}, fim: {timestamp_fim})")
            
    except Exception as e:
        print(f"❌ Erro ao fazer reserva: {e}")

def consultar_postos(cliente_id):
    """Consulta os postos disponíveis no servidor."""
    try:
        timestamp_inicio = get_timestamp()
        print(f"\n[LEITURA] [{timestamp_inicio}] Cliente {cliente_id} consultando postos...")
        
        response = requests.get(f"{URL_SERVIDOR}/postos")
        
        timestamp_fim = get_timestamp()
        print(f"[LEITURA] [{timestamp_fim}] Resposta para cliente {cliente_id}:")
        print(f"Status: {response.status_code}")
        print(f"Quantidade de postos: {len(response.json())}")
        
        if response.status_code == 200:
            print(f"✅ Consulta bem-sucedida para {cliente_id} (início: {timestamp_inicio}, fim: {timestamp_fim})")
        else:
            print(f"❌ Erro na consulta para {cliente_id} (início: {timestamp_inicio}, fim: {timestamp_fim})")
            
    except Exception as e:
        print(f"❌ Erro ao consultar postos: {e}")

def testar_lock():
    """Testa o mecanismo de lock do servidor."""
    print("\n" + "="*50)
    print("TESTE DE LOCK - CENÁRIO DE TESTE")
    print("="*50)
    print("1. Um cliente fará uma reserva demorada (5 segundos)")
    print("2. Durante a reserva, outros clientes tentarão:")
    print("   - Fazer reservas no mesmo posto")
    print("   - Consultar os postos disponíveis")
    print("3. Espera-se que:")
    print("   - As consultas aguardem o lock ser liberado")
    print("   - As outras reservas sejam rejeitadas (erro 409)")
    print("="*50 + "\n")
    
    # Cliente que fará a reserva demorada
    cliente_escrita = "cliente_escrita"
    
    # Clientes que tentarão reservar durante a operação
    clientes_concorrentes = [
        "escrita_0_concorrente",
        "escrita_1_concorrente"
    ]
    
    # Clientes que tentarão consultar durante a operação
    clientes_leitura = [
        "leitura_0_0",
        "leitura_0_1",
        "leitura_0_2",
        "leitura_1_0",
        "leitura_1_1",
        "leitura_1_2"
    ]
    
    # Horário de reserva
    horario_reserva = "18:25"
    
    # Inicia a thread da reserva demorada
    thread_escrita = threading.Thread(
        target=fazer_reserva,
        args=(POSTO_TESTE, cliente_escrita, horario_reserva)
    )
    thread_escrita.start()
    
    # Aguarda um pouco para garantir que a reserva começou
    time.sleep(1)
    
    # Inicia as threads de reserva concorrente
    threads_escrita = []
    for cliente in clientes_concorrentes:
        thread = threading.Thread(
            target=fazer_reserva,
            args=(POSTO_TESTE, cliente, horario_reserva)
        )
        threads_escrita.append(thread)
        thread.start()
    
    # Inicia as threads de consulta
    threads_leitura = []
    for cliente in clientes_leitura:
        thread = threading.Thread(
            target=consultar_postos,
            args=(cliente,)
        )
        threads_leitura.append(thread)
        thread.start()
    
    # Aguarda todas as threads terminarem
    thread_escrita.join()
    for thread in threads_escrita:
        thread.join()
    for thread in threads_leitura:
        thread.join()
    
    print("\n" + "="*50)
    print("RESULTADO DO TESTE")
    print("="*50)
    print("1. A primeira reserva deve ter sido bem-sucedida (status 200)")
    print("2. As outras tentativas de reserva devem ter falhado (status 409)")
    print("3. As consultas devem ter sido bem-sucedidas (status 200)")
    print("4. As consultas devem ter sido executadas após a reserva terminar")
    print("="*50)

if __name__ == "__main__":
    testar_lock() 