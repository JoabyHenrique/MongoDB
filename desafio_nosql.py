import os
import json
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import redis
from redis.exceptions import RedisError, AuthenticationError

# Configurações de conexão
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://admin_mg:SUA_SENHA_AQUI@cluster0.mongodb.net/desafio_nosql")
REDIS_URI = os.getenv("REDIS_URI", "redis://default:femUMuUkLFMSm5i8V30Pp3sBA00AdCPT@feathered-dreamy-caption-49651.db.redis.io:12056")

def iniciar_conexao_mongo():
    """Gerencia a autenticação e conexão com o cluster do MongoDB Atlas."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
        client.admin.command('ping')
        print("[INFO] Autenticado no MongoDB Atlas com sucesso.")
        return client
    except (ConnectionFailure, OperationFailure) as err:
        print(f"[ERRO] Falha crítica de conexão no MongoDB: {err}")
        return None

def iniciar_conexao_redis():
    """Gerencia a conexão com a instância ativa do Redis Cloud."""
    try:
        conexao_redis = redis.Redis.from_url(REDIS_URI, decode_responses=True)
        conexao_redis.ping()
        print("[INFO] Conectado à instância do Redis Cloud.")
        return conexao_redis
    except (RedisError, AuthenticationError) as err:
        print(f"[ERRO] Falha crítica de autenticação no Redis: {err}")
        return None

# Operações de Negócio: MongoDB

def carga_inicial_produtos(database):
    """Insere o catálogo inicial exigido pela atividade limpando dados prévios."""
    catalogo = [
        {"nome": "Notebook", "preco": 3500.00, "categoria": "Eletronicos"},
        {"nome": "Mouse", "preco": 8.50, "categoria": "Acessorios"},
        {"nome": "Teclado", "preco": 150.00, "categoria": "Acessorios"}
    ]
    database.produtos.delete_many({})
    database.produtos.insert_many(catalogo)
    print("[MONGO] Catálogo inicial provisionado (3 produtos).")

def listar_produtos_premium(database):
    """Filtra e exibe produtos com valor superior a 10 unidades monetárias."""
    print("[MONGO] Executando query: produtos com preço > 10")
    filtros = {"preco": {"$gt": 10}}
    for item in database.produtos.find(filtros):
        print(f"  • {item['nome']} - R$ {item['preco']:.2f}")

def atualizar_valor_produto(database, nome_produto, novo_preco):
    """Atualiza o preço de um item específico do catálogo."""
    resultado = database.produtos.update_one(
        {"nome": nome_produto},
        {"$set": {"preco": novo_preco}}
    )
    if resultado.modified_count > 0:
        print(f"[MONGO] Preço de '{nome_produto}' reajustado para R$ {novo_preco:.2f}.")

def deletar_por_categoria(database, categoria):
    """Remove o primeiro registro encontrado pertencente à categoria informada."""
    resultado = database.produtos.delete_one({"categoria": categoria})
    if resultado.deleted_count > 0:
        print(f"[MONGO] Registro da categoria '{categoria}' removido da coleção.")

# Operações de Negócio: Redis

def definir_boas_vindas(cliente_redis):
    """Define a string de inicialização padrão do sistema."""
    cliente_redis.set("mensagem:inicio", "Bem-vindo ao sistema de cache NoSQL!")
    print(f"[REDIS] Chave 'mensagem:inicio' gravada: '{cliente_redis.get('mensagem:inicio')}'")

def criar_perfil_usuario(cliente_redis, nome, email):
    """Armazena informações estruturadas de usuário utilizando HASH."""
    chave = "usuario:1"
    cliente_redis.hset(chave, mapping={"nome": nome, "email": email})
    perfil = cliente_redis.hgetall(chave)
    print(f"[REDIS] Hash de usuário criado com sucesso: {perfil}")

def salvar_log_evento(cliente_redis, mensagem_evento):
    """Enfileira um novo log cronológico na lista de auditoria."""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    entrada_log = f"[{agora}] {mensagem_evento}"
    cliente_redis.rpush("logs:acesso", entrada_log)

def extrair_logs_sistema(cliente_redis):
    """Busca e exibe todos os eventos registrados na lista sequencial."""
    historico = cliente_redis.lrange("logs:acesso", 0, -1)
    print("[REDIS] Histórico de Logs Coletados:")
    for log in historico:
        print(f"  {log}")

# Camada Integrada: Sistema de Cache

def consultar_produto_inteligente(database, cliente_redis, nome_produto):
    """Busca otimizada: Consulta a memória do Redis antes de onerar o MongoDB."""
    chave_cache = f"produto:{nome_produto}"
    
    dados_cache = cliente_redis.get(chave_cache)
    if dados_cache:
        salvar_log_evento(cliente_redis, f"CACHE HIT: '{nome_produto}' recuperado do Redis.")
        print(f"\n [CACHE HIT] '{nome_produto}' lido diretamente do Redis.")
        return json.loads(dados_cache)
    
    salvar_log_evento(cliente_redis, f"CACHE MISS: Buscando '{nome_produto}' no MongoDB.")
    print(f"\n🐢 [CACHE MISS] '{nome_produto}' não estava no cache. Consultando MongoDB...")
    
    documento_mongo = database.produtos.find_one({"nome": nome_produto}, {"_id": 0})
    
    if documento_mongo:
        cliente_redis.setex(chave_cache, 60, json.dumps(documento_mongo))
        print(f"-> '{nome_produto}' salvo no Redis com tempo de vida (TTL) de 60s.")
        return documento_mongo
        
    print(f"[AVISO] O produto '{nome_produto}' não existe na base de dados.")
    return None

# Fluxo Principal de Execução

def main():
    mongo_client = iniciar_conexao_mongo()
    redis_client = iniciar_conexao_redis()

    if not mongo_client or not redis_client:
        print("[ALERTA] Abortando execução devido a falhas de infraestrutura.")
        return

    redis_client.flushdb()
    db_mongo = mongo_client["desafio_nosql"]

    print("\n--- PASSO 1: ROTINAS MONGODB ---")
    carga_inicial_produtos(db_mongo)
    listar_produtos_premium(db_mongo)
    atualizar_valor_produto(db_mongo, "Notebook", 3200.00)
    deletar_por_categoria(db_mongo, "Acessorios")

    print("\n--- PASSO 2: ROTINAS REDIS ---")
    definir_boas_vindas(redis_client)
    criar_perfil_usuario(redis_client, "João Silva", "joao@email.com")

    print("\n--- PASSO 3: TESTE DA CAMADA DE CACHE ---")
    res_1 = consultar_produto_inteligente(db_mongo, redis_client, "Notebook")
    print(f"Resultado final: {res_1}")

    res_2 = consultar_produto_inteligente(db_mongo, redis_client, "Notebook")
    print(f"Resultado final: {res_2}")

    print("\n--- PASSO 4: AUDITORIA DE LOGS ---")
    extrair_logs_sistema(redis_client)

if __name__ == "__main__":
    main()