#!/usr/bin/env python3
"""
Script para adicionar novos documentos ao banco vetorial do RAG.

Este script permite:
1. Adicionar novos PDFs à pasta src/resources/
2. Limpar o banco vetorial existente para reprocessar todos os documentos
3. Verificar quais documentos estão atualmente indexados

Uso:
    python scripts/add_documents_to_rag.py --add documento.pdf
    python scripts/add_documents_to_rag.py --clear
    python scripts/add_documents_to_rag.py --list
"""

import sys
import argparse
import shutil
from pathlib import Path
from typing import List

def get_project_root() -> Path:
    """Encontra a raiz do projeto."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "src").exists() and (current / "requirements.txt").exists():
            return current
        current = current.parent
    return Path.cwd()

def get_resources_dir() -> Path:
    """Retorna o diretório resources do projeto."""
    project_root = get_project_root()
    resources_dir = project_root / "src" / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    return resources_dir

def get_cache_dir() -> Path:
    """Retorna o diretório de cache do RAG."""
    return Path.home() / ".cache" / "fasitech" / "rag"

def list_documents() -> List[Path]:
    """Lista todos os documentos PDF na pasta resources."""
    resources_dir = get_resources_dir()
    pdf_files = list(resources_dir.glob("*.pdf"))
    return pdf_files

def add_document(source_path: str) -> bool:
    """Adiciona um novo documento PDF à pasta resources."""
    source = Path(source_path)
    
    if not source.exists():
        print(f"❌ Arquivo não encontrado: {source}")
        return False
    
    if source.suffix.lower() != '.pdf':
        print(f"❌ Arquivo deve ser PDF: {source}")
        return False
    
    resources_dir = get_resources_dir()
    destination = resources_dir / source.name
    
    # Verificar se já existe
    if destination.exists():
        overwrite = input(f"Arquivo {source.name} já existe. Sobrescrever? (y/n): ")
        if overwrite.lower() != 'y':
            print("❌ Operação cancelada.")
            return False
    
    # Copiar arquivo
    try:
        shutil.copy2(source, destination)
        print(f"✅ Documento adicionado: {destination}")
        print(f"📁 Localização: {destination.absolute()}")
        
        # Informar sobre necessidade de rebuild
        print("\n⚠️  IMPORTANTE:")
        print("   Para indexar o novo documento, você precisa limpar o cache do RAG:")
        print(f"   python {__file__} --clear")
        print("   Ou reiniciar os containers para reprocessar todos os documentos.")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao copiar arquivo: {e}")
        return False

def clear_vector_cache() -> bool:
    """Limpa o cache do banco vetorial para forçar reprocessamento."""
    cache_dir = get_cache_dir()
    
    if not cache_dir.exists():
        print("✅ Cache já está limpo (não existe).")
        return True
    
    try:
        shutil.rmtree(cache_dir)
        print(f"✅ Cache do RAG limpo: {cache_dir}")
        print("\n📝 Na próxima inicialização do RAG:")
        print("   - Todos os PDFs em src/resources/ serão reprocessados")
        print("   - Novo banco vetorial será criado")
        print("   - Pode demorar alguns minutos na primeira vez")
        return True
    except Exception as e:
        print(f"❌ Erro ao limpar cache: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Gerenciar documentos no banco vetorial do RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s --list                    # Listar documentos atuais
  %(prog)s --add manual.pdf         # Adicionar novo documento  
  %(prog)s --clear                  # Limpar cache para reprocessar
        """
    )
    
    parser.add_argument(
        '--list', 
        action='store_true',
        help='Listar todos os documentos PDF atuais'
    )
    
    parser.add_argument(
        '--add',
        type=str,
        metavar='ARQUIVO.pdf',
        help='Adicionar um novo documento PDF'
    )
    
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Limpar cache do banco vetorial (força reprocessamento)'
    )
    
    args = parser.parse_args()
    
    if not any([args.list, args.add, args.clear]):
        parser.print_help()
        return
    
    print("🔧 GERENCIADOR DE DOCUMENTOS RAG")
    print("=" * 40)
    
    # Listar documentos
    if args.list:
        documents = list_documents()
        resources_dir = get_resources_dir()
        
        print(f"📁 Diretório: {resources_dir}")
        
        if documents:
            print(f"\n📄 Documentos encontrados ({len(documents)}):")
            for i, doc in enumerate(documents, 1):
                size_mb = doc.stat().st_size / (1024 * 1024)
                print(f"   {i}. {doc.name} ({size_mb:.1f}MB)")
        else:
            print("\n⚠️  Nenhum documento PDF encontrado.")
            print("   Use --add para adicionar documentos.")
    
    # Adicionar documento
    if args.add:
        print(f"\n📥 Adicionando documento: {args.add}")
        success = add_document(args.add)
        if success:
            print("\n📋 Próximos passos:")
            print("   1. Execute: python scripts/add_documents_to_rag.py --clear")
            print("   2. Reinicie o RAG ou containers")
            print("   3. Teste com uma pergunta sobre o novo documento")
    
    # Limpar cache
    if args.clear:
        print(f"\n🧹 Limpando cache do banco vetorial...")
        confirm = input("Isso forçará o reprocessamento de todos os documentos. Continuar? (y/n): ")
        if confirm.lower() == 'y':
            clear_vector_cache()
        else:
            print("❌ Operação cancelada.")

if __name__ == "__main__":
    main()