import os
import json
import time
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import redis
from redis.exceptions import RedisError, AuthenticationError

MONGO_URI = os.getenv("MONGO_URI", "sua_string_de_conexao_mongodb_aqui")
REDIS_URI = os.getenv("REDIS_URI", "sua_string_de_conexao_redis_aqui")

def conectar_mongodb():
    """Conecta a uma instância MongoDB Atlas."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Força uma chamada para verificar a conexão
        client.admin.command('ping')
        print("Conectado ao MongoDB com sucesso!")
        return client
    except (ConnectionFailure, OperationFailure) as e:
        print(f"Erro ao conectar/autenticar no MongoDB: {e}")
        return None

def conectar_redis():
    """Conecta a uma instância Redis Cloud ou Upstash."""
    try:
        r = redis.Redis.from_url(REDIS_URI, decode_responses=True)
        r.ping()
        print("Conectado ao Redis com sucesso!")
        return r
    except (RedisError, AuthenticationError) as e:
        print(f"Erro ao conectar/autenticar no Redis: {e}")
        return None

def popular_mongodb(db):
    """Insere 3 documentos na coleção produtos."""
    produtos = [
        {"nome": "Notebook", "preco": 3500.00, "categoria": "Eletronicos"},
        {"nome": "Mouse", "preco": 8.50, "categoria": "Acessorios"},
        {"nome": "Teclado", "preco": 150.00, "categoria": "Acessorios"}
    ]
    # Limpa a coleção para evitar duplicatas em múltiplos testes
    db.produtos.delete_many({})
    db.produtos.insert_many(produtos)
    print("-> 3 produtos inseridos no MongoDB.")

def consultar_produtos_caros(db):
    """Retorna produtos com preço > 10."""
    print("-> Produtos com preço > 10:")
    for prod in db.produtos.find({"preco": {"$gt": 10}}):
        print(f"   - {prod['nome']}: R${prod['preco']}")

def atualizar_preco(db, nome, novo_preco):
    """Atualiza o preço de um produto específico."""
    result = db.produtos.update_one(
        {"nome": nome},
        {"$set": {"preco": novo_preco}}
    )
    if result.modified_count > 0:
        print(f"-> Preço do produto '{nome}' atualizado para R${novo_preco}.")

def remover_por_categoria(db, categoria):
    """Remove um produto pela categoria."""
    result = db.produtos.delete_one({"categoria": categoria})
    if result.deleted_count > 0:
        print(f"-> Um produto da categoria '{categoria}' foi removido.")

def configurar_boas_vindas(r):
    """Armazena uma string de boas-vindas."""
    r.set("mensagem:inicio", "Bem-vindo ao sistema de cache NoSQL!")
    print(f"-> Redis Mensagem: {r.get('mensagem:inicio')}")

def salvar_dados_usuario(r, nome, email):
    """Utiliza uma estrutura hash para guardar dados de um usuário."""
    r.hset("usuario:1", mapping={"nome": nome, "email": email})
    usuario = r.hgetall("usuario:1")
    print(f"-> Redis Usuário salvo: {usuario}")

def registrar_log(r, acao):
    """Utiliza uma lista para armazenar logs de acesso."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {acao}"
    r.rpush("logs:acesso", log_entry)

def exibir_logs(r):
    """Recupera e exibe todos os elementos da lista de logs."""
    logs = r.lrange("logs:acesso", 0, -1)
    print("-> Logs de Acesso Registrados:")
    for log in logs:
        print(f"   - {log}")

def buscar_produto_com_cache(db, r, nome_produto):
    """Busca produto no cache (Redis) antes de ir ao banco (MongoDB)."""
    chave_redis = f"produto:{nome_produto}"
    
    # 1. Verifica no Redis
    produto_cache = r.get(chave_redis)
    if produto_cache:
        registrar_log(r, f"Cache HIT para o produto: {nome_produto}")
        print(f"\n[CACHE HIT] Produto '{nome_produto}' encontrado no Redis:")
        return json.loads(produto_cache)
    
    # 2. Se não existir, busca no MongoDB (ignorando o _id para facilitar serialização JSON)
    registrar_log(r, f"Cache MISS para o produto: {nome_produto}. Buscando no MongoDB...")
    produto_db = db.produtos.find_one({"nome": nome_produto}, {"_id": 0})
    
    # 3. Armazena no Redis com TTL de 60 segundos
    if produto_db:
        r.setex(chave_redis, 60, json.dumps(produto_db))
        print(f"\n[CACHE MISS] Produto '{nome_produto}' encontrado no MongoDB e salvo no Redis (TTL: 60s).")
        return produto_db
    else:
        print(f"\n[AVISO] Produto '{nome_produto}' não encontrado em nenhum banco.")
        return None

def main():
    mongo_client = conectar_mongodb()
    redis_client = conectar_redis()

    if not mongo_client or not redis_client:
        print("Encerrando execução devido a falha nas conexões.")
        return

    # Limpa dados do redis para o teste
    redis_client.flushdb()

    # Define banco e coleção do MongoDB
    db = mongo_client["desafio_nosql"]

    print("\n--- INICIANDO OPERAÇÕES MONGODB ---")
    popular_mongodb(db)
    consultar_produtos_caros(db)
    atualizar_preco(db, "Notebook", 3200.00)
    remover_por_categoria(db, "Acessorios")

    print("\n--- INICIANDO OPERAÇÕES REDIS ---")
    configurar_boas_vindas(redis_client)
    salvar_dados_usuario(redis_client, "João Silva", "joao@email.com")

    print("\n--- INICIANDO CASO INTEGRADO DE CACHE ---")
    # Primeira busca: Vai gerar um Cache Miss e salvar no Redis
    produto1 = buscar_produto_com_cache(db, redis_client, "Notebook")
    print(f"Dados retornados: {produto1}")

    # Segunda busca: Vai gerar um Cache Hit (vai pegar do Redis direto)
    produto2 = buscar_produto_com_cache(db, redis_client, "Notebook")
    print(f"Dados retornados: {produto2}")

    print("\n--- EXIBINDO LOGS DO SISTEMA ---")
    exibir_logs(redis_client)

if __name__ == "__main__":
    main()