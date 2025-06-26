import os
import subprocess
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('ANTHROPIC_API_KEY')

# Prepare curl command
curl_command = [
    'curl',
    '-v',  # Verbose output
    'https://api.anthropic.com/v1/messages',
    '-H', f'x-api-key: {api_key}',
    '-H', 'anthropic-version: 2023-06-01',
    '-H', 'content-type: application/json',
    '-d', json.dumps({
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": "Hello, this is a test message."
            }
        ]
    })
]

# Run curl command
print("Running curl command...")
result = subprocess.run(curl_command, capture_output=True, text=True)

print("\nSTDOUT:")
print(result.stdout)

print("\nSTDERR:")
print(result.stderr)

print("\nExit code:", result.returncode) 