#!/usr/bin/env python3
"""
Script para gerenciar API keys da FasiTech API.
Permite gerar novas API keys e testar endpoints.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.middleware.auth import generate_api_key, hash_api_key, VALID_API_KEYS


def gerar_nova_api_key(nome_cliente: str = "Cliente Teste") -> tuple[str, str]:
    """
    Gera uma nova API key.
    
    Args:
        nome_cliente: Nome do cliente para a API key
        
    Returns:
        Tupla com (api_key, hash_da_api_key)
    """
    api_key, key_hash = generate_api_key()
    
    print(f"\n🔑 Nova API Key gerada:")
    print(f"   Cliente: {nome_cliente}")
    print(f"   API Key: {api_key}")
    print(f"   Hash: {key_hash}")
    print(f"\n📝 Para usar esta API key, adicione ao código:")
    print(f"   VALID_API_KEYS['{key_hash}'] = {{")
    print(f"       'name': '{nome_cliente}',")
    print(f"       'permissions': ['read']")
    print(f"   }}")
    
    return api_key, key_hash


def listar_api_keys():
    """Lista todas as API keys válidas."""
    print(f"\n📋 API Keys válidas ({len(VALID_API_KEYS)}):")
    for i, (key_hash, info) in enumerate(VALID_API_KEYS.items(), 1):
        print(f"   {i}. {info['name']}")
        print(f"      Hash: {key_hash[:16]}...")
        print(f"      Permissões: {', '.join(info['permissions'])}")
        print()


def testar_endpoint(api_key: str, base_url: str = "http://localhost:8000"):
    """
    Testa endpoints da API social.
    
    Args:
        api_key: API key para autenticação
        base_url: URL base da API
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🧪 Testando API em {base_url}")
    print(f"   API Key: {api_key[:20]}...")
    
    # Teste 1: Health check
    print(f"\n1. Testando health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print(f"   ✅ Health check OK: {response.json()}")
        else:
            print(f"   ❌ Health check falhou: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro na conexão: {e}")
        return
    
    # Teste 2: Health check da API social
    print(f"\n2. Testando health check da API social...")
    try:
        response = requests.get(f"{base_url}/api/v1/dados-sociais/health", headers=headers)
        if response.status_code == 200:
            print(f"   ✅ Health check social OK: {response.json()}")
        else:
            print(f"   ❌ Health check social falhou: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 3: Opções de filtros
    print(f"\n3. Testando opções de filtros...")
    try:
        response = requests.get(f"{base_url}/api/v1/dados-sociais/opcoes", headers=headers)
        if response.status_code == 200:
            opcoes = response.json()
            print(f"   ✅ Opções obtidas:")
            for campo, valores in opcoes.items():
                print(f"      {campo}: {len(valores)} opções")
        else:
            print(f"   ❌ Falhou: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 4: Consulta de dados sociais (primeira página)
    print(f"\n4. Testando consulta de dados sociais...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/dados-sociais?pagina=1&por_pagina=5", 
            headers=headers
        )
        if response.status_code == 200:
            dados = response.json()
            print(f"   ✅ Dados obtidos:")
            print(f"      Total de registros: {dados['total']}")
            print(f"      Página: {dados['pagina']}")
            print(f"      Registros nesta página: {len(dados['dados'])}")
            if dados['dados']:
                primeiro = dados['dados'][0]
                print(f"      Exemplo - Matrícula: {primeiro['matricula']}, Período: {primeiro['periodo']}")
        else:
            print(f"   ❌ Falhou: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 5: Estatísticas
    print(f"\n5. Testando estatísticas...")
    try:
        response = requests.get(f"{base_url}/api/v1/dados-sociais/estatisticas", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Estatísticas obtidas:")
            print(f"      Total de registros: {stats['total_registros']}")
            print(f"      Percentual PCD: {stats['percentual_pcd']}%")
            print(f"      Percentual que trabalha: {stats['percentual_trabalham']}%")
        else:
            print(f"   ❌ Falhou: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste 6: Teste com filtros
    print(f"\n6. Testando consulta com filtros...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/dados-sociais?periodo=2025.(3 e 4)&por_pagina=3", 
            headers=headers
        )
        if response.status_code == 200:
            dados = response.json()
            print(f"   ✅ Dados filtrados obtidos:")
            print(f"      Total com filtro: {dados['total']}")
            print(f"      Registros nesta página: {len(dados['dados'])}")
        else:
            print(f"   ❌ Falhou: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")


def main():
    """Função principal do script."""
    print("🚀 FasiTech API - Gerenciador de API Keys")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nUso:")
        print("  python api_manager.py gerar [nome_cliente]  - Gerar nova API key")
        print("  python api_manager.py listar               - Listar API keys")
        print("  python api_manager.py testar <api_key>     - Testar API")
        print("  python api_manager.py exemplo              - Mostrar exemplo de uso")
        return
    
    comando = sys.argv[1].lower()
    
    if comando == "gerar":
        nome_cliente = sys.argv[2] if len(sys.argv) > 2 else "Cliente Teste"
        gerar_nova_api_key(nome_cliente)
    
    elif comando == "listar":
        listar_api_keys()
    
    elif comando == "testar":
        if len(sys.argv) < 3:
            print("❌ API key é obrigatória para teste")
            return
        api_key = sys.argv[2]
        base_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8000"
        testar_endpoint(api_key, base_url)
    
    elif comando == "exemplo":
        print("\n📖 Exemplo de uso da API:")
        print("\n1. Gerar API key:")
        print("   python api_manager.py gerar 'Meu Cliente'")
        print("\n2. Consultar dados sociais:")
        print("   curl -H 'Authorization: Bearer sua_api_key' \\")
        print("        'http://localhost:8000/api/v1/dados-sociais?pagina=1&por_pagina=10'")
        print("\n3. Ver estatísticas:")
        print("   curl -H 'Authorization: Bearer sua_api_key' \\")
        print("        'http://localhost:8000/api/v1/dados-sociais/estatisticas'")
        print("\n4. Usar filtros:")
        print("   curl -H 'Authorization: Bearer sua_api_key' \\")
        print("        'http://localhost:8000/api/v1/dados-sociais?cor_etnia=Pardo&trabalho=Sim'")
        
        # Mostrar API key de exemplo
        print(f"\n🔑 API Key de exemplo (já configurada):")
        print(f"   fasitech_api_2024_social_data")
    
    else:
        print(f"❌ Comando '{comando}' não reconhecido")


if __name__ == "__main__":
    main()