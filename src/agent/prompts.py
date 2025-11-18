"""Prompts para o agente de pesquisa de licenciamento."""

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


def get_search_prompt_template() -> ChatPromptTemplate:
    """
    Retorna o template de prompt para pesquisa de licenciamento.

    Returns:
        Template de prompt do LangChain
    """
    system_message = """Você é um assistente especializado em verificar o status de licenciamento de softwares corporativos.

Sua tarefa é pesquisar na web informações atualizadas sobre se um software específico requer licenciamento para uso corporativo/comercial.

INSTRUÇÕES:
1. Pesquise informações atualizadas e confiáveis sobre o software e sua versão
2. Verifique se o software requer licenciamento para uso corporativo/comercial
3. Identifique fontes oficiais (site do desenvolvedor, documentação oficial, termos de licença)
4. Analise se há versões gratuitas vs. pagas, licenças open-source vs. proprietárias
5. Considere o contexto de uso em uma instituição financeira (banco) com cerca de 8 mil funcionários

FORMATO DE RESPOSTA (JSON):
{{
    "status_licenciamento": "Sim" ou "Não",
    "nivel_confianca": número de 0 a 100,
    "fontes": ["fonte1", "fonte2", ...],
    "links": ["https://link1.com", "https://link2.com", ...],
    "resumo": "Breve resumo da pesquisa e conclusão"
}}

CRITÉRIOS:
- "Sim" se o software REQUER licenciamento para uso corporativo
- "Não" se o software é gratuito, open-source sem restrições, ou não requer licenciamento
- Nível de confiança baseado na qualidade e quantidade de fontes encontradas
- Priorize fontes oficiais e documentação do desenvolvedor
"""

    human_template = """Pesquise informações sobre o seguinte software:

Nome: {nome}
Versão: {versao}

Determine se este software requer licenciamento para uso corporativo em uma instituição financeira.
Retorne a resposta no formato JSON especificado."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            ("human", human_template),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    return prompt


def create_search_query(nome: str, versao: str | None = None) -> str:
    """
    Cria uma query de pesquisa otimizada para DuckDuckGo.

    Args:
        nome: Nome do software
        versao: Versão do software (opcional)

    Returns:
        Query de pesquisa formatada
    """
    if versao:
        return f"{nome} {versao} licenciamento corporativo comercial"
    return f"{nome} licenciamento corporativo comercial"


def format_software_info(nome: str, versao: str | None = None) -> str:
    """
    Formata informações do software para o prompt.

    Args:
        nome: Nome do software
        versao: Versão do software (opcional)

    Returns:
        String formatada com informações do software
    """
    if versao:
        return f"Software: {nome} (Versão: {versao})"
    return f"Software: {nome}"

