#!/usr/bin/env python3
"""
Script para limpar logs antigos e liberar espaço em disco
Útil para o plano $7 do Render que tem espaço limitado
"""

import os
import glob
import time
from datetime import datetime, timedelta

def cleanup_old_files():
    print("=== Limpeza de Arquivos Antigos - Horizont IA ===")
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Padrões de arquivos para limpar
    patterns = [
        "*.log",
        "*.tmp",
        "*.cache",
        "__pycache__/*",
        "*.pyc",
        "*.pyo"
    ]
    
    # Dias para manter arquivos
    days_to_keep = 7
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    total_size_freed = 0
    files_removed = 0
    
    for pattern in patterns:
        files = glob.glob(pattern, recursive=True)
        for file_path in files:
            try:
                # Verificar se é um arquivo
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        total_size_freed += file_size
                        files_removed += 1
                        print(f"Removido: {file_path} ({file_size} bytes)")
                
                # Verificar se é um diretório (para __pycache__)
                elif os.path.isdir(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        import shutil
                        dir_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                      for dirpath, dirnames, filenames in os.walk(file_path)
                                      for filename in filenames)
                        shutil.rmtree(file_path)
                        total_size_freed += dir_size
                        files_removed += 1
                        print(f"Removido diretório: {file_path} ({dir_size} bytes)")
                        
            except Exception as e:
                print(f"Erro ao processar {file_path}: {e}")
    
    print()
    print(f"Limpeza concluída:")
    print(f"- Arquivos removidos: {files_removed}")
    print(f"- Espaço liberado: {total_size_freed // 1024} KB")
    print(f"- Data de corte: {cutoff_date.strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    cleanup_old_files() 