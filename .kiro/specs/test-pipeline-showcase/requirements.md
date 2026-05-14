# Requirements Document

## Introduction

Este documento especifica os requisitos para a criação de uma pipeline de CI/CD que execute testes automaticamente e publique as métricas de teste na showcase do projeto. A solução integrará a execução de testes pytest com o sistema existente de coleta de métricas, garantindo que informações sobre qualidade do código sejam visíveis junto com outras métricas do repositório.

## Glossary

- **CI_Workflow**: Workflow do GitHub Actions responsável por executar testes em eventos de push e pull request
- **Test_Metrics_Collector**: Componente que coleta métricas dos testes executados (total, passados, falhados, tempo, cobertura)
- **Metrics_Updater**: Workflow existente que atualiza o config.json com métricas do repositório e board
- **Showcase**: Aplicação web estática que exibe métricas e informações do projeto via GitHub Pages
- **Config_JSON**: Arquivo de configuração (docs/showcase/config.json) que armazena todas as métricas exibidas na showcase
- **Coverage_Report**: Relatório de cobertura de código gerado pelo pytest-cov
- **Test_Suite**: Conjunto de testes pytest localizados no diretório tests/

## Requirements

### Requirement 1: Execução Automática de Testes

**User Story:** Como desenvolvedor, eu quero que os testes sejam executados automaticamente em PRs e pushes, para que problemas sejam detectados antes do merge.

#### Acceptance Criteria

1. WHEN um pull request é criado (opened, synchronize, reopened events), THE CI_Workflow SHALL executar todos os testes no diretório tests/ usando pytest
2. WHEN código é enviado (push event) para a branch develop ou main, THE CI_Workflow SHALL executar todos os testes no diretório tests/ usando pytest
3. THE CI_Workflow SHALL executar pytest com as configurações definidas em pyproject.toml ou pytest.ini se existir
4. WHEN pytest retorna exit code diferente de 0, THE CI_Workflow SHALL marcar o check como failed com status conclusion "failure"
5. WHEN pytest retorna exit code 0, THE CI_Workflow SHALL marcar o check como passed com status conclusion "success"
6. THE CI_Workflow SHALL configurar timeout de 10 minutos e falhar com status "timed_out" se exceder
7. THE CI_Workflow SHALL instalar Python 3.11 ou superior antes de executar os testes
8. THE CI_Workflow SHALL instalar todas as dependências listadas em requirements.txt ou pyproject.toml antes de executar os testes
9. WHEN o check status é "failure", THE GitHub branch protection SHALL bloquear o merge do pull request
10. WHEN o check status é "success", THE GitHub branch protection SHALL permitir o merge do pull request

### Requirement 2: Coleta de Métricas de Testes

**User Story:** Como gerente de projeto, eu quero visualizar métricas de testes na showcase, para que eu possa acompanhar a qualidade do código.

#### Acceptance Criteria

1. WHEN pytest completa a execução, THE Test_Metrics_Collector SHALL extrair o número total de testes do pytest JSON report
2. WHEN pytest completa a execução, THE Test_Metrics_Collector SHALL extrair o número de testes passados (status "passed") do pytest JSON report
3. WHEN pytest completa a execução, THE Test_Metrics_Collector SHALL extrair o número de testes falhados (status "failed" ou "error") do pytest JSON report
4. WHEN pytest completa a execução, THE Test_Metrics_Collector SHALL extrair o número de testes pulados (status "skipped") do pytest JSON report
5. WHEN pytest completa a execução, THE Test_Metrics_Collector SHALL calcular o tempo total de execução em segundos com precisão de 2 casas decimais
6. WHERE pytest-cov está instalado e configurado, THE Test_Metrics_Collector SHALL extrair a porcentagem de cobertura total do coverage JSON report
7. THE Test_Metrics_Collector SHALL gerar um arquivo test-metrics.json em /tmp/ contendo todos os campos coletados
8. IF pytest falha ao executar (exit code != 0 e != 1), THEN THE Test_Metrics_Collector SHALL registrar erro no log e definir status como "unknown"
9. THE Test_Metrics_Collector SHALL executar imediatamente após pytest completar, antes de qualquer outro step do workflow

### Requirement 3: Geração de Relatório de Cobertura

**User Story:** Como desenvolvedor, eu quero visualizar a cobertura de código dos testes, para que eu possa identificar áreas não testadas.

#### Acceptance Criteria

1. THE CI_Workflow SHALL executar pytest com a flag --cov para gerar Coverage_Report
2. THE CI_Workflow SHALL configurar pytest-cov para cobrir apenas o diretório src/tokemize
3. THE CI_Workflow SHALL gerar Coverage_Report em formato JSON para parsing automatizado
4. THE CI_Workflow SHALL gerar Coverage_Report em formato terminal para visualização nos logs
5. IF pytest-cov não estiver instalado, THEN THE CI_Workflow SHALL executar os testes sem cobertura e registrar aviso nos logs

### Requirement 4: Integração com Sistema de Métricas Existente

**User Story:** Como desenvolvedor, eu quero que as métricas de teste sejam integradas ao config.json existente, para que apareçam na showcase junto com outras métricas.

#### Acceptance Criteria

1. THE Metrics_Updater SHALL adicionar uma nova seção "testMetrics" ao Config_JSON
2. THE Metrics_Updater SHALL preservar todas as seções existentes do Config_JSON (repoStats, boardMetrics, contributors, prAuthors)
3. WHEN métricas de teste são coletadas, THE Metrics_Updater SHALL atualizar a seção testMetrics com os dados mais recentes
4. THE Metrics_Updater SHALL incluir timestamp ISO 8601 com timezone UTC indicando quando as métricas foram coletadas
5. IF a coleta de métricas de teste falhar, THEN THE Metrics_Updater SHALL manter os valores anteriores e registrar erro nos logs

### Requirement 5: Estrutura de Dados de Métricas de Teste

**User Story:** Como desenvolvedor frontend, eu quero uma estrutura de dados consistente para métricas de teste, para que eu possa exibi-las na showcase.

#### Acceptance Criteria

1. THE testMetrics section SHALL conter o campo "totalTests" com valor inteiro não-negativo no intervalo [0, 999999]
2. THE testMetrics section SHALL conter o campo "passed" com valor inteiro não-negativo no intervalo [0, totalTests]
3. THE testMetrics section SHALL conter o campo "failed" com valor inteiro não-negativo no intervalo [0, totalTests]
4. THE testMetrics section SHALL conter o campo "skipped" com valor inteiro não-negativo no intervalo [0, totalTests]
5. THE testMetrics section SHALL conter o campo "duration" com valor float não-negativo no intervalo [0.0, 86400.0] representando segundos
6. WHERE cobertura está disponível, THE testMetrics section SHALL conter o campo "coverage" com valor float no intervalo [0.0, 100.0] representando porcentagem
7. THE testMetrics section SHALL conter o campo "lastRunAt" com timestamp em formato ISO 8601 com timezone UTC e precisão de segundos (exemplo: "2026-05-13T14:30:00Z")
8. THE testMetrics section SHALL conter o campo "status" com um dos valores: "passing", "failing" ou "unknown"
9. WHEN failed > 0, THE status field SHALL ser definido como "failing"
10. WHEN failed == 0 AND totalTests > 0, THE status field SHALL ser definido como "passing"
11. WHEN totalTests == 0 OR lastRunAt is null, THE status field SHALL ser definido como "unknown"

### Requirement 6: Visualização na Showcase

**User Story:** Como visitante da showcase, eu quero visualizar métricas de teste de forma clara e visual, para que eu possa avaliar a qualidade do projeto.

#### Acceptance Criteria

1. THE Showcase SHALL exibir uma nova seção "Qualidade de Código" posicionada após a seção de métricas do repositório
2. THE Showcase SHALL exibir o número total de testes em um card visual com label "Total de Testes" lendo o valor de config.testMetrics.totalTests
3. THE Showcase SHALL calcular e exibir a taxa de sucesso como (passed / totalTests * 100) com precisão de 1 casa decimal seguida do símbolo "%"
4. WHERE config.testMetrics.coverage existe e não é null, THE Showcase SHALL exibir a porcentagem de cobertura em um card visual com label "Cobertura de Código" formatada com 1 casa decimal seguida de "%"
5. WHEN config.testMetrics.status é "passing", THE Showcase SHALL exibir indicador visual verde (cor #22c55e) com ícone de check
6. WHEN config.testMetrics.status é "failing", THE Showcase SHALL exibir indicador visual vermelho (cor #ef4444) com ícone de X
7. THE Showcase SHALL exibir o timestamp config.testMetrics.lastRunAt convertido para formato legível "DD/MM/YYYY HH:MM" no timezone local do navegador
8. IF config.testMetrics não existe ou está vazio, THEN THE Showcase SHALL exibir mensagem "Métricas de teste não disponíveis" na seção
9. THE Showcase SHALL usar a mesma paleta de cores e tipografia das seções existentes (repoStats, boardMetrics)

### Requirement 7: Workflow de CI para Testes

**User Story:** Como desenvolvedor, eu quero um workflow de CI dedicado para testes, para que a execução seja rápida e focada.

#### Acceptance Criteria

1. THE CI_Workflow SHALL ser nomeado "ci-tests.yml" e localizado em .github/workflows/
2. THE CI_Workflow SHALL ser disparado em eventos pull_request para todas as branches
3. THE CI_Workflow SHALL ser disparado em eventos push para branches develop e main
4. THE CI_Workflow SHALL usar ubuntu-latest como runner
5. THE CI_Workflow SHALL instalar Python 3.11 ou superior
6. THE CI_Workflow SHALL instalar dependências do projeto incluindo dev dependencies
7. THE CI_Workflow SHALL executar pytest com flags apropriadas para CI (-v, --tb=short, --cov)
8. THE CI_Workflow SHALL fazer upload dos resultados de teste como artifacts do workflow

### Requirement 8: Integração do CI com Metrics Updater

**User Story:** Como desenvolvedor, eu quero que as métricas de teste sejam automaticamente enviadas ao metrics updater, para que o config.json seja atualizado sem intervenção manual.

#### Acceptance Criteria

1. WHEN o CI_Workflow completa com sucesso na branch main, THE CI_Workflow SHALL disparar o Metrics_Updater workflow
2. THE CI_Workflow SHALL gerar um arquivo JSON com métricas de teste em formato padronizado
3. THE CI_Workflow SHALL fazer commit do arquivo de métricas em um diretório temporário
4. THE Metrics_Updater SHALL ler o arquivo de métricas de teste e integrar ao Config_JSON
5. THE Metrics_Updater SHALL fazer commit do Config_JSON atualizado com mensagem descritiva

### Requirement 9: Tratamento de Erros e Fallbacks

**User Story:** Como desenvolvedor, eu quero que o sistema seja resiliente a falhas, para que uma falha em testes não quebre a pipeline de métricas.

#### Acceptance Criteria

1. IF o Test_Suite falha, THEN THE CI_Workflow SHALL registrar o status "failing" nas métricas
2. IF pytest-cov não está disponível, THEN THE Test_Metrics_Collector SHALL omitir o campo coverage
3. IF a coleta de métricas falha, THEN THE Metrics_Updater SHALL manter valores anteriores e registrar warning
4. IF o Config_JSON está corrompido, THEN THE Metrics_Updater SHALL criar backup antes de atualizar
5. THE CI_Workflow SHALL sempre completar com exit code apropriado independente de falhas em coleta de métricas

### Requirement 10: Compatibilidade com Workflows Existentes

**User Story:** Como desenvolvedor, eu quero que o novo workflow seja compatível com workflows existentes, para que não haja conflitos ou duplicação de trabalho.

#### Acceptance Criteria

1. THE CI_Workflow SHALL usar concurrency groups para evitar execuções paralelas conflitantes
2. THE CI_Workflow SHALL respeitar as configurações de branch protection existentes
3. THE Metrics_Updater SHALL manter a estrutura existente do Config_JSON sem quebrar compatibilidade
4. THE CI_Workflow SHALL usar as mesmas convenções de commit do projeto (Conventional Commits)
5. THE CI_Workflow SHALL usar o mesmo token de autenticação (GITHUB_TOKEN ou PROJECT_TOKEN) dos workflows existentes
