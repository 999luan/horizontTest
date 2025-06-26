import os
from anthropic import Anthropic
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get API key from environment
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    logger.error("ANTHROPIC_API_KEY environment variable is not set")
    exit(1)

logger.info(f"API Key starts with: {api_key[:8]}... ends with: ...{api_key[-4:]}")

try:
    # Initialize client
    client = Anthropic(api_key=api_key)
    logger.info("Client initialized successfully")

    # Try to send a simple message
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": "Hello, this is a test message."
        }]
    )
    
    logger.info("Message sent successfully!")
    logger.info(f"Response: {message.content}")

except Exception as e:
    logger.error(f"Error occurred: {str(e)}")
    logger.error(f"Error type: {type(e)}") 