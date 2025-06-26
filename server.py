from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic
import json
import os
from datetime import datetime
import re
import PyPDF2
import base64
from io import BytesIO
from dotenv import load_dotenv
import logging
from database import (
    verify_user,
    get_all_users,
    create_user,
    delete_user,
    get_user_chats,
    create_chat,
    add_message_to_chat,
    get_chat_messages,
    delete_chat,
    get_prompt,
    update_prompt,
    get_db_connection
)
from setup_db import setup_database
import time
import uuid

# Carrega variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Variáveis de ambiente carregadas")

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Cliente Anthropic com timeout reduzido
api_key = os.getenv('ANTHROPIC_API_KEY')
logger.info("Verificando variáveis de ambiente:")
logger.info(f"ANTHROPIC_API_KEY está definida? {'Sim' if api_key else 'Não'}")

if not api_key:
    logger.error("API key não encontrada nas variáveis de ambiente")
    raise ValueError("ANTHROPIC_API_KEY não está definida")

if not api_key.startswith('sk-ant-'):
    logger.error("API key inválida: deve começar com 'sk-ant-'")
    raise ValueError("ANTHROPIC_API_KEY inválida")

# Add more detailed API key validation
api_key_length = len(api_key)
logger.info(f"Comprimento da API key: {api_key_length} caracteres")
logger.info(f"API key começa com: {api_key[:7]} e termina com: {api_key[-4:]}")

# Check for common issues
if ' ' in api_key:
    logger.warning("API key contém espaços em branco")
if '\n' in api_key or '\r' in api_key:
    logger.warning("API key contém caracteres de nova linha")
if len(api_key.strip()) != api_key_length:
    logger.warning("API key contém espaços em branco no início ou fim")

# Initialize client with clean API key and timeout
clean_api_key = api_key.strip()
logger.info("Inicializando cliente do Claude...")
try:
    client = anthropic.Anthropic(
        api_key=clean_api_key,
        max_retries=2,  # Reduzir número de retries
        timeout=90.0    # Aumentado de 30s para 90s para evitar timeouts
    )
    # Test the client with a simple request
    test_response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hi"}]
    )
    logger.info("Cliente do Claude testado e funcionando!")
except anthropic.AuthenticationError as e:
    logger.error(f"Erro de autenticação ao inicializar cliente do Claude: {e}")
    raise ValueError("Falha na autenticação com a API do Claude. Verifique sua API key.")
except Exception as e:
    logger.error(f"Erro ao inicializar cliente do Claude: {e}")
    raise ValueError(f"Falha ao inicializar cliente do Claude: {e}")

# Configurar banco de dados na inicialização
logger.info("Configurando banco de dados...")
try:
    setup_database()
    logger.info("Banco de dados configurado com sucesso!")
except Exception as e:
    logger.error(f"Erro ao configurar banco de dados: {e}")

def extract_pdf_text(file_data):
    try:
        if not file_data or ',' not in file_data:
            logger.error("Dados do PDF inválidos")
            return None
        pdf_bytes = base64.b64decode(file_data.split(',')[1])
        
        pdf_file = BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {e}")
        return None

def parse_chart_from_response(text):
    """Parse chart data from Claude's response text.
    
    Args:
        text (str): The text to parse
        
    Returns:
        dict or None: The parsed chart data or None if no valid data found
    """
    try:
        if not text:
            return None
            
        # First try to find data between [GRAFICO_DADOS] tags
        start = text.find('[GRAFICO_DADOS]')
        end = text.find('[/GRAFICO_DADOS]')
        
        if start != -1 and end != -1 and end > start:
            chart_json = text[start + 14:end].strip()
            
            try:
                chart_data = json.loads(chart_json)
                # Validate chart data structure
                if not isinstance(chart_data, dict):
                    return None
                    
                required_fields = ['type', 'title', 'years', 'initialValue', 'products']
                missing_fields = [field for field in required_fields if field not in chart_data]
                if missing_fields:
                    return None
                    
                return chart_data
            except json.JSONDecodeError:
                return None
        
        return None
    except Exception:
        return None

# Função para processar mensagem do Claude com timeout
def process_claude_message(messages, max_retries=1):
    for attempt in range(max_retries):
        try:
            # Obter o prompt do sistema
            system_prompt = get_prompt()
            logger.info(f"Prompt carregado: {system_prompt[:100] if system_prompt else 'NENHUM PROMPT ENCONTRADO'}...")
            logger.info(f"Tamanho total do prompt: {len(system_prompt) if system_prompt else 0} caracteres")
            
            if not system_prompt:
                logger.warning("Nenhum prompt do sistema encontrado, usando prompt padrão")
                system_prompt = "Você é um assistente especializado em investimentos da Horizont Investimentos."
            
            # Verificar tamanho total das mensagens e limitar para 0.5 CPU
            total_tokens = sum(len(msg["content"].split()) for msg in messages) * 2  # Estimativa aproximada
            
            # Ajustar max_tokens com base no tamanho da entrada (otimizado para 0.5 CPU)
            max_tokens = min(2048, max(512, total_tokens))  # Reduzido para 2048 max
            
            # Ajustar temperatura com base no tipo de resposta
            temp = 0.7
            if any("[GRAFICO_DADOS]" in msg["content"] for msg in messages):
                temp = 0.1  # Menor temperatura para respostas estruturadas
                max_tokens = 1024  # Limitar tokens para respostas com gráficos
            
            logger.info(f"Enviando para Claude com system prompt: {len(system_prompt)} caracteres")
            logger.info(f"Configuração: max_tokens={max_tokens}, temperature={temp}")
            
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=max_tokens,
                messages=messages,
                system=system_prompt,
                temperature=temp
            )
            
            logger.info(f"Resposta recebida do Claude: {len(response.content[0].text) if response and response.content else 0} caracteres")
            return response
            
        except Exception as e:
            logger.error(f"Tentativa {attempt + 1} falhou: {str(e)}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # Espera 1 segundo antes de tentar novamente

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        username = data.get('username', '')
        password = data.get('password', '')
        
        logger.info(f"Tentativa de login para usuário: {username}")
        
        if not username or not password:
            logger.warning("Tentativa de login sem usuário ou senha")
            return jsonify({"success": False, "message": "Username and password are required"}), 400
        
        user = verify_user(username, password)
        if user:
            logger.info(f"Login bem sucedido para usuário: {username}")
            return jsonify({"success": True, "role": user.get('role', 'user'), "name": user.get('name', username)})
        
        logger.warning(f"Login falhou para usuário: {username}")
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
        
    except Exception as e:
        logger.error(f"Erro durante login: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/chats/<username>', methods=['GET'])
def get_chats(username):
    try:
        logger.info(f"Buscando chats para usuário: {username}")
        chats = get_user_chats(username)
        return jsonify({"success": True, "chats": chats})
    except Exception as e:
        logger.error(f"Erro ao buscar chats: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/chats/<username>', methods=['POST'])
def create_new_chat(username):
    try:
        data = request.get_json() or {}
        title = data.get('title', 'New Chat')
        
        logger.info(f"Criando novo chat para usuário: {username}")
        chat_id = create_chat(username, title)
        
        if chat_id:
            logger.info(f"Chat criado com sucesso: {chat_id}")
            return jsonify({"success": True, "id": chat_id, "title": title})
            
        logger.error("Falha ao criar chat")
        return jsonify({"success": False, "message": "Failed to create chat"}), 500
    except Exception as e:
        logger.error(f"Erro ao criar chat: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/chats/<username>/<chat_id>', methods=['DELETE'])
def delete_user_chat(username, chat_id):
    try:
        logger.info(f"Deletando chat {chat_id} do usuário {username}")
        if delete_chat(chat_id):
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Failed to delete chat"}), 500
    except Exception as e:
        logger.error(f"Erro ao deletar chat: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/message', methods=['POST'])
def message():
    try:
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] Iniciando processamento de mensagem")
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Dados inválidos"}), 400

        chat_id = data.get('chatId')
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return jsonify({"success": False, "message": "Mensagem vazia"}), 400

        # Verificar se é uma mensagem muito longa
        if len(message_content) > 8000:  # Limitar tamanho da mensagem
            return jsonify({
                "success": False,
                "message": "Mensagem muito longa. Por favor, reduza o tamanho."
            }), 400

        # Processar PDF se presente
        pdf_data = data.get('pdfData')
        if pdf_data:
            pdf_text = extract_pdf_text(pdf_data)
            if pdf_text:
                message_content += f"\n\nConteúdo do PDF:\n{pdf_text}"

        # Obter mensagens anteriores do chat
        messages = []
        if chat_id:
            chat_messages = get_chat_messages(chat_id)
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_messages]
        
        # Adicionar nova mensagem
        messages.append({"role": "user", "content": message_content})
        
        logger.info(f"[{request_id}] Mensagens preparadas para o Claude: {len(messages)} mensagens")

        try:
            # Processar mensagem com retry e timeout
            response = process_claude_message(messages)
            
            if not response or not response.content:
                raise Exception("Resposta vazia do Claude")

            assistant_message = response.content[0].text
            
            # Salvar mensagens no banco de forma otimizada
            if chat_id:
                logger.info(f"Salvando mensagens no chat {chat_id}")
                
                # Salvar ambas as mensagens de uma vez para ser mais rápido
                try:
                    add_message_to_chat(chat_id, "user", message_content)
                    add_message_to_chat(chat_id, "assistant", assistant_message)
                    logger.info("Mensagens salvas com sucesso!")
                except Exception as db_error:
                    logger.error(f"Erro ao salvar no banco: {db_error}")
                    # Não falhar a resposta por erro no banco
                    pass
            
            return jsonify({
                "success": True,
                "message": assistant_message
            })

        except Exception as e:
            logger.error(f"[{request_id}] Erro ao processar mensagem: {str(e)}")
            return jsonify({
                "success": False,
                "message": "O servidor está temporariamente indisponível. Por favor, tente novamente em alguns instantes."
            }), 502

    except Exception as e:
        logger.error(f"Erro não tratado: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Erro interno do servidor"
        }), 500

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    try:
        logger.info("Buscando lista de usuários")
        users = get_all_users()
        return jsonify({"success": True, "users": users})
    except Exception as e:
        logger.error(f"Erro ao buscar usuários: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/users', methods=['POST'])
def create_new_user():
    try:
        data = request.get_json() or {}
        username = data.get('username', '')
        password = data.get('password', '')
        role = data.get('role', 'user')
        
        if not username or not password:
            logger.warning("Tentativa de criar usuário sem username ou senha")
            return jsonify({"success": False, "message": "Username and password are required"}), 400
        
        logger.info(f"Criando novo usuário: {username}")
        if create_user(username, password, role):
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Failed to create user"}), 500
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/users/<username>', methods=['DELETE'])
def delete_existing_user(username):
    try:
        logger.info(f"Deletando usuário: {username}")
        if delete_user(username):
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Failed to delete user"}), 500
    except Exception as e:
        logger.error(f"Erro ao deletar usuário: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/config/prompt', methods=['GET'])
def get_public_prompt():
    """Endpoint público para visualizar o prompt atual"""
    try:
        logger.info("Buscando prompt público")
        prompt_content = get_prompt()
        if prompt_content:
            return jsonify({"success": True, "prompt": prompt_content})
        return jsonify({"success": False, "message": "No prompt configured"}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar prompt público: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/config/prompt', methods=['GET'])
def get_prompt_config():
    try:
        logger.info("Buscando configuração do prompt (admin)")
        prompt_content = get_prompt()
        if prompt_content:
            return jsonify({"success": True, "prompt": prompt_content})
        return jsonify({"success": False, "message": "No prompt configured"}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar prompt admin: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/config/prompt', methods=['PUT'])
def update_prompt_config():
    try:
        data = request.get_json() or {}
        new_prompt = data.get('prompt', '')
        username = data.get('username', 'admin')
        
        if not new_prompt:
            logger.warning("Tentativa de atualizar prompt sem conteúdo")
            return jsonify({"success": False, "message": "No prompt provided"}), 400
        
        logger.info(f"Atualizando prompt (usuário: {username})")
        if update_prompt(new_prompt, username):
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Failed to update prompt"}), 500
    except Exception as e:
        logger.error(f"Erro ao atualizar prompt: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        connection = get_db_connection()
        if connection is None:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
        connection.close()
        
        # Test Claude API
        try:
            client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
                timeout=5  # Short timeout for health check
            )
        except Exception as e:
            return jsonify({"status": "error", "message": f"Claude API check failed: {str(e)}"}), 500
        
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.before_request
def before_request():
    logger.info(f"Recebendo requisição: {request.method} {request.path}")

@app.after_request
def after_request(response):
    """Ensure all responses have proper headers and format"""
    # Add CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    # Log response status
    logger.info(f"Enviando resposta: {response.status_code}")
    
    # For error responses, ensure they have the correct format
    if response.status_code >= 400 and response.is_json:
        try:
            data = response.get_json()
            if 'success' not in data:
                new_data = {
                    'success': False,
                    'message': data.get('message', 'Unknown error')
                }
                response.set_data(json.dumps(new_data))
        except Exception as e:
            logger.error(f"Erro ao formatar resposta de erro: {e}")
            # If we can't parse the JSON, set a generic error response
            response.set_data(json.dumps({
                'success': False,
                'message': 'Internal server error'
            }))
    
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle any uncaught exception"""
    logger.error(f"Erro não tratado: {str(e)}")
    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    print("\n🚀 Servidor Horizont IA iniciado!")
    print(f"📍 Acesse: http://localhost:{port}")
    print("�� Login: admin/horizont2025")
    app.run(host='0.0.0.0', port=port, debug=True)