"""Script de teste rápido para verificar integração ponta a ponta do pipeline."""

from tokemize.orchestrator import run_pipeline

# Teste 1: Pipeline completo com sucesso
print("=" * 60)
print("Teste 1: Pipeline completo com diretório válido")
print("=" * 60)

result = run_pipeline(".", "add authentication to the API")

print(f"\nResultado:")
print(f"  success: {result.success}")
print(f"  prompt (primeiros 100 chars): {result.prompt[:100]}...")
print(f"  failed_stage: {result.failed_stage}")
print(f"  error_message: {result.error_message}")
print(f"  elapsed_seconds: {result.elapsed_seconds:.4f}s")
print(f"  stages_completed: {result.stages_completed}")

assert result.success is True, "Pipeline deveria ter sucesso"
assert result.prompt != "", "Prompt não deveria estar vazio"
assert result.failed_stage is None, "failed_stage deveria ser None"
assert result.error_message is None, "error_message deveria ser None"
assert len(result.stages_completed) == 7, "Deveria ter 7 etapas concluídas"
assert result.elapsed_seconds > 0, "elapsed_seconds deveria ser positivo"

print("\n✅ Teste 1 passou!")

# Teste 2: Pipeline com diretório inválido (deve falhar no scanner)
print("\n" + "=" * 60)
print("Teste 2: Pipeline com diretório inválido")
print("=" * 60)

result2 = run_pipeline("/caminho/inexistente/xyz", "qualquer tarefa")

print(f"\nResultado:")
print(f"  success: {result2.success}")
print(f"  failed_stage: {result2.failed_stage}")
print(f"  error_message: {result2.error_message}")
print(f"  stages_completed: {result2.stages_completed}")

assert result2.success is False, "Pipeline deveria ter falhado"
assert result2.failed_stage == "scanner", "Deveria ter falhado no scanner"
assert result2.error_message is not None, "Deveria ter mensagem de erro"
assert len(result2.stages_completed) == 0, "Nenhuma etapa deveria ter sido concluída"

print("\n✅ Teste 2 passou!")

print("\n" + "=" * 60)
print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 60)
print("\nO pipeline está funcionando corretamente ponta a ponta.")
print("Próximo passo: implementar os testes unitários e de propriedade.")
