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
    update_prompt
)
from setup_db import setup_database

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

# Cliente Anthropic
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

# Initialize client with clean API key
clean_api_key = api_key.strip()
logger.info("Inicializando cliente do Claude...")
try:
    client = anthropic.Anthropic(
        api_key=clean_api_key
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
    try:
        if not text:
            logger.info("Nenhum texto para parsear dados do gráfico")
            return None
            
        # First try to find data between [GRAFICO_DADOS] tags
        start = text.find('[GRAFICO_DADOS]')
        end = text.find('[/GRAFICO_DADOS]')
        
        logger.info(f"Procurando dados do gráfico - início: {start}, fim: {end}")
        
        if start != -1 and end != -1:
            chart_json = text[start + 14:end].strip()
            logger.info(f"JSON do gráfico encontrado: {chart_json}")
            
            try:
                chart_data = json.loads(chart_json)
                logger.info("Dados do gráfico parseados com sucesso")
                return chart_data
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON do gráfico: {e}")
                logger.error(f"JSON inválido: {chart_json}")
                return None
        
        # If no tags found, try to find a JSON object in the text
        import re
        json_pattern = r'\{[^{}]*\}'
        matches = re.finditer(json_pattern, text)
        
        for match in matches:
            try:
                potential_json = match.group()
                chart_data = json.loads(potential_json)
                
                # Validate if it looks like chart data
                if isinstance(chart_data, dict) and ('products' in chart_data or 'initialValue' in chart_data):
                    logger.info("Dados do gráfico encontrados em JSON inline")
                    return chart_data
            except json.JSONDecodeError:
                continue
            
        logger.info("Nenhum dado de gráfico encontrado no texto")
        return None
    except Exception as e:
        logger.error(f"Erro ao parsear dados do gráfico: {e}")
        logger.error(f"Texto completo: {text[:200]}...")  # Log apenas os primeiros 200 caracteres
        return None

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
def send_message():
    try:
        data = request.get_json() or {}
        chat_id = data.get('chatId', '')
        message = data.get('message', '')
        files = data.get('files', [])
        
        if not chat_id or not message:
            logger.warning("Tentativa de enviar mensagem sem chat_id ou conteúdo")
            return jsonify({"success": False, "message": "chat_id and message are required"}), 400
        
        logger.info(f"Processando mensagem para chat: {chat_id}")
        
        # Adiciona mensagem do usuário
        if not add_message_to_chat(chat_id, 'user', message):
            logger.error("Falha ao salvar mensagem do usuário")
            return jsonify({"success": False, "message": "Failed to save user message"}), 500
        
        # Obtém o prompt do banco de dados
        system_prompt = get_prompt()
        if not system_prompt:
            logger.error("Nenhum prompt configurado")
            return jsonify({"success": False, "message": "No prompt configured"}), 500
        
        # Obtém histórico de mensagens
        messages = get_chat_messages(chat_id)
        conversation = []
        for msg in messages:
            if isinstance(msg, dict):
                conversation.append({
                    "role": str(msg.get('role', '')),
                    "content": str(msg.get('content', ''))
                })
        
        # Envia para o Claude
        logger.info("Enviando mensagem para o Claude")
        try:
            # Prepara as mensagens para o Claude
            messages_for_claude = []
            
            # Adiciona o histórico da conversa
            for msg in conversation:
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    continue
                    
                role = "assistant" if msg["role"] == "assistant" else "user"
                content = msg["content"]
                if not content:  # Skip empty messages
                    continue
                    
                messages_for_claude.append({
                    "role": role,
                    "content": content
                })
            
            logger.info(f"Mensagens preparadas para o Claude: {len(messages_for_claude)} mensagens")
            
            try:
                response = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4096,
                    messages=messages_for_claude,
                    system=str(system_prompt)
                )
                logger.info("Resposta recebida do Claude")
                
                # Extract text from response
                if not response:
                    logger.error("Resposta do Claude está vazia")
                    raise ValueError("Empty response from Claude")
                    
                if not hasattr(response, 'content'):
                    logger.error("Resposta do Claude não contém conteúdo")
                    raise ValueError("Response from Claude has no content")
                    
                # For Claude-3, content is a list of content blocks
                content = response.content
                logger.info(f"Tipo do conteúdo da resposta: {type(content)}")
                logger.info(f"Conteúdo da resposta: {content}")
                
                if not isinstance(content, list):
                    logger.error("Conteúdo da resposta do Claude não é uma lista")
                    raise ValueError("Claude response content is not a list")
                    
                # Combine all text blocks
                response_text = ""
                for block in content:
                    logger.info(f"Processando bloco: {block}")
                    # Extract text from the block's string representation
                    block_str = str(block)
                    if 'text=' in block_str:
                        # Extract text between single quotes after 'text='
                        text_start = block_str.find("text='") + 6
                        text_end = block_str.find("'", text_start)
                        if text_start > 5 and text_end > text_start:
                            # Replace literal \n with actual newlines and add to response
                            text = block_str[text_start:text_end]
                            text = text.replace('\\\\n', '\n')  # Handle escaped newlines
                            text = text.replace('\\n', '\n')    # Handle literal newlines
                            response_text += text
                            
                            # Check for chart data in this block
                            try:
                                chart_data = parse_chart_from_response(text)
                                if chart_data:
                                    logger.info("Dados do gráfico encontrados no bloco")
                                    break  # Found chart data, no need to continue parsing
                            except Exception as e:
                                logger.error(f"Erro ao processar dados do gráfico no bloco: {e}")
                                continue
                        
                if not response_text:
                    logger.error("Texto da resposta do Claude está vazio")
                    raise ValueError("Empty text in Claude response")
                    
                logger.info(f"Resposta do Claude processada: {len(response_text)} caracteres")
                
                # Salva resposta do assistente
                if not add_message_to_chat(chat_id, 'assistant', response_text):
                    logger.error("Falha ao salvar resposta do assistente")
                    return jsonify({"success": False, "message": "Failed to save assistant message"}), 500
                
                logger.info("Mensagem processada com sucesso")
                
                # Parse chart data with better error handling
                chart_data = None
                try:
                    chart_data = parse_chart_from_response(response_text)
                except Exception as e:
                    logger.error(f"Erro ao processar dados do gráfico: {e}")
                    # Continue without chart data
                
                return jsonify({
                    "success": True,
                    "response": response_text,
                    "chart_data": chart_data
                })
                    
            except anthropic.AuthenticationError as e:
                error_msg = str(e)
                logger.error(f"Erro de autenticação na API do Claude: {error_msg}")
                return jsonify({"success": False, "message": "Authentication error with Claude API. Please check your API key."}), 401
            except anthropic.APIError as e:
                error_msg = str(e)
                logger.error(f"Erro na API do Claude: {error_msg}")
                return jsonify({"success": False, "message": f"Claude API error: {error_msg}"}), 500
            except Exception as e:
                logger.error(f"Erro inesperado na chamada do Claude: {str(e)}")
                return jsonify({"success": False, "message": "Unexpected error communicating with Claude"}), 500
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            return jsonify({"success": False, "message": "Error processing message"}), 500
        
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {str(e)}")
        return jsonify({"success": False, "message": "Error processing request"}), 500

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

@app.route('/api/admin/config/prompt', methods=['GET'])
def get_prompt_config():
    try:
        logger.info("Buscando configuração do prompt")
        prompt_content = get_prompt()
        if prompt_content:
            return jsonify({"success": True, "prompt": prompt_content})
        return jsonify({"success": False, "message": "No prompt configured"}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar prompt: {e}")
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    print("\n🚀 Servidor Horizont IA iniciado!")
    print(f"📍 Acesse: http://localhost:{port}")
    print("�� Login: admin/horizont2025")
    app.run(host='0.0.0.0', port=port, debug=True)