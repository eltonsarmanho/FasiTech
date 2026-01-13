#!/usr/bin/env python3
"""Script para inicializar banco de dados remotamente na VM."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.engine import init_db, engine
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def create_database_if_not_exists():
    """Cria o banco fasitech se não existir."""
    print("🔧 Verificando se banco 'fasitech' existe...")
    
    # URL para conectar ao postgres padrão
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", "5432")
    
    if not db_password:
        raise ValueError("DB_PASSWORD environment variable is required")
    
    base_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"
    
    try:
        base_engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
        
        with base_engine.connect() as conn:
            # Verificar se o banco existe
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'fasitech'")
            )
            exists = result.fetchone() is not None
            
            if not exists:
                print("📦 Criando banco 'fasitech'...")
                conn.execute(text("CREATE DATABASE fasitech"))
                print("✅ Banco 'fasitech' criado!")
            else:
                print("ℹ️  Banco 'fasitech' já existe")
        
        base_engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")
        return False

def init_remote_database():
    """Inicializa banco de dados na VM remota."""
    print("=" * 60)
    print("INICIALIZANDO BANCO DE DADOS NA VM (72.60.6.113)")
    print("=" * 60)
    
    # Definir URL para a VM
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "fasitech")
    
    if not db_password:
        raise ValueError("DB_PASSWORD environment variable is required")
    
    os.environ["DATABASE_URL"] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        # 1. Criar banco se não existir
        if not create_database_if_not_exists():
            return False
        
        # 2. Testar conexão
        print("\n🔗 Testando conexão...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            print(f"   ✅ Conexão bem-sucedida! (result: {result[0]})")
        
        # 3. Criar tabelas
        print("\n🏗️  Criando tabelas...")
        init_db()
        
        print("\n" + "=" * 60)
        print("✅ BANCO DE DADOS INICIALIZADO COM SUCESSO!")
        print("=" * 60)
        print("\n📋 Tabelas criadas:")
        print("   - social_submissions")
        print("   - tcc_submissions") 
        print("   - acc_submissions")
        print("   - projetos_submissions")
        print("   - plano_ensino_submissions")
        print("   - estagio_submissions")
        print("   - requerimento_tcc_submissions")
        print("   - avaliacao_gestao_submissions")
        
        return True
        
    except OperationalError as e:
        error_msg = str(e)
        print(f"\n❌ ERRO DE CONEXÃO: {e}")
        
        if "Connection refused" in error_msg or "timed out" in error_msg:
            print("\n💡 POSSÍVEIS SOLUÇÕES:")
            print("   1. Verificar se PostgreSQL está rodando na VM:")
            print("      ssh root@72.60.6.113")
            print("      systemctl status postgresql")
            print("      systemctl start postgresql")
            print("\n   2. Verificar configuração do PostgreSQL:")
            print("      nano /etc/postgresql/*/main/postgresql.conf")
            print("      listen_addresses = '*'")
            print("\n   3. Verificar pg_hba.conf:")
            print("      nano /etc/postgresql/*/main/pg_hba.conf")
            print("      host all all 0.0.0.0/0 md5")
            print("\n   4. Reiniciar PostgreSQL:")
            print("      systemctl restart postgresql")
        
        return False
        
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_remote_database()
    sys.exit(0 if success else 1)