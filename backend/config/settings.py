from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Banco de Dados
    database_url: str = Field(default="sqlite:///./fasitech.db")

    # Google APIs
    google_credentials_base64: str = Field(default="")
    google_credentials_fasi_base64: str = Field(default="")

    # Email
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")

    # API Keys
    api_key: str = Field(default="")
    raw_social_api_key: str = Field(default="")
    admin_api_keys: str = Field(default="")  # CSV de tokens admin

    # AI / RAG
    gemini_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    ollama_base_url: str = Field(default="http://localhost:11434")

    # SIGAA
    sigaa_url: str = Field(default="")
    login: str = Field(default="")
    senha: str = Field(default="")
    fasi_token: str = Field(default="")  # Token de acesso admin (Gestor de Alertas, Lançamento)

    # Drive folders — um por formulário
    acc_folder_id: str = Field(default="")
    tcc_folder_id: str = Field(default="")
    estagio_folder_id: str = Field(default="")
    plano_folder_id: str = Field(default="")
    projetos_folder_id: str = Field(default="")

    # Sheets — um por formulário (mesmos nomes das seções do secrets.toml)
    acc_sheet_id: str = Field(default="")
    tcc_sheet_id: str = Field(default="")
    requerimento_tcc_sheet_id: str = Field(default="")
    estagio_sheet_id: str = Field(default="")
    plano_sheet_id: str = Field(default="")
    projetos_sheet_id: str = Field(default="")
    social_sheet_id: str = Field(default="")
    ofertas_sheet_id: str = Field(default="")

    # Destinatários por formulário (CSV de e-mails)
    acc_recipients: str = Field(default="")
    tcc_recipients: str = Field(default="")
    requerimento_tcc_recipients: str = Field(default="")
    estagio_recipients: str = Field(default="")
    plano_recipients: str = Field(default="")
    projetos_recipients: str = Field(default="")
    social_recipients: str = Field(default="")

    # Períodos letivos disponíveis (CSV, ex: "2026.1,2026.2,2026.3")
    periodos_letivos: str = Field(default="")

    # Destinatários globais (fallback / alertas acadêmicos)
    destinatarios: str = Field(default="")  # DESTINATARIOS no .env
    pareceristas: str = Field(default="")  # "Nome:email,Nome:email,..."

    # App
    environment: str = Field(default="development")
    api_base_url: str = Field(default="http://localhost:8000")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def admin_keys_list(self) -> list[str]:
        return [k.strip() for k in self.admin_api_keys.split(",") if k.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
