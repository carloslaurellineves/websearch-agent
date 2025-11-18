"""Cliente para integração com SharePoint."""

import logging
import time
from pathlib import Path
from typing import Optional

from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential

from src.config.settings import settings

logger = logging.getLogger(__name__)


class SharePointClient:
    """Cliente para autenticação e download de arquivos do SharePoint."""

    def __init__(
        self,
        url: Optional[str] = None,
        site: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Inicializa o cliente SharePoint.

        Args:
            url: URL base do SharePoint (usa settings se não fornecido)
            site: Caminho do site (usa settings se não fornecido)
            username: Usuário (usa settings se não fornecido)
            password: Senha (usa settings se não fornecido)
        """
        self.url = url or settings.sharepoint_url
        self.site = site or settings.sharepoint_site
        self.username = username or settings.sharepoint_username
        self.password = password or settings.sharepoint_password
        self.ctx: Optional[ClientContext] = None

    def authenticate(self, max_retries: Optional[int] = None) -> bool:
        """
        Autentica no SharePoint com retry e backoff.

        Args:
            max_retries: Número máximo de tentativas (usa settings se não fornecido)

        Returns:
            True se autenticação bem-sucedida, False caso contrário
        """
        max_retries = max_retries or settings.max_retries

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Tentando autenticar no SharePoint (tentativa {attempt}/{max_retries})...")
                site_url = f"{self.url}{self.site}"
                credentials = UserCredential(self.username, self.password)
                self.ctx = ClientContext(site_url).with_credentials(credentials)
                # Testa a conexão
                self.ctx.web.get().execute_query()
                logger.info("Autenticação no SharePoint bem-sucedida")
                return True
            except Exception as e:
                logger.warning(f"Erro na autenticação (tentativa {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Backoff exponencial
                    logger.info(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    logger.error("Falha na autenticação do SharePoint após todas as tentativas")
                    return False

        return False

    def download_file(
        self,
        library_name: str,
        file_name: str,
        local_path: Path,
        max_retries: Optional[int] = None,
    ) -> bool:
        """
        Baixa um arquivo do SharePoint.

        Args:
            library_name: Nome da biblioteca de documentos
            file_name: Nome do arquivo
            local_path: Caminho local onde salvar o arquivo
            max_retries: Número máximo de tentativas (usa settings se não fornecido)

        Returns:
            True se download bem-sucedido, False caso contrário
        """
        if not self.ctx:
            logger.error("Cliente não autenticado. Chame authenticate() primeiro.")
            return False

        max_retries = max_retries or settings.max_retries

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Baixando arquivo {file_name} (tentativa {attempt}/{max_retries})...")
                # Garante que o diretório existe
                local_path.parent.mkdir(parents=True, exist_ok=True)

                # Obtém a biblioteca de documentos
                library = self.ctx.web.lists.get_by_title(library_name)
                # Obtém o arquivo
                file = library.root_folder.files.get_by_url(file_name)
                # Baixa o conteúdo
                file_content = file.get_content().execute_query()

                # Salva localmente
                with open(local_path, "wb") as f:
                    f.write(file_content.value)

                logger.info(f"Arquivo baixado com sucesso: {local_path}")
                return True
            except Exception as e:
                logger.warning(f"Erro ao baixar arquivo (tentativa {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    logger.error("Falha ao baixar arquivo após todas as tentativas")
                    return False

        return False

    def download_excel_file(
        self,
        library_name: Optional[str] = None,
        file_name: Optional[str] = None,
        local_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Baixa o arquivo Excel configurado do SharePoint.

        Args:
            library_name: Nome da biblioteca (usa settings se não fornecido)
            file_name: Nome do arquivo (usa settings se não fornecido)
            local_path: Caminho local (usa temp se não fornecido)

        Returns:
            Caminho do arquivo baixado ou None em caso de erro
        """
        library_name = library_name or settings.sharepoint_library
        file_name = file_name or settings.sharepoint_file

        if local_path is None:
            local_path = Path("./temp") / file_name

        if self.download_file(library_name, file_name, local_path):
            return local_path
        return None

