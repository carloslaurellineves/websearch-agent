"""Leitor de arquivos Excel."""

import logging
from pathlib import Path
from typing import List

import pandas as pd

from src.models.software import Software

logger = logging.getLogger(__name__)


class ExcelReader:
    """Classe para ler arquivos Excel e extrair dados de softwares."""

    def __init__(self, file_path: Path):
        """
        Inicializa o leitor de Excel.

        Args:
            file_path: Caminho do arquivo Excel
        """
        self.file_path = file_path

    def read_softwares(self) -> List[Software]:
        """
        Lê o arquivo Excel e extrai a lista de softwares.

        Espera as seguintes colunas:
        - Coluna A: Nome do software
        - Coluna B: Versão do software
        - Coluna C: Status (Sim/Não)

        Returns:
            Lista de objetos Software

        Raises:
            FileNotFoundError: Se o arquivo não existir
            ValueError: Se o formato do arquivo for inválido
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.file_path}")

        try:
            logger.info(f"Lendo arquivo Excel: {self.file_path}")
            # Lê o Excel, assumindo que a primeira linha pode ser cabeçalho
            df = pd.read_excel(self.file_path, header=None)

            # Valida se tem pelo menos uma coluna
            if df.empty:
                logger.warning("Arquivo Excel está vazio")
                return []

            # Pega as primeiras 3 colunas (A, B, C)
            # Remove linhas completamente vazias
            df = df.iloc[:, :3].dropna(how="all")

            # Verifica se há dados
            if len(df) == 0:
                logger.warning("Nenhum dado encontrado no arquivo Excel")
                return []

            softwares = []
            for idx, row in df.iterrows():
                try:
                    # Extrai dados das colunas (índices 0, 1, 2)
                    nome = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                    versao = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
                    status = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None

                    # Ignora linhas vazias ou sem nome
                    if not nome or nome.lower() in ["nome", "software", ""]:
                        continue

                    # Normaliza valores None
                    if versao == "" or versao == "nan":
                        versao = None
                    if status == "" or status == "nan":
                        status = None

                    software = Software(
                        nome=nome,
                        versao=versao if versao else None,
                        status_original=status if status else None,
                    )
                    softwares.append(software)
                    logger.debug(f"Software lido: {software.nome} - {software.versao}")

                except Exception as e:
                    logger.warning(f"Erro ao processar linha {idx + 1}: {e}")
                    continue

            logger.info(f"Total de softwares lidos: {len(softwares)}")
            return softwares

        except Exception as e:
            logger.error(f"Erro ao ler arquivo Excel: {e}")
            raise ValueError(f"Erro ao processar arquivo Excel: {e}") from e

