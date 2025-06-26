import os
import logging
from dotenv import load_dotenv
import anthropic

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('ANTHROPIC_API_KEY')

logger.info("Testing with older SDK version...")

try:
    # Initialize client
    client = anthropic.Client(api_key=api_key)
    
    # Create completion (old style API)
    completion = client.completion(
        prompt=f"\n\nHuman: Hello, this is a test message.\n\nAssistant:",
        model="claude-2.1",
        max_tokens_to_sample=1024,
    )
    
    logger.info("Success!")
    logger.info(f"Response: {completion.completion}")
    
except Exception as e:
    logger.error(f"Error: {str(e)}")
    logger.error(f"Error type: {type(e)}") 