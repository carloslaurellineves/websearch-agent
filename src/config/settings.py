"""Configurações do sistema usando Pydantic Settings."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações do sistema carregadas de variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # SharePoint
    sharepoint_url: str = Field(..., description="URL base do SharePoint")
    sharepoint_site: str = Field(..., description="Caminho do site do SharePoint")
    sharepoint_library: str = Field(..., description="Biblioteca de documentos")
    sharepoint_file: str = Field(..., description="Nome do arquivo Excel")
    sharepoint_username: str = Field(..., description="Usuário do SharePoint")
    sharepoint_password: str = Field(..., description="Senha do SharePoint")

    # LLM Gateway
    llm_base_url: str = Field(..., description="URL base do gateway LLM")
    llm_api_key: str = Field(..., description="Token de API do gateway LLM")
    llm_model: str = Field(default="gpt-4o-mini", description="Modelo LLM a ser usado")

    # Arquivos
    output_file: str = Field(default="resultados_licenciamento.xlsx", description="Nome do arquivo de saída")
    output_dir: Path = Field(default=Path("./output"), description="Diretório de saída")

    # Configurações
    max_retries: int = Field(default=3, description="Número máximo de tentativas")
    request_timeout: int = Field(default=30, description="Timeout de requisições em segundos")
    confidence_threshold: int = Field(default=70, description="Limiar mínimo de confiança (0-100)")

    def __init__(self, **kwargs):
        """Inicializa as configurações e cria o diretório de saída se necessário."""
        super().__init__(**kwargs)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def output_path(self) -> Path:
        """Retorna o caminho completo do arquivo de saída."""
        return self.output_dir / self.output_file


# Instância global das configurações
settings = Settings()

