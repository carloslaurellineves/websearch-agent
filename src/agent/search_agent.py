"""Agente de pesquisa com LangChain e DuckDuckGo Search."""

import json
import logging
import time
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import create_agent
from langchain_core.runnables import Runnable

from src.config.settings import settings
from src.models.software import Software, SoftwareResult
from src.agent.prompts import get_search_prompt_template

logger = logging.getLogger(__name__)


class SearchAgent:
    """Agente de pesquisa para verificação de licenciamento de softwares."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Inicializa o agente de pesquisa.

        Args:
            base_url: URL base do gateway LLM (usa settings se não fornecido)
            api_key: Token de API (usa settings se não fornecido)
            model: Modelo LLM (usa settings se não fornecido)
            timeout: Timeout de requisições (usa settings se não fornecido)
            max_retries: Número máximo de tentativas (usa settings se não fornecido)
        """
        self.base_url = base_url or settings.llm_base_url
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.timeout = timeout or settings.request_timeout
        self.max_retries = max_retries or settings.max_retries

        # Inicializa o LLM
        self.llm = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            temperature=0,
            timeout=self.timeout,
        )

        # Inicializa a ferramenta de busca
        self.search_tool = DuckDuckGoSearchRun()

        # Template de prompt reutilizável
        self.prompt = get_search_prompt_template()

        # Cria o agente
        self.agent = self._create_agent()

    def _create_agent(self) -> Runnable:
        """
        Cria o agente LangChain com as ferramentas usando create_agent.

        Returns:
            Runnable configurado
        """
        tools = [self.search_tool]

        return create_agent(model=self.llm, tools=tools)

    def search_software_licensing(
        self, software: Software, max_retries: Optional[int] = None
    ) -> SoftwareResult:
        """
        Pesquisa informações sobre licenciamento de um software.

        Args:
            software: Objeto Software a ser pesquisado
            max_retries: Número máximo de tentativas (usa settings se não fornecido)

        Returns:
            SoftwareResult com os resultados da pesquisa
        """
        max_retries = max_retries or self.max_retries

        logger.info(f"Pesquisando licenciamento para: {software.nome} {software.versao or ''}")

        for attempt in range(1, max_retries + 1):
            try:
                # Prepara o prompt
                prompt_messages = self.prompt.invoke(
                    {
                        "nome": software.nome,
                        "versao": software.versao or "N/A",
                        "agent_scratchpad": [],
                    }
                ).to_messages()

                # Executa o agente
                logger.debug(f"Executando agente (tentativa {attempt}/{max_retries})...")
                response = self.agent.invoke({"messages": prompt_messages})

                # Extrai a resposta do último AIMessage
                output = self._extract_output_content(response)

                # Tenta parsear JSON da resposta
                result = self._parse_response(output, software)

                logger.info(
                    f"Pesquisa concluída: {software.nome} - "
                    f"Status: {result.status_verificado}, "
                    f"Confiança: {result.nivel_confianca}%"
                )

                return result

            except json.JSONDecodeError as e:
                logger.warning(f"Erro ao parsear JSON (tentativa {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    # Retorna resultado com erro
                    return self._create_error_result(software, f"Erro ao parsear resposta: {e}")

            except Exception as e:
                logger.warning(f"Erro na pesquisa (tentativa {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    return self._create_error_result(software, f"Erro na pesquisa: {e}")

        # Se chegou aqui, todas as tentativas falharam
        return self._create_error_result(software, "Falha após todas as tentativas")

    def _extract_output_content(self, agent_response: dict[str, Any]) -> str:
        """
        Obtém o conteúdo textual da última mensagem do agente.

        Args:
            agent_response: Estado retornado pelo agente

        Returns:
            Texto extraído da resposta
        """
        messages = agent_response.get("messages", [])
        if messages:
            last_message = messages[-1]
            content = getattr(last_message, "content", "")

            if isinstance(content, str):
                return content

            if isinstance(content, list):
                text_parts = []
                for fragment in content:
                    if isinstance(fragment, dict):
                        text_parts.append(fragment.get("text", ""))
                    else:
                        text_parts.append(str(fragment))
                return " ".join(part for part in text_parts if part).strip()

            return str(content)

        return str(agent_response.get("output", ""))

    def _parse_response(self, output: str, software: Software) -> SoftwareResult:
        """
        Parseia a resposta do agente e cria um SoftwareResult.

        Args:
            output: Resposta do agente
            software: Software original

        Returns:
            SoftwareResult parseado
        """
        # Tenta extrair JSON da resposta
        json_str = self._extract_json_from_text(output)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Se não conseguir parsear, tenta extrair informações manualmente
            logger.warning("Não foi possível parsear JSON, tentando extração manual...")
            return self._extract_manual_result(output, software)

        # Valida e cria o resultado
        status = str(data.get("status_licenciamento", "Não")).strip()
        if status.lower() not in ["sim", "não", "nao", "yes", "no"]:
            status = "Não"  # Default seguro

        # Normaliza para "Sim" ou "Não"
        if status.lower() in ["sim", "yes", "s"]:
            status = "Sim"
        else:
            status = "Não"

        confianca = int(data.get("nivel_confianca", 50))
        confianca = max(0, min(100, confianca))  # Garante entre 0-100

        fontes = data.get("fontes", [])
        if isinstance(fontes, str):
            fontes = [f.strip() for f in fontes.split(";") if f.strip()]

        links = data.get("links", [])
        if isinstance(links, str):
            links = [l.strip() for l in links.split(";") if l.strip()]

        resumo = data.get("resumo", output[:500])  # Limita resumo

        return SoftwareResult.from_software(
            software,
            status_verificado=status,
            nivel_confianca=confianca,
            fontes_utilizadas=fontes,
            links_fontes=links,
            resumo_pesquisa=resumo,
        )

    def _extract_json_from_text(self, text: str) -> str:
        """
        Extrai JSON de um texto que pode conter outros caracteres.

        Args:
            text: Texto que pode conter JSON

        Returns:
            String JSON extraída
        """
        # Tenta encontrar JSON entre chaves
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]

        # Se não encontrar, retorna o texto original
        return text

    def _extract_manual_result(self, output: str, software: Software) -> SoftwareResult:
        """
        Extrai resultado manualmente quando JSON não pode ser parseado.

        Args:
            output: Resposta do agente
            software: Software original

        Returns:
            SoftwareResult com informações extraídas manualmente
        """
        # Tenta identificar status
        output_lower = output.lower()
        if "sim" in output_lower or "yes" in output_lower or "requer" in output_lower:
            status = "Sim"
        else:
            status = "Não"

        # Confiança baixa para resultados manuais
        confianca = 40

        # Tenta extrair links
        import re

        url_pattern = r"https?://[^\s]+"
        links = re.findall(url_pattern, output)

        return SoftwareResult.from_software(
            software,
            status_verificado=status,
            nivel_confianca=confianca,
            fontes_utilizadas=["Resposta do agente"],
            links_fontes=links[:5],  # Limita a 5 links
            resumo_pesquisa=output[:500],
        )

    def _create_error_result(self, software: Software, error_msg: str) -> SoftwareResult:
        """
        Cria um resultado de erro.

        Args:
            software: Software original
            error_msg: Mensagem de erro

        Returns:
            SoftwareResult com status de erro
        """
        logger.error(f"Erro ao pesquisar {software.nome}: {error_msg}")

        return SoftwareResult.from_software(
            software,
            status_verificado="Erro",
            nivel_confianca=0,
            fontes_utilizadas=[],
            links_fontes=[],
            resumo_pesquisa=f"Erro na pesquisa: {error_msg}",
        )

