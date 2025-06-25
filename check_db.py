import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def check_database():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        
        if connection.is_connected():
            print("Conexão bem sucedida!")
            cursor = connection.cursor()
            
            # Listar todas as tabelas
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("\nTabelas existentes:")
            for table in tables:
                print(f"- {table[0]}")
                
                # Mostrar estrutura de cada tabela
                cursor.execute(f"DESCRIBE {table[0]}")
                columns = cursor.fetchall()
                print("  Colunas:")
                for column in columns:
                    print(f"  - {column[0]}: {column[1]}")
                print()
            
            # Verificar usuários
            cursor.execute("SELECT username, role FROM users")
            users = cursor.fetchall()
            print("\nUsuários cadastrados:")
            for user in users:
                print(f"- {user[0]} ({user[1]})")
            
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConexão fechada.")

if __name__ == "__main__":
    check_database() 