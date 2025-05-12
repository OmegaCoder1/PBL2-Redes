# Constantes
BATERIA_INICIAL = 100  # Bateria inicial em porcentagem
BATERIA_MINIMA = 20    # Bateria mínima para solicitar reserva
UNIDADES_POR_PORCENTAGEM = 10  # Unidades que o carro pode percorrer por 1% de bateria

# Ranges de geração de postos para esta central
X_MIN = -1000
X_MAX = -500
Y_MIN = -1000
Y_MAX = 1000

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
        nome_posto = f"Posto_Central1_{timestamp}_{random_code}"
        
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

// ... existing code ...