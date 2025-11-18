"""Modelos de dados para softwares e resultados de pesquisa."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Software(BaseModel):
    """Modelo base para representar um software da planilha original."""

    nome: str = Field(..., description="Nome do software")
    versao: Optional[str] = Field(default=None, description="Versão do software")
    status_original: Optional[str] = Field(default=None, description="Status original (Sim/Não)")

    class Config:
        """Configuração do modelo."""

        frozen = False


class SoftwareResult(BaseModel):
    """Modelo estendido com resultados da pesquisa de licenciamento."""

    # Dados originais
    nome: str = Field(..., description="Nome do software")
    versao: Optional[str] = Field(default=None, description="Versão do software")
    status_original: Optional[str] = Field(default=None, description="Status original (Sim/Não)")

    # Resultados da pesquisa
    status_verificado: str = Field(..., description="Status verificado: Sim ou Não")
    data_pesquisa: datetime = Field(default_factory=datetime.now, description="Data e hora da pesquisa")
    fontes_utilizadas: list[str] = Field(default_factory=list, description="Lista de fontes utilizadas")
    links_fontes: list[str] = Field(default_factory=list, description="Lista de links das fontes")
    nivel_confianca: int = Field(..., ge=0, le=100, description="Nível de confiança (0-100)")
    resumo_pesquisa: Optional[str] = Field(default=None, description="Resumo da pesquisa realizada")

    def to_excel_row(self) -> dict:
        """Converte o resultado para um dicionário compatível com Excel."""
        return {
            "Nome": self.nome,
            "Versão": self.versao or "",
            "Status Original": self.status_original or "",
            "Status Verificado": self.status_verificado,
            "Data Pesquisa": self.data_pesquisa.strftime("%Y-%m-%d %H:%M:%S"),
            "Fontes": "; ".join(self.fontes_utilizadas) if self.fontes_utilizadas else "",
            "Links": "; ".join(self.links_fontes) if self.links_fontes else "",
            "Confiança": self.nivel_confianca,
            "Resumo": self.resumo_pesquisa or "",
        }

    @classmethod
    def from_software(cls, software: Software, **kwargs) -> "SoftwareResult":
        """Cria um SoftwareResult a partir de um Software."""
        return cls(
            nome=software.nome,
            versao=software.versao,
            status_original=software.status_original,
            **kwargs,
        )

