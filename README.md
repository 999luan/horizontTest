# Horizont IA

Sistema de chat inteligente para representantes da Horizont Investimentos.

## Estrutura do Banco de Dados

O sistema utiliza um banco de dados MySQL com as seguintes tabelas:

### Users
- Armazena informações dos usuários
- Campos: id, username, password_hash, role, created_at, updated_at, last_login, is_active

### Chats
- Armazena as conversas dos usuários
- Campos: id (UUID), user_id, title, created_at, updated_at, last_message_at, context (JSON)

### Chat Messages
- Armazena as mensagens individuais dos chats
- Campos: id, chat_id, role, content, created_at

### Prompts
- Armazena os prompts do sistema
- Campos: id, name, description, content, is_active, created_at, updated_at, created_by, updated_by

## Configuração do Ambiente

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Copie o arquivo `.env.example` para `.env` e configure as variáveis:
```bash
cp .env.example .env
```

4. Configure o banco de dados:
```bash
python setup_db.py
```

## Executando o Sistema

Para desenvolvimento:
```bash
python server.py
```

Para produção:
```bash
gunicorn wsgi:app
```

## Usuários Padrão

- Admin: admin/horizont2025
- Usuários de teste:
  - carlos/123456
  - ana/123456
  - paulo/123456

## Endpoints da API

### Autenticação
- POST /api/login - Login de usuário

### Chats
- GET /api/chats/<username> - Lista chats do usuário
- POST /api/chats/<username> - Cria novo chat
- DELETE /api/chats/<username>/<chat_id> - Deleta chat

### Mensagens
- POST /api/message - Envia mensagem para o chat

### Administração
- GET /api/admin/users - Lista usuários
- POST /api/admin/users - Cria usuário
- DELETE /api/admin/users/<username> - Deleta usuário
- GET /api/admin/config/prompt - Obtém prompt atual
- PUT /api/admin/config/prompt - Atualiza prompt

## Funcionalidades

- Chat com IA usando Claude 3 Sonnet
- Suporte a PDF (extração de texto)
- Geração de gráficos comparativos
- Gerenciamento de usuários
- Configuração de prompts
- Interface administrativa 