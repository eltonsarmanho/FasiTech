"""Script para testar conexão com banco de dados e criar tabelas."""
from __future__ import annotations

import sys
from pathlib import Path

# Adicionar raiz ao path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database.engine import init_db, engine
from sqlmodel import Session, select
from src.models.db_models import TccSubmission


def test_connection():
    """Testa conexão com o banco de dados."""
    print("=" * 60)
    print("TESTE DE CONEXÃO COM BANCO DE DADOS")
    print("=" * 60)
    
    try:
        # Tentar conectar
        print("\n1. Testando conexão...")
        with Session(engine) as session:
            result = session.exec(select(1)).first()
            print(f"   ✅ Conexão estabelecida com sucesso! (result: {result})")
        
        # Criar tabelas
        print("\n2. Criando/Verificando tabelas...")
        init_db()
        print("   ✅ Tabelas criadas/verificadas com sucesso!")
        
        # Listar tabelas criadas
        print("\n3. Tabelas disponíveis:")
        from sqlmodel import SQLModel
        for table_name in SQLModel.metadata.tables.keys():
            print(f"   📊 {table_name}")
        
        # Contar registros em TCC
        print("\n4. Contagem de registros:")
        with Session(engine) as session:
            tcc_count = len(session.exec(select(TccSubmission)).all())
            print(f"   📝 TCC Submissions: {tcc_count}")
        
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ERRO: {e}")
        
        print("\n" + "=" * 60)
        print("DIAGNÓSTICO:")
        print("=" * 60)
        
        if "does not exist" in error_msg and "fasitech" in error_msg:
            print("\n🔍 Problema: Banco de dados 'fasitech' não existe")
            print("\n✅ SOLUÇÃO:")
            print("   Execute o script de criação do banco:")
            print("   python scripts/create_database.py")
            print("\n   Ou crie manualmente:")
            print("   psql -h localhost -U postgres")
            print("   CREATE DATABASE fasitech;")
            print("   \\q")
        
        elif "Connection refused" in error_msg:
            print("\n🔍 Problema: PostgreSQL não está acessível")
            print("\n✅ SOLUÇÕES:")
            print("   1. Verificar se PostgreSQL está rodando:")
            print("      sudo systemctl status postgresql")
            print("\n   2. Se usar servidor remoto, ativar SSH tunnel:")
            print("      ./scripts/setup_ssh_tunnel.sh")
        
        elif "authentication failed" in error_msg or "password" in error_msg:
            print("\n🔍 Problema: Credenciais incorretas")
            print("\n✅ SOLUÇÃO:")
            print("   Verifique as credenciais no DATABASE_URL ou variáveis de ambiente")
            print("   Configure: DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME")
        
        else:
            print(f"\n🔍 Problema: {error_msg}")
            print("\nDetalhes do erro:")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    test_connection()
