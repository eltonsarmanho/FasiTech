#!/usr/bin/env python3
"""
Script para verificar dependências do processador ACC no servidor.
Execute este script no servidor para diagnosticar problemas.
"""

import sys
import os
from pathlib import Path

print("🔍 VERIFICADOR DE DEPENDÊNCIAS ACC")
print("="*50)

def verificar_python():
    """Verifica versão do Python"""
    print(f"🐍 Python: {sys.version}")
    print(f"   Executável: {sys.executable}")
    return True

def verificar_env_vars():
    """Verifica variáveis de ambiente"""
    print("\n🔧 Variáveis de Ambiente:")
    
    # GOOGLE_API_KEY
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"   ✅ GOOGLE_API_KEY: {api_key[:10]}...{api_key[-5:]}")
    else:
        print("   ❌ GOOGLE_API_KEY: NÃO CONFIGURADA")
        return False
    
    # PYTHONPATH
    python_path = os.getenv("PYTHONPATH", "")
    print(f"   📂 PYTHONPATH: {python_path or 'NÃO DEFINIDO'}")
    
    return True

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    print("\n📦 Dependências Python:")
    
    dependencias = [
        ("os", "Módulo padrão"),
        ("pathlib", "Módulo padrão"),
        ("typing", "Módulo padrão"),
        ("tempfile", "Módulo padrão"),
        ("dotenv", "python-dotenv"),
        ("pdf2image", "pdf2image"),
        ("PIL", "Pillow"),
        ("agno", "agno"),
        ("agno.agent", "agno - Agent"),
        ("agno.models.google", "agno - Gemini"),
        ("agno.media", "agno - Image")
    ]
    
    todos_ok = True
    
    for modulo, descricao in dependencias:
        try:
            __import__(modulo)
            print(f"   ✅ {modulo} ({descricao})")
        except ImportError as e:
            print(f"   ❌ {modulo} ({descricao}) - ERRO: {e}")
            todos_ok = False
    
    return todos_ok

def verificar_sistema():
    """Verifica recursos do sistema"""
    print("\n💻 Sistema:")
    
    # Diretório temporário
    import tempfile
    temp_dir = tempfile.gettempdir()
    print(f"   📁 Temp dir: {temp_dir}")
    
    # Verificar se pode criar arquivos no temp
    try:
        test_file = os.path.join(temp_dir, "test_acc.tmp")
        with open(test_file, 'w') as f:
            f.write("teste")
        os.remove(test_file)
        print("   ✅ Escrita em temp: OK")
    except Exception as e:
        print(f"   ❌ Escrita em temp: ERRO - {e}")
        return False
    
    # Verificar configuração de upload do Streamlit
    try:
        config_path = ".streamlit/config.toml"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_content = f.read()
                if "maxUploadSize" in config_content:
                    import re
                    match = re.search(r'maxUploadSize\s*=\s*(\d+)', config_content)
                    if match:
                        size = int(match.group(1))
                        print(f"   📤 Limite upload Streamlit: {size}MB")
                    else:
                        print("   📤 maxUploadSize encontrado mas valor não identificado")
                else:
                    print("   ⚠️ maxUploadSize não configurado no Streamlit")
        else:
            print("   ⚠️ Arquivo config.toml não encontrado")
    except Exception as e:
        print(f"   ⚠️ Erro ao verificar config Streamlit: {e}")
    
    # Verificar memória disponível (se psutil estiver disponível)
    try:
        import psutil
        mem = psutil.virtual_memory()
        print(f"   💾 Memória: {mem.available / 1024**3:.1f}GB disponível de {mem.total / 1024**3:.1f}GB")
    except ImportError:
        print("   💾 Memória: psutil não disponível")
    
    return True

def testar_gemini():
    """Testa conexão com Gemini"""
    print("\n🤖 Teste Gemini:")
    
    try:
        from agno.models.google import Gemini
        modelo = Gemini(id="gemini-2.5-flash")
        print("   ✅ Modelo Gemini criado com sucesso")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao criar modelo Gemini: {e}")
        return False

def testar_pdf2image():
    """Testa pdf2image e poppler"""
    print("\n📄 Teste PDF2Image e Poppler:")
    
    # Verificar poppler primeiro
    import shutil
    if shutil.which("pdftoppm"):
        print("   ✅ poppler-utils encontrado")
    else:
        print("   ❌ poppler-utils NÃO ENCONTRADO")
        print("       Instale com: sudo apt-get install poppler-utils")
        return False
    
    try:
        from pdf2image import convert_from_path
        print("   ✅ pdf2image importado")
        
        # Tentar localizar um PDF de teste (se existir)
        pdf_test_paths = [
            "/tmp/test.pdf",
            "./test.pdf",
            "../test.pdf"
        ]
        
        pdf_encontrado = None
        for path in pdf_test_paths:
            if os.path.exists(path):
                pdf_encontrado = path
                break
        
        if pdf_encontrado:
            print(f"   📋 PDF de teste encontrado: {pdf_encontrado}")
            try:
                images = convert_from_path(pdf_encontrado, dpi=150)
                print(f"   ✅ Conversão OK: {len(images)} páginas")
            except Exception as e:
                print(f"   ⚠️ Erro na conversão: {e}")
                if "poppler" in str(e).lower():
                    print("       Instale poppler: sudo apt-get install poppler-utils")
                return False
        else:
            print("   📋 Nenhum PDF de teste encontrado")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Erro ao importar pdf2image: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erro inesperado: {e}")
        if "poppler" in str(e).lower():
            print("       Instale poppler: sudo apt-get install poppler-utils")
        return False

def main():
    """Executa todos os testes"""
    print(f"📍 Executando em: {os.getcwd()}")
    print(f"📍 Script: {__file__}")
    
    resultados = []
    
    # Executar testes
    resultados.append(("Python", verificar_python()))
    resultados.append(("Variáveis de Ambiente", verificar_env_vars()))
    resultados.append(("Dependências", verificar_dependencias()))
    resultados.append(("Sistema", verificar_sistema()))
    resultados.append(("Gemini", testar_gemini()))
    resultados.append(("PDF2Image", testar_pdf2image()))
    
    # Resumo final
    print("\n" + "="*50)
    print("📊 RESUMO FINAL:")
    print("="*50)
    
    todos_ok = True
    for nome, resultado in resultados:
        status = "✅ OK" if resultado else "❌ FALHA"
        print(f"   {status} {nome}")
        if not resultado:
            todos_ok = False
    
    print("\n" + "="*50)
    if todos_ok:
        print("🎉 TUDO OK! O processador ACC deve funcionar.")
    else:
        print("⚠️  PROBLEMAS ENCONTRADOS! Corrija os itens marcados com ❌")
        print("\nSugestões:")
        print("- Instale dependências: pip install python-dotenv pdf2image pillow agno")
        print("- Configure GOOGLE_API_KEY no arquivo .env")
        print("- Verifique permissões de escrita em /tmp")
    print("="*50)

if __name__ == "__main__":
    main()