"""Script para criar o banco de dados fasitech se não existir."""
from __future__ import annotations

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError


def create_database():
    """Cria o banco de dados fasitech se não existir."""
    print("=" * 60)
    print("CRIAÇÃO DO BANCO DE DADOS FASITECH")
    print("=" * 60)
    
    # URL base para conectar ao PostgreSQL (sem especificar banco)
    base_url = "postgresql://postgres:adminadmin@localhost:5432/postgres"
    
    try:
        print("\n1. Conectando ao PostgreSQL...")
        engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
        
        with engine.connect() as conn:
            # Verificar se o banco já existe
            print("2. Verificando se banco 'fasitech' existe...")
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'fasitech'")
            )
            exists = result.fetchone() is not None
            
            if exists:
                print("   ✅ Banco 'fasitech' já existe!")
            else:
                print("   ℹ️  Banco 'fasitech' não encontrado. Criando...")
                conn.execute(text("CREATE DATABASE fasitech"))
                print("   ✅ Banco 'fasitech' criado com sucesso!")
        
        engine.dispose()
        
        # Testar conexão com o banco criado
        print("\n3. Testando conexão com banco 'fasitech'...")
        test_url = "postgresql://postgres:adminadmin@localhost:5432/fasitech"
        test_engine = create_engine(test_url)
        
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            print(f"   ✅ Conexão bem-sucedida! (result: {result[0]})")
        
        test_engine.dispose()
        
        print("\n" + "=" * 60)
        print("✅ BANCO DE DADOS PRONTO PARA USO!")
        print("=" * 60)
        print("\n🎯 Próximo passo: python scripts/test_database.py")
        
        return True
        
    except OperationalError as e:
        error_msg = str(e)
        print(f"\n❌ ERRO DE CONEXÃO: {e}")
        print("\n" + "=" * 60)
        print("POSSÍVEIS CAUSAS:")
        print("=" * 60)
        
        if "Connection refused" in error_msg:
            print("\n1. PostgreSQL não está rodando")
            print("   Soluções:")
            print("   - Inicie o PostgreSQL: sudo systemctl start postgresql")
            print("   - Ou ative o SSH tunnel: ./scripts/setup_ssh_tunnel.sh")
        
        elif "authentication failed" in error_msg or "password" in error_msg:
            print("\n2. Credenciais incorretas")
            print("   Verifique usuário/senha no DATABASE_URL")
            print("   Atual: postgresql://postgres:adminadmin@localhost:5432/postgres")
        
        else:
            print(f"\n3. Outro erro: {error_msg}")
        
        print("\n💡 Comando manual alternativo:")
        print("   psql -h localhost -U postgres")
        print("   CREATE DATABASE fasitech;")
        print("   \\q")
        
        return False
        
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)
