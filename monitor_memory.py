#!/usr/bin/env python3
"""
Script para monitorar o uso de memória do sistema
Útil para identificar problemas de memória no plano $7 do Render
"""

import psutil
import time
import os
from datetime import datetime

def monitor_memory():
    print("=== Monitor de Memória - Horizont IA ===")
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    while True:
        try:
            # Informações de memória
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Informações de CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Informações de disco
            disk = psutil.disk_usage('/')
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"RAM: {memory.percent}% ({memory.used // 1024 // 1024}MB/{memory.total // 1024 // 1024}MB) | "
                  f"CPU: {cpu_percent}% | "
                  f"SWAP: {swap.percent}% | "
                  f"DISK: {disk.percent}%")
            
            # Alertas
            if memory.percent > 80:
                print(f"⚠️  ALERTA: Uso de RAM alto: {memory.percent}%")
            
            if swap.percent > 50:
                print(f"⚠️  ALERTA: Uso de SWAP alto: {swap.percent}%")
            
            if cpu_percent > 80:
                print(f"⚠️  ALERTA: Uso de CPU alto: {cpu_percent}%")
            
            time.sleep(5)  # Verificar a cada 5 segundos
            
        except KeyboardInterrupt:
            print("\nMonitoramento interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"Erro no monitoramento: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_memory() 