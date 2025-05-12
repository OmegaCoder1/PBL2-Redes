import requests
import json
import time

def criar_posto(url, x, y):
    """Função para criar um posto em uma central específica."""
    try:
        response = requests.post(url, json={"x": x, "y": y})
        if response.status_code == 200:
            print(f"Posto criado com sucesso em {url} com coordenadas ({x}, {y})")
            print(f"Resposta: {response.json()}\n")
        else:
            print(f"Erro ao criar posto em {url}: {response.status_code}")
            print(f"Resposta: {response.text}\n")
    except Exception as e:
        print(f"Erro ao fazer requisição para {url}: {str(e)}\n")

def main():
    # Lista de postos a serem criados
    postos = [
        # Central 1 (porta 5000)
        {"url": "http://localhost:5000/adicionar_posto", "x": -1302.93, "y": -1302.93},
        {"url": "http://localhost:5000/adicionar_posto", "x": 394.14, "y": 394.14},
        {"url": "http://localhost:5000/adicionar_posto", "x": 2091.21, "y": 2091.21},
        
        # Central 2 (porta 5001)
        {"url": "http://localhost:5001/adicionar_posto", "x": -737.24, "y": -737.24},
        {"url": "http://localhost:5001/adicionar_posto", "x": 959.83, "y": 959.83},
        {"url": "http://localhost:5001/adicionar_posto", "x": 2656.90, "y": 2656.90},
        
        # Central 3 (porta 5002)
        {"url": "http://localhost:5002/adicionar_posto", "x": -171.55, "y": -171.55},
        {"url": "http://localhost:5002/adicionar_posto", "x": 1525.52, "y": 1525.52}
    ]
    
    print("Iniciando criação de postos...\n")
    
    # Cria cada posto com um pequeno intervalo entre as requisições
    for posto in postos:
        criar_posto(posto["url"], posto["x"], posto["y"])
        time.sleep(1)  # Espera 1 segundo entre as requisições
    
    print("Processo de criação de postos concluído!")

if __name__ == "__main__":
    main() 