#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

def fix_prompts():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            print("Corrigindo prompts duplicados...")
            
            # Desativar todos os prompts
            cursor.execute("UPDATE prompts SET is_active = FALSE")
            print("Todos os prompts desativados")
            
            # Ativar apenas o mais recente
            cursor.execute("""
                UPDATE prompts 
                SET is_active = TRUE 
                WHERE id = (
                    SELECT id FROM (
                        SELECT id FROM prompts 
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    ) as temp
                )
            """)
            print("Prompt mais recente ativado")
            
            connection.commit()
            print("✅ Prompts corrigidos!")
            
            # Verificar resultado
            cursor.execute("SELECT COUNT(*) FROM prompts WHERE is_active = TRUE")
            active_count = cursor.fetchone()[0]
            print(f"Prompts ativos: {active_count}")
                
    except Error as e:
        print(f"Erro ao conectar ao banco: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    fix_prompts() 