import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import bcrypt
from datetime import datetime
import uuid
import json

load_dotenv()

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return connection
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def verify_user(username, password):
    connection = get_db_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, username, password_hash, role 
            FROM users 
            WHERE username = %s AND is_active = TRUE
        """, (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Atualizar último login
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (user['id'],))
            connection.commit()
            
            return {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        return None
    except Error as e:
        print(f"Erro ao verificar usuário: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def get_all_users():
    connection = get_db_connection()
    if connection is None:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, username, role, created_at, last_login, is_active
            FROM users
            WHERE username != 'admin' AND is_active = TRUE
            ORDER BY created_at DESC
        """)
        return cursor.fetchall()
    except Error as e:
        print(f"Erro ao buscar usuários: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def create_user(username, password, role='user'):
    connection = get_db_connection()
    if connection is None:
        print("Erro: Não foi possível obter conexão com o banco")
        return False
    
    try:
        cursor = connection.cursor()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        print(f"Tentando criar usuário: {username} com role: {role}")
        cursor.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (%s, %s, %s)
        """, (username, password_hash.decode('utf-8'), role))
        
        connection.commit()
        print(f"Usuário {username} criado com sucesso!")
        return True
    except Error as e:
        print(f"Erro detalhado ao criar usuário: {str(e)}")
        if "Duplicate entry" in str(e):
            print("Erro: Username já existe")
        return False
    except Exception as e:
        print(f"Erro inesperado ao criar usuário: {str(e)}")
        return False
    finally:
        cursor.close()
        connection.close()

def delete_user(username):
    connection = get_db_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        # Soft delete - apenas marca como inativo
        cursor.execute("""
            UPDATE users 
            SET is_active = FALSE 
            WHERE username = %s AND username != 'admin'
        """, (username,))
        connection.commit()
        return True
    except Error as e:
        print(f"Erro ao deletar usuário: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_user_chats(username):
    connection = get_db_connection()
    if connection is None:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Primeiro buscar os chats
        cursor.execute("""
            SELECT c.id, c.title, c.created_at, c.updated_at, c.last_message_at
            FROM chats c
            JOIN users u ON c.user_id = u.id
            WHERE u.username = %s
            ORDER BY COALESCE(c.last_message_at, '1970-01-01') DESC
        """, (username,))
        
        chats = cursor.fetchall()
        
        # Para cada chat, buscar suas mensagens
        for chat in chats:
            cursor.execute("""
                SELECT role, content, created_at
                FROM chat_messages
                WHERE chat_id = %s
                ORDER BY created_at ASC
            """, (chat['id'],))
            
            chat['messages'] = cursor.fetchall()
        
        return chats
    except Error as e:
        print(f"Erro ao buscar chats: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def create_chat(username, title):
    connection = get_db_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Buscar ID do usuário
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return None
        
        chat_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO chats (id, user_id, title, context, last_message_at)
            VALUES (%s, %s, %s, '[]', CURRENT_TIMESTAMP)
        """, (chat_id, user[0], title))
        
        connection.commit()
        return chat_id
    except Error as e:
        print(f"Erro ao criar chat: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def add_message_to_chat(chat_id, role, content):
    print(f"Tentando adicionar mensagem ao chat {chat_id}")
    print(f"Role: {role}")
    print(f"Content length: {len(content) if content else 0}")
    
    connection = get_db_connection()
    if connection is None:
        print("Erro: Não foi possível obter conexão com o banco")
        return False
    
    try:
        cursor = connection.cursor()
        
        # Verificar se o chat existe
        print("Verificando se o chat existe...")
        cursor.execute("SELECT id FROM chats WHERE id = %s", (chat_id,))
        chat = cursor.fetchone()
        if not chat:
            print(f"Erro: Chat {chat_id} não encontrado")
            return False
        
        print("Chat encontrado, adicionando mensagem...")
        # Adicionar mensagem ao histórico do chat
        try:
            cursor.execute("""
                INSERT INTO chat_messages (chat_id, role, content)
                VALUES (%s, %s, %s)
            """, (chat_id, role, content))
            print("Mensagem inserida com sucesso")
        except Exception as insert_error:
            print(f"Erro ao inserir mensagem: {insert_error}")
            connection.rollback()
            return False
        
        print("Mensagem adicionada, atualizando timestamp...")
        # Apenas atualizar o timestamp da última mensagem (mais rápido)
        try:
            cursor.execute("""
                UPDATE chats 
                SET last_message_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (chat_id,))
            print("Timestamp atualizado com sucesso")
        except Exception as update_error:
            print(f"Erro ao atualizar timestamp: {update_error}")
            connection.rollback()
            return False
        
        try:
            connection.commit()
            print("Commit realizado com sucesso!")
        except Exception as commit_error:
            print(f"Erro no commit: {commit_error}")
            connection.rollback()
            return False
            
        print("Mensagem salva com sucesso!")
        return True
    except Error as e:
        print(f"Erro MySQL ao adicionar mensagem: {str(e)}")
        if connection:
            try:
                connection.rollback()
            except:
                pass
        return False
    except Exception as e:
        print(f"Erro inesperado ao adicionar mensagem: {str(e)}")
        if connection:
            try:
                connection.rollback()
            except:
                pass
        return False
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception as close_error:
            print(f"Erro ao fechar conexão: {close_error}")

def get_chat_messages(chat_id):
    connection = get_db_connection()
    if connection is None:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT role, content, created_at
            FROM chat_messages
            WHERE chat_id = %s
            ORDER BY created_at ASC
        """, (chat_id,))
        
        return cursor.fetchall()
    except Error as e:
        print(f"Erro ao buscar mensagens: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

def delete_chat(chat_id):
    connection = get_db_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM chats WHERE id = %s", (chat_id,))
        connection.commit()
        return True
    except Error as e:
        print(f"Erro ao deletar chat: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_prompt():
    connection = get_db_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT content
            FROM prompts
            WHERE is_active = TRUE
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        return result['content'] if result else None
    except Error as e:
        print(f"Erro ao buscar prompt: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def update_prompt(content, username):
    connection = get_db_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Primeiro, desativar todos os prompts anteriores
        cursor.execute("""
            UPDATE prompts 
            SET is_active = FALSE 
            WHERE is_active = TRUE
        """)
        
        # Depois, inserir o novo prompt como ativo
        cursor.execute("""
            INSERT INTO prompts (name, description, content, created_by, updated_by, is_active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
        """, ('Prompt Atualizado', 'Atualização do prompt do sistema', content, username, username))
        
        connection.commit()
        return True
    except Error as e:
        print(f"Erro ao atualizar prompt: {e}")
        return False
    finally:
        cursor.close()
        connection.close() 