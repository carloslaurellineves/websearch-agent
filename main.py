"""Ponto de entrada principal do sistema de verificação de licenciamento."""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.config.settings import settings
from src.sharepoint.client import SharePointClient
from src.excel.reader import ExcelReader
from src.excel.writer import ExcelWriter
from src.agent.search_agent import SearchAgent
from src.models.software import SoftwareResult

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
def setup_logging():
    """Configura o sistema de logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"websearch_agent_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    """Função principal que orquestra todo o processo."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("Iniciando processo de verificação de licenciamento de softwares")
    logger.info("=" * 80)

    start_time = time.time()
    stats = {
        "total": 0,
        "processados": 0,
        "erros": 0,
        "sim": 0,
        "nao": 0,
        "erro_status": 0,
    }

    try:
        # 1. Carregar configurações
        logger.info("Carregando configurações...")
        logger.info(f"SharePoint: {settings.sharepoint_url}{settings.sharepoint_site}")
        logger.info(f"LLM Gateway: {settings.llm_base_url} (Modelo: {settings.llm_model})")
        logger.info(f"Arquivo de saída: {settings.output_path}")

        # 2. Autenticar no SharePoint
        logger.info("\n" + "-" * 80)
        logger.info("Etapa 1: Autenticação no SharePoint")
        logger.info("-" * 80)

        sharepoint_client = SharePointClient()
        if not sharepoint_client.authenticate():
            logger.error("Falha na autenticação do SharePoint. Abortando.")
            return 1

        # 3. Baixar arquivo Excel
        logger.info("\n" + "-" * 80)
        logger.info("Etapa 2: Download do arquivo Excel do SharePoint")
        logger.info("-" * 80)

        excel_path = sharepoint_client.download_excel_file()
        if not excel_path:
            logger.error("Falha ao baixar arquivo Excel. Abortando.")
            return 1

        logger.info(f"Arquivo baixado: {excel_path}")

        # 4. Ler arquivo Excel
        logger.info("\n" + "-" * 80)
        logger.info("Etapa 3: Leitura do arquivo Excel")
        logger.info("-" * 80)

        excel_reader = ExcelReader(excel_path)
        softwares = excel_reader.read_softwares()
        stats["total"] = len(softwares)

        if not softwares:
            logger.warning("Nenhum software encontrado no arquivo Excel. Abortando.")
            return 1

        logger.info(f"Total de softwares encontrados: {stats['total']}")

        # 5. Inicializar agente de pesquisa
        logger.info("\n" + "-" * 80)
        logger.info("Etapa 4: Inicialização do agente de pesquisa")
        logger.info("-" * 80)

        search_agent = SearchAgent()
        logger.info("Agente de pesquisa inicializado com sucesso")

        # 6. Loop de pesquisa
        logger.info("\n" + "-" * 80)
        logger.info("Etapa 5: Pesquisa de licenciamento")
        logger.info("-" * 80)
        logger.info(f"Iniciando pesquisa para {stats['total']} softwares...\n")

        results: list[SoftwareResult] = []

        for idx, software in enumerate(softwares, 1):
            logger.info(f"[{idx}/{stats['total']}] Pesquisando: {software.nome} {software.versao or ''}")

            try:
                result = search_agent.search_software_licensing(software)
                results.append(result)
                stats["processados"] += 1

                # Atualiza estatísticas
                status = result.status_verificado.upper()
                if status == "SIM":
                    stats["sim"] += 1
                elif status in ["NÃO", "NAO"]:
                    stats["nao"] += 1
                else:
                    stats["erro_status"] += 1

                logger.info(
                    f"  ✓ Status: {result.status_verificado} | "
                    f"Confiança: {result.nivel_confianca}% | "
                    f"Fontes: {len(result.fontes_utilizadas)}"
                )

            except Exception as e:
                logger.error(f"  ✗ Erro ao pesquisar {software.nome}: {e}")
                stats["erros"] += 1

                # Cria resultado de erro
                error_result = SoftwareResult.from_software(
                    software,
                    status_verificado="Erro",
                    nivel_confianca=0,
                    fontes_utilizadas=[],
                    links_fontes=[],
                    resumo_pesquisa=f"Erro: {str(e)}",
                )
                results.append(error_result)
                stats["processados"] += 1
                stats["erro_status"] += 1

            # Pequena pausa entre requisições para evitar rate limiting
            if idx < stats["total"]:
                time.sleep(1)

        # 7. Gerar Excel de saída
        logger.info("\n" + "-" * 80)
        logger.info("Etapa 6: Geração do arquivo Excel de saída")
        logger.info("-" * 80)

        excel_writer = ExcelWriter(settings.output_path)
        if not excel_writer.write_results(results):
            logger.error("Falha ao gerar arquivo Excel de saída.")
            return 1

        # 8. Estatísticas finais
        elapsed_time = time.time() - start_time
        logger.info("\n" + "=" * 80)
        logger.info("Processo concluído com sucesso!")
        logger.info("=" * 80)
        logger.info(f"Tempo total: {elapsed_time:.2f} segundos ({elapsed_time/60:.2f} minutos)")
        logger.info(f"Total de softwares: {stats['total']}")
        logger.info(f"Processados com sucesso: {stats['processados']}")
        logger.info(f"Erros: {stats['erros']}")
        logger.info(f"Status 'Sim' (requer licenciamento): {stats['sim']}")
        logger.info(f"Status 'Não' (não requer licenciamento): {stats['nao']}")
        logger.info(f"Status 'Erro': {stats['erro_status']}")
        logger.info(f"\nArquivo de saída: {settings.output_path}")
        logger.info("=" * 80)

        return 0

    except KeyboardInterrupt:
        logger.warning("\nProcesso interrompido pelo usuário.")
        return 1

    except Exception as e:
        logger.error(f"\nErro crítico no processo: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
