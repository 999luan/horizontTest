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

app = Flask(__name__)
CORS(app)

# Sua API Key do Claude
ANTHROPIC_API_KEY = "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"

# Cliente Anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Usuários do sistema
USERS = {
    "admin": {"password": "horizont2025", "role": "admin"},
    "carlos": {"password": "123456", "role": "user"},
    "ana": {"password": "123456", "role": "user"},
    "paulo": {"password": "123456", "role": "user"}
}

# Armazenamento em memória (em produção, use um banco de dados)
chats_storage = {}

def load_config():
    """Carrega as configurações do arquivo config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Se o arquivo não existir, cria com configuração padrão
        default_config = {"claude_prompt": get_default_prompt()}
        save_config(default_config)
        return default_config

def save_config(config):
    """Salva as configurações no arquivo config.json"""
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def get_default_prompt():
    """Retorna o prompt padrão do Claude"""
    return """Você é o CONSULTOR AMIGO da Horizont Investimentos — um especialista experiente que apoia os representantes como um colega veterano. Data atual: junho de 2025.

{greeting}

SUA PERSONALIDADE:
- Tom profissional mas próximo (como consultor sênior experiente)
- Elogie situações de forma natural: "Boa situação!", "Interessante caso!"
- Seja direto e prático nas orientações
- Sempre direcione para VENDA + INVESTIMENTO na Horizont
- Confiante sem ser exagerado
- Foque em OPORTUNIDADE DE NEGÓCIO sempre
- IMPORTANTE: Você apoia o REPRESENTANTE, não fala diretamente com o cliente

📌 IMPORTANTE SOBRE FORMATAÇÃO DE VALORES:
1. SEMPRE use valores monetários no formato brasileiro: R$ 250.000,00
2. Use ponto como separador de milhares e vírgula para decimais
3. SEMPRE inclua os centavos ,00 mesmo quando for valor redondo
4. Exemplos corretos:
   - R$ 250.000,00 (não R$ 250.000 ou R$ 250k)
   - R$ 1.234.567,89 (não R$ 1234567,89)
   - R$ 50.000,00 (não R$ 50 mil)

📌 IMPORTANTE SOBRE CÁLCULOS:
1. SEMPRE faça os cálculos corretamente usando as taxas exatas:
   - Horizont Smart: 1,20% ao mês = (1,012^12 - 1) = 15,39% ao ano
   - Horizont Trend: 19,37% ao ano = 1,1937 ao ano
   - Horizont Leverage: 2,00% ao mês = (1,02^12 - 1) = 26,82% ao ano
   - Poupança: 7,75% ao ano = 1,0775 ao ano
   - CDI: 10,88% ao ano = 1,1088 ao ano

2. Para calcular valor futuro: Valor Inicial × (1 + taxa)^anos
3. SEMPRE confira os cálculos antes de apresentar

📌 IMPORTANTE SOBRE GRÁFICOS:
Quando o usuário pedir gráficos ou quando for relevante mostrar visualmente:
1. SEMPRE use valores REAIS mencionados na conversa
2. NUNCA use valores genéricos como R$ 100.000
3. Crie gráficos ESPECÍFICOS para cada situação
4. Para incluir um gráfico customizado, use este formato:

[GRAFICO_DADOS]
{
  "type": "comparison",
  "title": "Comparativo Personalizado",
  "years": 5,
  "initialValue": 500000,
  "products": {
    "Poupança": {"rate": 7.75, "yearlyMultiplier": 1.0775},
    "CDI": {"rate": 10.88, "yearlyMultiplier": 1.1088},
    "Horizont Smart": {"rate": 15.39, "monthlyRate": 0.012, "yearlyMultiplier": 1.1539},
    "Horizont Trend": {"rate": 19.37, "yearlyMultiplier": 1.1937}
  }
}
[/GRAFICO_DADOS]

📌 REGRA DE SAQUE:
- Saques só podem ser solicitados **nos 5 primeiros dias úteis de cada mês**
- Fora desse período, o cliente precisa aguardar a próxima janela de saque

📌 INFORMAÇÕES DA EMPRESA:
Horizont Investimentos LTDA  
CNPJ: 43.734.412/0001-68  
Sede: Av. Conselheiro Carrão, 1918 — Vila Carrão — São Paulo-SP  
Sócio proprietário: Ivan Gabriel Duarte

📱 CONTATOS E LINKS:
- WhatsApp: +55 11 97685-9406
- Site: https://www.horizontinvestimentos.com.br/
- Especificações dos fundos: https://horizontinvestimentos.com.br/fundos.html
- Simulador online: disponível no site (mas priorize fazer simulações aqui)

📄 IMPORTANTE SOBRE O CONTRATO:
- Temos um CONTRATO DE MÚTUO formal registrado
- Natureza jurídica: Operação de mútuo financeiro (empréstimo)
- O cliente (mutuante) empresta recursos para a Horizont (mutuária)
- Devolução garantida com remuneração pactuada
- Tributação: Rendimentos equiparados a renda fixa com IR definitivo
- Garantias: Saldo nunca ficará abaixo de 0%
- Beneficiários: Cliente deve cadastrar 3 beneficiários

📌 DETALHES CONTRATUAIS IMPORTANTES:
- Aplicação mínima: R$ 100,00
- Movimentação mínima: R$ 50,00
- Saldo mínimo: R$ 100,00
- Prazo mínimo: 365 dias (Smart e Trend), 180 dias (Leverage)
- Saques de rendimento: Até o 5º dia útil do mês
- Liquidação: 2 dias úteis para depósitos, 5 dias úteis para rendimentos
- Taxas já inclusas nos rendimentos líquidos informados

💡 QUANDO MENCIONAR O CONTRATO:
- Se o cliente questionar sobre segurança jurídica
- Se perguntar sobre garantias
- Se questionar a natureza do investimento
- Sempre que necessário para dar mais confiança
- Use: "Temos contrato de mútuo registrado que garante..."

📈 PRODUTOS COM GESTÃO ATIVA (Contratos de Mútuo):

🔵 HORIZONT SMART (Renda Fixa):
- Rentabilidade: 1,20% ao mês LÍQUIDA
- Rentabilidade anual: 15,44% LÍQUIDA
- Aplicação mínima: R$ 1,00
- Liquidação: 1 dia útil | Resgate: 4 dias úteis
- Prazo mínimo: 364 dias
- Taxa de carregamento: Regressiva (14,40% → 1,20%)

🟡 HORIZONT TREND (Renda Variável):
- Rentabilidade 2024: +19,37% LÍQUIDA
- Rentabilidade mensal média: 1,61% LÍQUIDA
- Aplicação mínima: R$ 1,00
- Liquidação: 1 dia útil | Resgate: 4 dias úteis
- Prazo mínimo: 364 dias
- Taxa de carregamento: Regressiva (25,00% → 2,10%)
- Os principais ativos de risco dentro do fundo são 14% nas Bis Seven americanas ( Apple, Microsoft, Nvidia, Amazon, Alphabet, Meta, Tesla),2% Mercado cambial, 2% HK50 (Mercado chinês) e 2% Bitcoin. Mantendo os outros 80% em renda fixa.

🔴 HORIZONT LEVERAGE (Premium):
- Rentabilidade: 2,00% ao mês LÍQUIDA
- Rentabilidade semestral: 12,62% LÍQUIDA (6 meses)
- Aplicação mínima: R$ 100.000,00
- Prazo: 6 meses (180 dias)
- SEM taxa de carregamento
- IMPORTANTE: Produto de curto prazo (6 meses), ideal para maximizar ganhos e depois migrar para Smart ou Trend

📌 ESTRATÉGIA PARA LEVERAGE:
- O Leverage é um produto de CURTO PRAZO (apenas 6 meses)
- Ideal para: maximizar rentabilidade inicial e depois diversificar
- Sempre sugira: "6 meses no Leverage para turbinar o capital, depois migrar parte para Smart/Trend"
- Exemplo: R$ 500k → 6 meses Leverage = R$ 563.100 → Dividir entre Smart e Trend
- NUNCA projete Leverage para mais de 1 ano sem explicar a estratégia de migração

📊 COMPARATIVO DE 2024 (RESULTADOS LÍQUIDOS):
- Horizont Trend: +19,37%
- CDI: +10,88%
- Ibovespa: -10,36%
- Poupança: +7,75%

📌 ESTRUTURA DE RECEITA (TRANSPARENTE):
- Taxa de Performance: 30% sobre o lucro
- Taxa de Administração: 5% sobre o lucro
- **Total descontado internamente: 35% sobre o lucro**
- O cliente **sempre recebe o rendimento líquido prometido**

📌 ABORDAGEM ESTRATÉGICA:
1. SEMPRE calcule com valores REAIS mencionados
2. Mostre diferenças em R$ e não apenas %
3. Use comparações práticas (carro, viagem, curso)
4. Crie urgência mostrando o custo da oportunidade perdida
5. Seja criativo nos cálculos e comparações
6. Quando necessário, mencione o contrato de mútuo para dar segurança
7. Se o cliente quiser mais detalhes técnicos, direcione para o link de especificações
8. Para simulações, faça você mesmo ou sugira o site se o cliente preferir

🎯 MISSÃO:
Ser o mentor confiante que converte oportunidades em negócios fechados para a Horizont!

📞 FECHAMENTO E PRÓXIMOS PASSOS:
Sempre oriente o REPRESENTANTE a:
- "Sugira agendar uma reunião presencial ou por vídeo"
- "Envie uma proposta personalizada por email"
- "Faça o cadastro do cliente enquanto o interesse está quente"
- "Use o contrato de mútuo como argumento de segurança"
- "Mostre que você (representante) está ali para acompanhar todo o processo"

LEMBRE-SE: Você está orientando o REPRESENTANTE sobre como ele deve abordar o CLIENTE!
"""

def extract_pdf_text(file_data):
    """Extrai texto de um arquivo PDF"""
    try:
        pdf_file = BytesIO(base64.b64decode(file_data))
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        print(f"Erro ao ler PDF: {e}")
        return ""

def parse_chart_from_response(text):
    """Extrai dados de gráfico customizado da resposta do Claude"""
    chart_data = None
    
    # Procurar por padrões de gráfico na resposta
    if '[GRAFICO_DADOS]' in text and '[/GRAFICO_DADOS]' in text:
        try:
            start = text.find('[GRAFICO_DADOS]') + len('[GRAFICO_DADOS]')
            end = text.find('[/GRAFICO_DADOS]')
            chart_json = text[start:end].strip()
            chart_data = json.loads(chart_json)
            
            # Remover tags do texto
            text = text[:text.find('[GRAFICO_DADOS]')] + text[text.find('[/GRAFICO_DADOS]') + len('[/GRAFICO_DADOS]'):]
        except:
            pass
    
    # Se não encontrou dados customizados mas mencionou gráfico, criar um padrão
    if not chart_data and ('gráfico' in text.lower() or 'comparativo' in text.lower()):
        # Extrair valores mencionados no texto para criar gráfico dinâmico
        valores = re.findall(r'R\$\s*([\d.,]+)', text)
        anos = re.findall(r'(\d+)\s*anos?', text)
        
        valor_inicial = 100000  # padrão
        if valores:
            # Pegar o maior valor mencionado como inicial
            valor_inicial = max([float(v.replace('.', '').replace(',', '.')) for v in valores[:3]])
        
        anos_projecao = 5  # padrão
        if anos:
            anos_projecao = int(anos[0])
        
        chart_data = {
            'type': 'comparison',
            'years': anos_projecao,
            'initialValue': valor_inicial,
            'customData': True
        }
    
    return chart_data, text.strip()

def get_horizont_prompt():
    """Retorna o prompt atual do Claude"""
    config = load_config()
    return config.get('claude_prompt', get_default_prompt())

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username in USERS and USERS[username]['password'] == password:
        # Inicializar storage para o usuário
        if username not in chats_storage:
            chats_storage[username] = []
        
        return jsonify({
            'success': True,
            'username': username,
            'role': USERS[username]['role'],
            'message': 'Login realizado com sucesso'
        })
    
    return jsonify({
        'success': False,
        'message': 'Usuário ou senha incorretos'
    }), 401

@app.route('/api/chats/<username>', methods=['GET'])
def get_chats(username):
    if username not in chats_storage:
        chats_storage[username] = []
    
    return jsonify({
        'success': True,
        'chats': chats_storage[username]
    })

@app.route('/api/chats/<username>', methods=['POST'])
def create_chat(username):
    data = request.json
    
    if username not in chats_storage:
        chats_storage[username] = []
    
    new_chat = {
        'id': datetime.now().timestamp(),
        'title': data.get('title', 'Nova Conversa'),
        'messages': [],
        'createdAt': datetime.now().isoformat()
    }
    
    chats_storage[username].append(new_chat)
    
    return jsonify({
        'success': True,
        'chat': new_chat
    })

@app.route('/api/chats/<username>/<chat_id>', methods=['DELETE'])
def delete_chat(username, chat_id):
    if username in chats_storage:
        chats_storage[username] = [
            chat for chat in chats_storage[username] 
            if str(chat['id']) != chat_id
        ]
    
    return jsonify({'success': True})

@app.route('/api/message', methods=['POST'])
def send_message():
    data = request.json
    username = data.get('username')
    chat_id = data.get('chatId')
    message = data.get('message')
    files = data.get('files', [])
    
    # Processar arquivos anexados
    file_context = ""
    for file in files:
        if file.get('type') == 'application/pdf':
            pdf_text = extract_pdf_text(file.get('data'))
            if pdf_text:
                file_context += f"\n\nConteúdo do PDF {file.get('name')}:\n{pdf_text[:3000]}..."
    
    # Adicionar contexto do arquivo à mensagem
    full_message = message
    if file_context:
        full_message += f"\n\n[Arquivo anexado]{file_context}"
    
    # Adicionar mensagem do usuário ao chat
    for chat in chats_storage.get(username, []):
        if str(chat['id']) == str(chat_id):
            user_message = {
                'role': 'user',
                'content': message,  # Salvar mensagem original sem arquivo
                'timestamp': datetime.now().isoformat()
            }
            if files:
                user_message['files'] = [{'name': f['name'], 'size': f['size'], 'type': f['type']} for f in files]
            
            chat['messages'].append(user_message)
            
            # Atualizar título se for a primeira mensagem
            if len(chat['messages']) == 1:
                chat['title'] = message[:50] + '...' if len(message) > 50 else message
            
            break
    
    try:
        # Construir histórico de mensagens
        messages = []
        for chat in chats_storage.get(username, []):
            if str(chat['id']) == str(chat_id):
                for msg in chat['messages']:
                    if msg['role'] == 'user':
                        messages.append({
                            'role': 'user',
                            'content': msg['content']
                        })
                    elif msg['role'] == 'assistant':
                        messages.append({
                            'role': 'assistant',
                            'content': msg['content']
                        })
        
        # Adicionar contexto de arquivo apenas na última mensagem para o Claude
        if messages and file_context:
            messages[-1]['content'] = full_message
        
        # Chamar API do Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            system=get_horizont_prompt(),
            messages=messages[-10:]  # Limitar histórico
        )
        
        ai_response = response.content[0].text
        
        # Processar resposta para extrair dados de gráfico
        chart_data, clean_response = parse_chart_from_response(ai_response)
        
        # Adicionar resposta da IA ao chat
        for chat in chats_storage.get(username, []):
            if str(chat['id']) == str(chat_id):
                ai_message = {
                    'role': 'assistant',
                    'content': clean_response,
                    'timestamp': datetime.now().isoformat()
                }
                if chart_data:
                    ai_message['chart'] = chart_data
                chat['messages'].append(ai_message)
                break
        
        return jsonify({
            'success': True,
            'response': clean_response,
            'chart': chart_data
        })
        
    except Exception as e:
        print(f"Erro ao chamar API do Claude: {str(e)}")
        
        # Resposta de fallback
        fallback_response = """
Desculpe, estou com dificuldades técnicas no momento. Mas posso ajudar com informações sobre os produtos Horizont:

🔵 **Horizont Smart**: 1,20% ao mês líquido (15,44% ao ano)
🟡 **Horizont Trend**: 19,37% em 2024 (1,61% ao mês médio)
🔴 **Horizont Leverage**: 2,00% ao mês (mínimo R$ 100k)

Como posso ajudar você a converter esse cliente?
"""
        
        # Adicionar resposta de fallback
        for chat in chats_storage.get(username, []):
            if str(chat['id']) == str(chat_id):
                ai_message = {
                    'role': 'assistant',
                    'content': fallback_response,
                    'timestamp': datetime.now().isoformat()
                }
                chat['messages'].append(ai_message)
                break
        
        return jsonify({
            'success': True,
            'response': fallback_response,
            'chart': None
        })

@app.route('/api/chats/<username>/<chat_id>/update', methods=['PUT'])
def update_chat_title(username, chat_id):
    data = request.json
    new_title = data.get('title')
    
    for chat in chats_storage.get(username, []):
        if str(chat['id']) == str(chat_id):
            chat['title'] = new_title
            break
    
    return jsonify({'success': True})

@app.route('/api/generate-presentation', methods=['POST'])
def generate_presentation():
    data = request.json
    chat_id = data.get('chatId')
    username = data.get('username')
    client_name = data.get('clientName', 'Cliente')
    
    # Pegar dados da conversa
    presentation_data = {
        'title': 'Proposta Horizont Investimentos',
        'client': client_name,
        'date': datetime.now().strftime('%d/%m/%Y'),
        'charts': [],
        'summary': '',
        'calculations': []
    }
    
    # Buscar mensagens com gráficos e cálculos
    for chat in chats_storage.get(username, []):
        if str(chat['id']) == str(chat_id):
            for msg in chat['messages']:
                if msg.get('chart'):
                    presentation_data['charts'].append(msg['chart'])
                if msg['role'] == 'assistant':
                    # Extrair cálculos e simulações
                    if 'R$' in msg['content']:
                        presentation_data['calculations'].append(msg['content'])
    
    return jsonify({
        'success': True,
        'presentation': presentation_data
    })

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    # Verificar se é admin (em produção, use JWT ou sessão)
    users_list = []
    for username, user_data in USERS.items():
        if username != 'admin':  # Não mostrar admin na lista
            users_list.append({
                'username': username,
                'role': user_data['role'],
                'chatsCount': len(chats_storage.get(username, []))
            })
    
    return jsonify({
        'success': True,
        'users': users_list
    })

@app.route('/api/admin/users', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'Usuário e senha são obrigatórios'
        }), 400
    
    if username in USERS:
        return jsonify({
            'success': False,
            'message': 'Usuário já existe'
        }), 400
    
    USERS[username] = {
        'password': password,
        'role': 'user'
    }
    
    return jsonify({
        'success': True,
        'message': 'Usuário criado com sucesso'
    })

@app.route('/api/admin/users/<username>', methods=['DELETE'])
def delete_user(username):
    if username == 'admin':
        return jsonify({
            'success': False,
            'message': 'Não é possível deletar o admin'
        }), 400
    
    if username in USERS:
        del USERS[username]
        # Deletar chats do usuário também
        if username in chats_storage:
            del chats_storage[username]
    
    return jsonify({
        'success': True,
        'message': 'Usuário deletado'
    })

@app.route('/api/admin/users/<username>/chats', methods=['GET'])
def get_user_chats(username):
    chats = chats_storage.get(username, [])
    
    # Resumir chats para lista
    chats_summary = []
    for chat in chats:
        chats_summary.append({
            'id': chat['id'],
            'title': chat['title'],
            'messagesCount': len(chat['messages']),
            'createdAt': chat['createdAt'],
            'lastMessage': chat['messages'][-1]['content'][:100] if chat['messages'] else ''
        })
    
    return jsonify({
        'success': True,
        'chats': chats_summary
    })

@app.route('/api/admin/users/<username>/chats/<chat_id>', methods=['GET'])
def get_user_chat_details(username, chat_id):
    chats = chats_storage.get(username, [])
    
    for chat in chats:
        if str(chat['id']) == str(chat_id):
            return jsonify({
                'success': True,
                'chat': chat
            })
    
    return jsonify({
        'success': False,
        'message': 'Chat não encontrado'
    }), 404

@app.route('/api/admin/config/prompt', methods=['GET'])
def get_prompt_config():
    """Retorna o prompt atual do Claude"""
    try:
        config = load_config()
        return jsonify({
            "success": True,
            "prompt": config.get('claude_prompt', get_default_prompt())
        })
    except Exception as e:
        print(f"Erro ao carregar prompt: {e}")
        return jsonify({
            "success": False,
            "error": "Erro ao carregar configuração"
        }), 500

@app.route('/api/admin/config/prompt', methods=['PUT'])
def update_prompt_config():
    """Atualiza o prompt do Claude"""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "error": "Prompt não fornecido"
            }), 400

        config = load_config()
        config['claude_prompt'] = data['prompt']
        save_config(config)

        return jsonify({
            "success": True,
            "message": "Prompt atualizado com sucesso"
        })
    except Exception as e:
        print(f"Erro ao salvar prompt: {e}")
        return jsonify({
            "success": False,
            "error": "Erro ao salvar configuração"
        }), 500

if __name__ == '__main__':
    import sys
    port = 8001 if '--port' in sys.argv else 8000
    print("\n🚀 Servidor Horizont IA iniciado!")
    print(f"📍 Acesse: http://localhost:{port}")
    print("👤 Login: admin/horizont2025 ou carlos/123456")
    print("📱 Interface otimizada para mobile!\n")
    app.run(host='0.0.0.0', port=port, debug=True)