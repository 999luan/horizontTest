import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

def check_table_exists(cursor, table_name):
    try:
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        return cursor.fetchone() is not None
    except Error as e:
        print(f"Erro ao verificar tabela {table_name}: {e}")
        return False

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

            # Verificar se as tabelas já existem
            tables_exist = all([
                check_table_exists(cursor, 'users'),
                check_table_exists(cursor, 'chats'),
                check_table_exists(cursor, 'chat_messages'),
                check_table_exists(cursor, 'prompts')
            ])

            if tables_exist:
                print("Tabelas já existem, verificando dados...")
                
                # Verificar se existe algum usuário
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                
                # Verificar se existe algum prompt
                cursor.execute("SELECT COUNT(*) FROM prompts")
                prompt_count = cursor.fetchone()[0]
                
                if user_count > 0 and prompt_count > 0:
                    print("Banco de dados já está configurado!")
                    return
                
            # Se chegou aqui, precisa configurar o banco
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

            # Criar usuário admin se não existir
            print("\nVerificando usuário admin...")
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            if cursor.fetchone()[0] == 0:
                print("Criando usuário admin...")
                admin_password = "horizont2025"
                password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
                
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role)
                    VALUES (%s, %s, %s)
                """, ('admin', password_hash.decode('utf-8'), 'admin'))

            # Criar usuários iniciais se não existirem
            print("\nVerificando usuários iniciais...")
            initial_users = [
                ('carlos', '123456', 'user'),
                ('ana', '123456', 'user'),
                ('paulo', '123456', 'user')
            ]

            for username, password, role in initial_users:
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
                if cursor.fetchone()[0] == 0:
                    print(f"Criando usuário {username}...")
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, role)
                        VALUES (%s, %s, %s)
                    """, (username, password_hash.decode('utf-8'), role))

            # Criar prompt padrão se não existir
            print("\nVerificando prompt padrão...")
            cursor.execute("SELECT COUNT(*) FROM prompts WHERE is_active = TRUE")
            if cursor.fetchone()[0] == 0:
                print("Criando prompt padrão...")
                with open('config.json', 'r', encoding='utf-8') as f:
                    import json
                    config = json.load(f)
                    default_prompt = config.get('claude_prompt', '')
                    
                    cursor.execute("""
                        INSERT INTO prompts (name, description, content, created_by, updated_by, is_active)
                        VALUES (%s, %s, %s, %s, %s, TRUE)
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