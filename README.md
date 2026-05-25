# Integração Python com NoSQL (MongoDB e Redis)

Este projeto demonstra a conexão de um script Python a bancos de dados NoSQL, realizando operações CRUD em uma instância do MongoDB Atlas e utilizando o Redis Cloud para um sistema de cache simples.

#Requisitos da Atividade

* MongoDB: Criação do banco `desafio_nosql`, coleção `produtos`, inserção de documentos (nome, preco, categoria), consultas com filtros, atualizações e remoções.
* Redis: Armazenamento de string (`mensagem:inicio`), hash para usuário, lista para logs.
* Cache Integrado: Função que busca produto por nome e utiliza a chave `produto:{nome}` no Redis com TTL de 60 segundos antes de buscar no MongoDB.

# Tecnologias Utilizadas e Dependências

* Python 3.8+
* [pymongo](https://pypi.org/project/pymongo/): Para comunicação com o MongoDB Atlas.
* [redis-py](https://pypi.org/project/redis/): Para comunicação com o Redis Cloud.

# Instalação das dependências

Abra seu terminal e execute o seguinte comando:

```bash
pip install pymongo redis

# Problemas enventuais e Dificuldades Encontradas
* Durante o desenvolvimento, a principal dificuldade foi configurar corretamente as variáveis de ambiente no terminal Windows (PowerShell) para garantir que as senhas e URIs dos bancos não ficassem expostas no código-fonte. Além disso, houve um pequeno desafio ao resolver um conflito de merge (Merge Conflict) no Git durante o envio dos arquivos, que foi solucionado mesclando as versões locais e remotas.

