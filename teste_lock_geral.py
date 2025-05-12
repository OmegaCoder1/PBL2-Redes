import requests
import threading
import time
from datetime import datetime

def get_timestamp():
    """Retorna o timestamp atual com milissegundos."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def fazer_reserva(servidor, cliente_id, horario):
    """Faz uma reserva em um servidor específico."""
    url = f"http://localhost:{servidor}/reservar"
    nome_posto = f"Posto_Central{servidor[-1]}_1"
    
    print(f"[ESCRITA] [{get_timestamp()}] Cliente {cliente_id} tentando reservar no servidor {servidor}...")
    
    try:
        response = requests.post(url, json={
            "nome_posto": nome_posto,
            "cliente_id": cliente_id,
            "horario_reserva": horario
        })
        
        print(f"[ESCRITA] [{get_timestamp()}] Resposta para {cliente_id} no servidor {servidor}:")
        if response.status_code == 200:
            print(f"✅ Reserva bem-sucedida para {cliente_id} (início: {get_timestamp()})")
        else:
            print(f"❌ Erro {response.status_code}: {response.json()['mensagem']}")
            
    except Exception as e:
        print(f"❌ Erro ao fazer reserva: {str(e)}")

def consultar_postos(servidor, cliente_id):
    """Consulta os postos em um servidor específico."""
    url = f"http://localhost:{servidor}/postos"
    
    print(f"[LEITURA] [{get_timestamp()}] Cliente {cliente_id} consultando postos no servidor {servidor}...")
    
    try:
        response = requests.get(url)
        
        print(f"[LEITURA] [{get_timestamp()}] Resposta para {cliente_id} no servidor {servidor}:")
        if response.status_code == 200:
            print(f"✅ Consulta bem-sucedida para {cliente_id} (início: {get_timestamp()})")
        else:
            print(f"❌ Erro {response.status_code}: {response.json()['mensagem']}")
            
    except Exception as e:
        print(f"❌ Erro ao consultar postos: {str(e)}")

def testar_servidor(servidor):
    """Testa o Reader-Writer Lock em um servidor específico."""
    print(f"\n{'='*50}")
    print(f"TESTANDO SERVIDOR {servidor}")
    print(f"{'='*50}")
    
    # Cliente de escrita
    cliente_escrita = f"cliente_escrita_{servidor}"
    horario = "10:00"
    
    # Clientes de leitura
    clientes_leitura = [f"leitura_{servidor}_{i}" for i in range(3)]
    
    # Inicia a escrita em uma thread separada
    thread_escrita = threading.Thread(
        target=fazer_reserva,
        args=(servidor, cliente_escrita, horario)
    )
    thread_escrita.start()
    
    # Dá um pequeno delay para garantir que a escrita comece primeiro
    time.sleep(1)
    
    # Inicia as leituras em threads separadas
    threads_leitura = []
    for cliente in clientes_leitura:
        thread = threading.Thread(
            target=consultar_postos,
            args=(servidor, cliente)
        )
        threads_leitura.append(thread)
        thread.start()
    
    # Aguarda todas as threads terminarem
    thread_escrita.join()
    for thread in threads_leitura:
        thread.join()
    
    print(f"\nResultados para o servidor {servidor}:")
    print("1. A escrita deve ter sido executada primeiro")
    print("2. As leituras devem ter esperado a escrita terminar")
    print("3. As leituras devem ter sido executadas em paralelo")
    print("4. O tempo de execução total deve ser de aproximadamente 5 segundos")

def main():
    """Função principal que testa todos os servidores."""
    servidores = ["5000", "5001", "5002"]
    
    print("Iniciando teste do Reader-Writer Lock em todos os servidores...")
    print("Este teste irá:")
    print("1. Iniciar uma escrita em cada servidor")
    print("2. Iniciar 3 leituras em cada servidor durante a escrita")
    print("3. Verificar se as leituras esperam a escrita terminar")
    print("4. Verificar se as leituras são executadas em paralelo")
    
    for servidor in servidores:
        testar_servidor(servidor)
        time.sleep(2)  # Pequeno delay entre os testes

if __name__ == "__main__":
    main() 