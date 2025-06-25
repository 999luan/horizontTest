import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

def setup_database():
    try:
        # Conectar ao banco de dados
        print("Conectando ao banco de dados...")
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )

        if connection.is_connected():
            print("Conexão estabelecida com sucesso!")
            cursor = connection.cursor()

            # Ler e executar o script SQL
            print("\nExecutando script SQL...")
            with open('setup_database.sql', 'r', encoding='utf-8') as sql_file:
                sql_script = sql_file.read()
                # Dividir o script em comandos individuais
                sql_commands = sql_script.split(';')
                
                for command in sql_commands:
                    if command.strip():
                        print(f"\nExecutando comando:\n{command}")
                        cursor.execute(command)
                        print("Comando executado com sucesso!")

            # Criar usuário admin
            print("\nCriando usuário admin...")
            admin_password = "horizont2025"
            password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
            """, ('admin', password_hash.decode('utf-8'), 'admin'))

            # Criar usuários iniciais
            print("\nCriando usuários iniciais...")
            initial_users = [
                ('carlos', '123456', 'user'),
                ('ana', '123456', 'user'),
                ('paulo', '123456', 'user')
            ]

            for username, password, role in initial_users:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role)
                    VALUES (%s, %s, %s)
                """, (username, password_hash.decode('utf-8'), role))

            # Criar prompt padrão
            print("\nCriando prompt padrão...")
            with open('config.json', 'r', encoding='utf-8') as f:
                import json
                config = json.load(f)
                default_prompt = config.get('claude_prompt', '')
                
                cursor.execute("""
                    INSERT INTO prompts (name, description, content, created_by, updated_by)
                    VALUES (%s, %s, %s, %s, %s)
                """, ('Prompt Padrão', 'Prompt padrão do sistema', default_prompt, 'admin', 'admin'))

            # Commit das alterações
            connection.commit()
            print("\nBanco de dados configurado com sucesso!")

    except Error as e:
        print(f"\nErro durante a configuração do banco de dados: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConexão com o banco de dados fechada.")

if __name__ == "__main__":
    setup_database() 