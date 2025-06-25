from database import verify_user
import bcrypt
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def test_login():
    print("\n🔑 Testando login...")
    
    # Testar login do admin
    print("\nTestando login do admin...")
    result = verify_user('admin', 'horizont2025')
    print(f"Resultado: {result}")
    
    # Testar login de usuário normal
    print("\nTestando login do carlos...")
    result = verify_user('carlos', '123456')
    print(f"Resultado: {result}")
    
    # Testar login inválido
    print("\nTestando login inválido...")
    result = verify_user('usuario_inexistente', 'senha_errada')
    print(f"Resultado: {result}")
    
    # Verificar hash da senha diretamente no banco
    try:
        print("\n🔍 Verificando hash das senhas no banco...")
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT username, password_hash FROM users")
            users = cursor.fetchall()
            
            print("\nHashes armazenados:")
            for user in users:
                username = str(user.get('username', ''))
                password_hash = str(user.get('password_hash', ''))
                print(f"- {username}: {password_hash}")
                
            # Testar verificação de hash para cada usuário com sua senha correta
            print("\n✅ Testando verificação de hash...")
            test_users = {
                'admin': 'horizont2025',
                'carlos': '123456',
                'ana': '123456',
                'paulo': '123456'
            }
            
            for user in users:
                try:
                    username = str(user.get('username', ''))
                    password_hash = str(user.get('password_hash', ''))
                    correct_password = test_users.get(username)
                    
                    if correct_password and password_hash:
                        matches = bcrypt.checkpw(
                            correct_password.encode('utf-8'),
                            password_hash.encode('utf-8')
                        )
                        print(f"- {username} (senha: {correct_password}): {'✅' if matches else '❌'}")
                except Exception as e:
                    print(f"- {username}: Erro ao verificar hash: {e}")
            
    except Error as e:
        print(f"\n❌ Erro ao conectar ao banco de dados: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔒 Conexão fechada")

if __name__ == "__main__":
    test_login() 