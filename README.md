# Web Search Agent - Verificação de Licenciamento de Softwares

Sistema automatizado para verificação de licenciamento de softwares corporativos através de pesquisa web assistida por IA. O sistema integra com SharePoint para leitura de dados e utiliza LangChain com DuckDuckGo Search para pesquisar informações atualizadas sobre licenciamento.

## Características

- ✅ Integração automática com SharePoint para leitura de planilhas Excel
- ✅ Pesquisa web automatizada usando DuckDuckGo Search
- ✅ Análise inteligente com modelos de linguagem (LLM) via gateway corporativo
- ✅ Geração de relatório Excel detalhado com fontes, links e níveis de confiança
- ✅ Formatação condicional baseada em confiança e status
- ✅ Tratamento robusto de erros com retry automático
- ✅ Logging completo para auditoria

## Estrutura do Projeto

```
websearch-agent/
├── src/
│   ├── sharepoint/          # Integração com SharePoint
│   ├── excel/              # Leitura e escrita de Excel
│   ├── agent/              # Agente de pesquisa com LangChain
│   ├── models/             # Modelos de dados Pydantic
│   └── config/             # Configurações e variáveis de ambiente
├── logs/                   # Arquivos de log
├── output/                 # Arquivos Excel de saída
├── main.py                 # Ponto de entrada principal
├── .env.example            # Template de variáveis de ambiente
└── pyproject.toml          # Dependências do projeto
```

## Requisitos

- Python >= 3.13
- Acesso ao SharePoint corporativo
- Gateway LLM corporativo (compatível com OpenAI API)
- Credenciais de acesso ao SharePoint

## Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd websearch-agent
```

2. Instale as dependências usando `uv` (recomendado) ou `pip`:
```bash
# Com uv
uv sync

# Ou com pip
pip install -e .
```

3. Configure as variáveis de ambiente:
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas credenciais
```

## Configuração

Edite o arquivo `.env` com suas configurações:

### SharePoint
- `SHAREPOINT_URL`: URL base do SharePoint (ex: `https://seu-tenant.sharepoint.com`)
- `SHAREPOINT_SITE`: Caminho do site (ex: `/sites/NomeDoSite`)
- `SHAREPOINT_LIBRARY`: Nome da biblioteca de documentos (use `%20` para espaços)
- `SHAREPOINT_FILE`: Nome do arquivo Excel no SharePoint
- `SHAREPOINT_USERNAME`: Seu usuário do SharePoint
- `SHAREPOINT_PASSWORD`: Sua senha do SharePoint

### Gateway LLM
- `LLM_BASE_URL`: URL base do gateway LLM corporativo
- `LLM_API_KEY`: Token de API do gateway
- `LLM_MODEL`: Modelo a ser usado (ex: `gpt-4o-mini`)

### Arquivos
- `OUTPUT_FILE`: Nome do arquivo de saída (padrão: `resultados_licenciamento.xlsx`)
- `OUTPUT_DIR`: Diretório de saída (padrão: `./output`)

### Configurações Gerais
- `MAX_RETRIES`: Número máximo de tentativas em caso de erro (padrão: `3`)
- `REQUEST_TIMEOUT`: Timeout de requisições em segundos (padrão: `30`)
- `CONFIDENCE_THRESHOLD`: Limiar mínimo de confiança 0-100 (padrão: `70`)

## Formato do Arquivo Excel de Entrada

O arquivo Excel no SharePoint deve ter a seguinte estrutura:

| Coluna A | Coluna B | Coluna C |
|----------|----------|----------|
| Nome do Software | Versão | Status Original |
| Microsoft Office | 2021 | Sim |
| Python | 3.11 | Não |

**Nota**: A primeira linha pode ser cabeçalho ou dados. O sistema detecta automaticamente.

## Uso

Execute o script principal:

```bash
python main.py
```

O sistema irá:
1. Autenticar no SharePoint
2. Baixar o arquivo Excel
3. Ler a lista de softwares
4. Pesquisar informações de licenciamento para cada software
5. Gerar arquivo Excel de saída com resultados detalhados

## Formato do Arquivo de Saída

O arquivo Excel gerado contém as seguintes colunas:

| Coluna | Descrição |
|--------|-----------|
| Nome | Nome do software |
| Versão | Versão do software |
| Status Original | Status original da planilha |
| Status Verificado | Status verificado pela pesquisa (Sim/Não) |
| Data Pesquisa | Data e hora da pesquisa |
| Fontes | Fontes utilizadas (separadas por ponto-e-vírgula) |
| Links | Links das fontes (separados por ponto-e-vírgula) |
| Confiança | Nível de confiança (0-100) |
| Resumo | Resumo da pesquisa |

### Formatação Condicional

- **Confiança >= 80%**: Fundo verde claro
- **Confiança 50-79%**: Fundo amarelo claro
- **Confiança < 50%**: Fundo vermelho claro
- **Status "Sim"**: Fundo vermelho, texto em negrito
- **Status "Não"**: Fundo verde, texto em negrito
- **Status "Erro"**: Fundo vermelho, texto em negrito

## Logs

Os logs são salvos em `logs/websearch_agent_YYYYMMDD.log` e também exibidos no console.

Níveis de log:
- **INFO**: Progresso geral e estatísticas
- **DEBUG**: Detalhes de requisições e respostas
- **WARNING**: Avisos e erros recuperáveis
- **ERROR**: Falhas críticas

## Tratamento de Erros

O sistema possui tratamento robusto de erros:

- **Autenticação SharePoint**: Retry com backoff exponencial
- **Download de arquivo**: Múltiplas tentativas
- **Pesquisa web**: Timeout e fallback para próximo item
- **LLM**: Retry com diferentes estratégias
- **Escrita Excel**: Backup antes de sobrescrever

## Dependências Principais

- `langchain`: Framework para construção de agentes de IA
- `langchain-community`: Ferramentas comunitárias (DuckDuckGo Search)
- `langchain-openai`: Integração com APIs compatíveis OpenAI
- `office365-rest-python-client`: Cliente para SharePoint
- `openpyxl`: Manipulação de arquivos Excel
- `pandas`: Processamento de dados
- `pydantic`: Validação de dados
- `pydantic-settings`: Gerenciamento de configurações
- `python-dotenv`: Carregamento de variáveis de ambiente
- `duckduckgo-search`: Ferramenta de busca web

## Desenvolvimento

### Estrutura de Módulos

- `src/config/settings.py`: Configurações centralizadas
- `src/models/software.py`: Modelos de dados
- `src/sharepoint/client.py`: Cliente SharePoint
- `src/excel/reader.py`: Leitor de Excel
- `src/excel/writer.py`: Escritor de Excel
- `src/agent/prompts.py`: Templates de prompts
- `src/agent/search_agent.py`: Agente de pesquisa
- `main.py`: Orquestração principal

## Melhorias Futuras

- [ ] Cache de pesquisas para evitar reprocessamento
- [ ] Paralelização de pesquisas (ThreadPoolExecutor)
- [ ] Interface web para visualização de resultados
- [ ] Dashboard com métricas de confiança
- [ ] Integração com banco de dados para histórico

## Licença

Este projeto é de uso interno corporativo.

## Suporte

Para questões ou problemas, entre em contato com a equipe de desenvolvimento.

