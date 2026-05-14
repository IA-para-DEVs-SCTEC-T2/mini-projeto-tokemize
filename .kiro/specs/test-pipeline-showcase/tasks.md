# Implementation Plan: Test Pipeline Showcase

## Overview

Implementar a pipeline de CI/CD para execução automática de testes pytest, coleta de métricas de teste, integração com o config.json existente e visualização na showcase. A implementação segue as fases do design: CI workflow → metrics collector script → metrics updater integration → showcase frontend.

## Tasks

- [-] 1. Configurar dependências e pyproject.toml para suporte a relatórios de teste
  - Adicionar `pytest-json-report` às dependências de desenvolvimento em `pyproject.toml` ou `requirements.txt`
  - Adicionar `pytest-cov` às dependências de desenvolvimento (se ainda não presente)
  - Configurar seção `[tool.coverage.json]` em `pyproject.toml` com `output = "coverage.json"`
  - Configurar seção `[tool.coverage.report]` com `precision = 2`
  - _Requirements: 1.3, 1.7, 1.8, 3.1, 3.2, 3.3_

- [ ] 2. Criar o script de coleta de métricas de teste
  - [-] 2.1 Criar arquivo `.github/scripts/collect_test_metrics.py` com a função `collect_test_metrics(pytest_json_path, coverage_json_path, pytest_exit_code)`
    - Implementar extração de `totalTests`, `passed`, `failed`, `skipped` do pytest JSON report (`summary` field)
    - Implementar extração de `duration` com arredondamento para 2 casas decimais
    - Implementar extração de `coverage` do coverage JSON report (`totals.percent_covered`)
    - Implementar lógica de status: `"failing"` se `failed > 0`, `"passing"` se `failed == 0 AND totalTests > 0`, `"unknown"` caso contrário ou se `exit_code > 1`
    - Implementar geração de `lastRunAt` em formato ISO 8601 UTC com precisão de segundos
    - Gravar resultado em `/tmp/test-metrics.json`
    - Usar type hints em todas as funções e docstrings no padrão Google Style
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 5.1–5.11_

  - [ ]* 2.2 Escrever property test para extração de métricas (Property 1: Metrics Extraction Correctness)
    - Criar `tests/test_metrics_collector_properties.py`
    - Implementar generator `pytest_report` com Hypothesis para relatórios válidos
    - Implementar generator `coverage_report` com Hypothesis
    - **Property 1: Metrics Extraction Correctness**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6**

  - [ ]* 2.3 Escrever property test para validação de campos (Property 2: Test Metrics Validation)
    - Implementar generator `test_metrics` com Hypothesis
    - Verificar que todos os campos satisfazem suas constraints após `validate_metrics()`
    - **Property 2: Test Metrics Validation**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.8**

  - [ ]* 2.4 Escrever property test para cálculo de status (Property 3: Status Calculation Correctness)
    - Verificar a lógica de status para todas as combinações de `failed`, `totalTests` e `exit_code`
    - **Property 3: Status Calculation Correctness**
    - **Validates: Requirements 5.9, 5.10, 5.11**

  - [ ]* 2.5 Escrever property test para precisão de duração (Property 7: Duration Precision)
    - Verificar que qualquer float de duração é arredondado para exatamente 2 casas decimais
    - **Property 7: Duration Precision**
    - **Validates: Requirements 2.5**

  - [ ]* 2.6 Escrever property test para formato de timestamp (Property 5: Timestamp ISO 8601 UTC Format)
    - Verificar que `lastRunAt` sempre segue o formato `"YYYY-MM-DDTHH:MM:SSZ"`
    - **Property 5: Timestamp ISO 8601 UTC Format**
    - **Validates: Requirements 4.4, 5.7**

  - [ ]* 2.7 Escrever property test para serialização JSON round-trip (Property 6: JSON Serialization Round-Trip)
    - Verificar que serializar e desserializar um objeto de métricas preserva todos os campos e tipos
    - **Property 6: Test Metrics JSON Serialization Round-Trip**
    - **Validates: Requirements 2.7, 8.2**

- [~] 3. Checkpoint — Garantir que todos os testes do script de métricas passam
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [ ] 4. Criar o workflow de CI (ci-tests.yml)
  - [~] 4.1 Criar `.github/workflows/ci-tests.yml` com triggers `pull_request` (opened, synchronize, reopened) e `push` para `main` e `develop`
    - Configurar `concurrency` com grupo `ci-tests-${{ github.ref }}` e `cancel-in-progress: true`
    - Configurar job `test` com `runs-on: ubuntu-latest` e `timeout-minutes: 10`
    - Adicionar steps: checkout, setup Python 3.11, install dependencies, run pytest, collect metrics, upload artifacts
    - Configurar pytest com flags: `--json-report --json-report-file=pytest-report.json --cov=src/tokemize --cov-report=json --cov-report=term -v --tb=short`
    - Adicionar step de upload de artifacts: `pytest-report.json`, `coverage.json`, `test-metrics.json`
    - Adicionar step condicional para disparar `update-board-metrics.yml` apenas em push para `main`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 3.1, 3.2, 3.3, 3.4, 3.5, 7.1–7.8, 8.1, 8.2, 8.3, 9.5, 10.1, 10.2, 10.4, 10.5_

- [ ] 5. Integrar métricas de teste ao Metrics Updater
  - [~] 5.1 Modificar `.github/workflows/update-board-metrics.yml` para adicionar step de leitura de `test-metrics.json`
    - Adicionar step `Read test metrics (if available)` que verifica existência de `/tmp/test-metrics.json` e copia para `/tmp/test_metrics_data.json`
    - _Requirements: 4.1, 4.2, 4.3, 8.4, 8.5, 10.3_

  - [~] 5.2 Modificar o script Python do `update-board-metrics.yml` para fazer merge de `testMetrics` no `config.json`
    - Implementar função `update_test_metrics(config, new_metrics)` com fallback para valores anteriores
    - Implementar inicialização com valores padrão se `testMetrics` não existir no config
    - Preservar todas as seções existentes (`repoStats`, `boardMetrics`, `contributors`, `prAuthors`)
    - Adicionar timestamp ISO 8601 UTC ao fazer update
    - Implementar backup `config.json.backup.{timestamp}` antes de atualizar em caso de JSON corrompido
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 9.3, 9.4_

  - [ ]* 5.3 Escrever property test para merge de config (Property 4: Config Merge Preserves Existing Data)
    - Verificar que o merge preserva todas as seções existentes e apenas adiciona/atualiza `testMetrics`
    - **Property 4: Config Merge Preserves Existing Data**
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [ ]* 5.4 Escrever property test para invariante de soma (Property 8: Metrics Sum Invariant)
    - Verificar que `passed + failed + skipped <= totalTests` para qualquer objeto de métricas válido
    - **Property 8: Metrics Sum Invariant**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [~] 6. Checkpoint — Garantir que todos os testes de integração do metrics updater passam
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [ ] 7. Implementar a seção "Qualidade de Código" na showcase
  - [~] 7.1 Atualizar `docs/showcase/` (HTML/JS) para adicionar seção "Qualidade de Código" após a seção de métricas do repositório
    - Ler `config.testMetrics.totalTests` e exibir em card com label "Total de Testes"
    - Calcular e exibir taxa de sucesso como `(passed / totalTests * 100)` com 1 casa decimal e símbolo `%`
    - Exibir `coverage` (se não null) em card com label "Cobertura de Código" com 1 casa decimal e `%`
    - Exibir indicador visual verde (`#22c55e`) com ícone de check quando `status === "passing"`
    - Exibir indicador visual vermelho (`#ef4444`) com ícone de X quando `status === "failing"`
    - Converter `lastRunAt` para formato `"DD/MM/YYYY HH:MM"` no timezone local do navegador
    - Exibir mensagem `"Métricas de teste não disponíveis"` se `config.testMetrics` não existir ou estiver vazio
    - Usar a mesma paleta de cores e tipografia das seções existentes
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

- [ ] 8. Criar fixtures e utilitários de teste
  - [x] 8.1 Criar `tests/fixtures/pytest-report-sample.json` com exemplo de relatório pytest válido
    - Criar `tests/fixtures/coverage-sample.json` com exemplo de relatório de cobertura válido
    - Criar `tests/fixtures/config-sample.json` com exemplo de `config.json` contendo seções existentes
    - _Requirements: 2.1–2.7, 4.1–4.5_

  - [ ] 8.2 Criar `tests/utils/metrics_helpers.py` com funções auxiliares para geração de dados de teste
    - Criar `tests/utils/json_helpers.py` com funções auxiliares para manipulação de JSON nos testes
    - _Requirements: 2.1–2.9_

- [~] 9. Checkpoint final — Garantir que todos os testes passam
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

## Notes

- Tasks marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada task referencia requisitos específicos para rastreabilidade
- Os property tests usam Hypothesis (já presente nas dependências do projeto)
- O script `.github/scripts/collect_test_metrics.py` deve seguir as convenções do projeto: type hints, docstrings Google Style, snake_case
- O workflow `ci-tests.yml` deve usar `GITHUB_TOKEN` ou `PROJECT_TOKEN` conforme os workflows existentes
- Artifacts têm retenção padrão de 7 dias no GitHub Actions

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "8.1"] },
    { "id": 1, "tasks": ["2.1", "8.2"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "4.1"] },
    { "id": 3, "tasks": ["5.1"] },
    { "id": 4, "tasks": ["5.2"] },
    { "id": 5, "tasks": ["5.3", "5.4", "7.1"] }
  ]
}
```
