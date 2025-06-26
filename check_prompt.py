#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

def check_prompt():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Verificar se há prompts ativos
            cursor.execute("""
                SELECT id, name, content, is_active, created_at, updated_at
                FROM prompts
                ORDER BY updated_at DESC
            """)
            
            prompts = cursor.fetchall()
            
            print(f"Encontrados {len(prompts)} prompts no banco:")
            for i, prompt in enumerate(prompts):
                print(f"\n--- Prompt {i+1} ---")
                print(f"ID: {prompt['id']}")
                print(f"Nome: {prompt['name']}")
                print(f"Ativo: {prompt['is_active']}")
                print(f"Criado: {prompt['created_at']}")
                print(f"Atualizado: {prompt['updated_at']}")
                print(f"Conteúdo (primeiros 200 chars): {prompt['content'][:200]}...")
            
            # Verificar prompt ativo
            cursor.execute("""
                SELECT content
                FROM prompts
                WHERE is_active = TRUE
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            
            active_prompt = cursor.fetchone()
            if active_prompt:
                print(f"\n✅ PROMPT ATIVO ENCONTRADO:")
                print(f"Conteúdo: {active_prompt['content'][:300]}...")
            else:
                print(f"\n❌ NENHUM PROMPT ATIVO ENCONTRADO!")
                
    except Error as e:
        print(f"Erro ao conectar ao banco: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    check_prompt() 