import os
import logging
from dotenv import load_dotenv
from anthropic import Anthropic, APIError, APIConnectionError, AuthenticationError, HUMAN_PROMPT, AI_PROMPT
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def validate_api_key(api_key):
    """Validate API key format and common issues."""
    if not api_key:
        logger.error("❌ API key não encontrada nas variáveis de ambiente")
        return False
        
    if not api_key.startswith('sk-ant-'):
        logger.error("❌ API key inválida: deve começar com 'sk-ant-'")
        return False
        
    # Check length
    api_key_length = len(api_key)
    logger.info(f"📏 Comprimento da API key: {api_key_length} caracteres")
    logger.info(f"🔑 API key começa com: {api_key[:7]} e termina com: {api_key[-4:]}")
    
    # Check for common issues
    has_issues = False
    if ' ' in api_key:
        logger.error("❌ API key contém espaços em branco")
        has_issues = True
    if '\n' in api_key or '\r' in api_key:
        logger.error("❌ API key contém caracteres de nova linha")
        has_issues = True
    if len(api_key.strip()) != api_key_length:
        logger.error("❌ API key contém espaços em branco no início ou fim")
        has_issues = True
        
    return not has_issues

def test_api_connection(api_key):
    """Test API connection using the same code as the server."""
    try:
        logger.info("\n🔄 Testando conexão com a API...")
        
        # Initialize client
        client = Anthropic(api_key=api_key.strip())
        
        # Test request using new messages API
        logger.info("📤 Enviando requisição de teste...")
        test_response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": "Hi"
            }],
            system="You are a helpful AI assistant."
        )
        
        logger.info("✅ Teste bem sucedido!")
        logger.info(f"📥 Resposta: {test_response.content}")
        return True
        
    except AuthenticationError as e:
        logger.error(f"❌ Erro de autenticação: {str(e)}")
        return False
    except APIConnectionError as e:
        logger.error(f"❌ Erro de conexão: {str(e)}")
        return False
    except APIError as e:
        logger.error(f"❌ Erro da API: {str(e)}")
        # Log error details if available in the error message
        error_str = str(e)
        if 'status code' in error_str.lower():
            logger.error(f"📡 {error_str}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {str(e)}")
        return False

def main():
    """Main test function."""
    logger.info("\n🔍 Iniciando testes de conexão com a API do Claude...")
    
    # Load environment variables
    load_dotenv()
    logger.info("📚 Variáveis de ambiente carregadas")
    
    # Get and validate API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    logger.info("\n🔑 Validando API key...")
    
    if not validate_api_key(api_key):
        logger.error("❌ Falha na validação da API key")
        return False
        
    logger.info("✅ API key válida")
    
    # Test connection
    if not test_api_connection(api_key):
        logger.error("❌ Falha no teste de conexão")
        return False
        
    logger.info("\n✅ Todos os testes passaram!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 