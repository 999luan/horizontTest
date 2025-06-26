# Documentação Técnica Completa - Horizont API

## Configuração do Ambiente (.env)
```env
# Banco de Dados
DB_HOST=horizont.mysql.database.azure.com
DB_USER=horizont_admin
DB_PASSWORD=H0r!z0nt2025
DB_NAME=horizont_prod

# Anthropic/Claude
ANTHROPIC_API_KEY=sua_chave_api

# Configurações do Servidor
PORT=5000
```

## Estrutura Completa do Banco de Dados

### 1. users
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 2. chats
```sql
CREATE TABLE chats (
    id VARCHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP NULL,
    context JSON DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 3. chat_messages
```sql
CREATE TABLE chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
);
```

### 4. prompts
```sql
CREATE TABLE prompts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(50) NOT NULL,
    updated_by VARCHAR(50) NOT NULL
);
```

## Detalhes Adicionais Importantes

### Configurações do Banco
- Engine: MySQL/MariaDB
- Charset: UTF-8
- Collation: utf8mb4_unicode_ci
- Versão mínima: MySQL 5.7 ou MariaDB 10.2

### Índices Importantes
- `users.username` (UNIQUE)
- `chats.user_id` (FK)
- `chat_messages.chat_id` (FK)
- `chats.last_message_at` (para ordenação)

### Constraints
1. **Cascade Delete**:
   - Quando um chat é deletado, suas mensagens são deletadas
   - Quando um usuário é deletado, seus chats (e mensagens) são deletados

2. **Valores Default**:
   - `users.role`: 'user'
   - `users.is_active`: TRUE
   - Timestamps: CURRENT_TIMESTAMP
   - `chats.context`: NULL (JSON)

### Formato do Context (JSON)
```json
{
  "systemPrompt": "string",
  "lastInteractions": [
    {
      "role": "user|assistant",
      "content": "string"
    }
  ]
}
```

## Rotas da API

### Autenticação

1. **POST `/api/login`**
   ```json
   {
     "username": "string",
     "password": "string"
   }
   ```
   Resposta:
   ```json
   {
     "success": true,
     "role": "user|admin",
     "name": "string"
   }
   ```

### Gerenciamento de Usuários

1. **GET `/api/admin/users`**
   - Requer: Autenticação como admin
   - Retorna: Lista de todos os usuários ativos (exceto admin)
   ```json
   {
     "success": true,
     "users": [
       {
         "id": "int",
         "username": "string",
         "role": "string",
         "created_at": "timestamp",
         "last_login": "timestamp"
       }
     ]
   }
   ```

2. **POST `/api/admin/users`**
   - Requer: Autenticação como admin
   ```json
   {
     "username": "string",
     "password": "string",
     "role": "user|admin"
   }
   ```
   Resposta:
   ```json
   {
     "success": true
   }
   ```

3. **DELETE `/api/admin/users/{username}`**
   - Requer: Autenticação como admin
   - Realiza soft delete (marca como inativo)

### Gerenciamento de Chats

1. **GET `/api/chats/{username}`**
   - Retorna: Lista de chats do usuário com mensagens
   ```json
   {
     "success": true,
     "chats": [
       {
         "id": "uuid",
         "title": "string",
         "created_at": "timestamp",
         "updated_at": "timestamp",
         "last_message_at": "timestamp",
         "messages": [
           {
             "role": "user|assistant|system",
             "content": "string",
             "created_at": "timestamp"
           }
         ]
       }
     ]
   }
   ```

2. **POST `/api/chats/{username}`**
   - Cria novo chat
   ```json
   {
     "title": "string"
   }
   ```
   Resposta:
   ```json
   {
     "success": true,
     "id": "uuid",
     "title": "string"
   }
   ```

3. **DELETE `/api/chats/{username}/{chat_id}`**
   - Deleta um chat específico

### Mensagens

1. **POST `/api/message`**
   - Envia nova mensagem
   ```json
   {
     "username": "string",
     "chatId": "uuid",
     "message": "string",
     "files": ["array de arquivos"] // opcional
   }
   ```
   Resposta:
   ```json
   {
     "success": true,
     "response": "string"
   }
   ```

### Configuração do Sistema

1. **GET `/api/admin/config/prompt`**
   - Requer: Autenticação como admin
   - Retorna o prompt do sistema

2. **PUT `/api/admin/config/prompt`**
   - Requer: Autenticação como admin
   ```json
   {
     "prompt": "string",
     "username": "string"
   }
   ```

## Produtos e Taxas

### Horizont Smart (Renda Fixa)
- Taxa: 1,20% ao mês (15,39% ao ano)
- Prazo: 365 dias
- Aplicação mínima: R$ 1,00
- Liquidação: 1 dia útil
- Resgate: 4 dias úteis

### Horizont Trend (Renda Variável)
- Taxa: 19,37% ao ano
- Prazo: 365 dias
- Aplicação mínima: R$ 1,00

### Horizont Leverage
- Taxa: 2,00% ao mês (26,82% ao ano)
- Prazo: 180 dias

## Informações da Empresa
- **Razão Social**: Horizont Investimentos LTDA
- **CNPJ**: 43.734.412/0001-68
- **Endereço**: Av. Conselheiro Carrão, 1918 — Vila Carrão — São Paulo-SP
- **WhatsApp**: +55 11 97685-9406
- **Site**: https://www.horizontinvestimentos.com.br/

## Regras de Negócio

### Saques
- Somente nos 5 primeiros dias úteis de cada mês
- Liquidação em 5 dias úteis para rendimentos
- 2 dias úteis para depósitos

### Valores Mínimos
- Aplicação: R$ 100,00
- Movimentação: R$ 50,00
- Saldo: R$ 100,00

### Prazos Mínimos
- Smart e Trend: 365 dias
- Leverage: 180 dias 