#!/usr/bin/env python3
"""
Script para testar a performance das operações de banco de dados
"""

import time
import uuid
from database import get_db_connection, add_message_to_chat, create_chat

def test_database_performance():
    print("=== Teste de Performance do Banco de Dados ===")
    
    # Teste 1: Conexão com o banco
    print("\n1. Testando conexão com o banco...")
    start_time = time.time()
    connection = get_db_connection()
    if connection:
        print(f"✓ Conexão estabelecida em {time.time() - start_time:.3f}s")
        connection.close()
    else:
        print("✗ Falha na conexão")
        return
    
    # Teste 2: Criar um chat de teste
    print("\n2. Testando criação de chat...")
    start_time = time.time()
    chat_id = create_chat("admin", "Teste de Performance")
    if chat_id:
        print(f"✓ Chat criado em {time.time() - start_time:.3f}s (ID: {chat_id})")
    else:
        print("✗ Falha ao criar chat")
        return
    
    # Teste 3: Adicionar mensagens
    print("\n3. Testando adição de mensagens...")
    
    # Mensagem pequena
    start_time = time.time()
    success = add_message_to_chat(chat_id, "user", "Teste de mensagem pequena")
    if success:
        print(f"✓ Mensagem pequena adicionada em {time.time() - start_time:.3f}s")
    else:
        print("✗ Falha ao adicionar mensagem pequena")
    
    # Mensagem grande (simulando resposta do Claude)
    large_message = "Esta é uma mensagem de teste muito longa " * 100  # ~3000 caracteres
    start_time = time.time()
    success = add_message_to_chat(chat_id, "assistant", large_message)
    if success:
        print(f"✓ Mensagem grande adicionada em {time.time() - start_time:.3f}s")
    else:
        print("✗ Falha ao adicionar mensagem grande")
    
    # Teste 4: Múltiplas mensagens em sequência
    print("\n4. Testando múltiplas mensagens...")
    start_time = time.time()
    for i in range(5):
        success = add_message_to_chat(chat_id, "user", f"Mensagem de teste {i+1}")
        if not success:
            print(f"✗ Falha na mensagem {i+1}")
            break
    total_time = time.time() - start_time
    print(f"✓ 5 mensagens adicionadas em {total_time:.3f}s (média: {total_time/5:.3f}s por mensagem)")
    
    print("\n=== Teste Concluído ===")

if __name__ == "__main__":
    test_database_performance() 