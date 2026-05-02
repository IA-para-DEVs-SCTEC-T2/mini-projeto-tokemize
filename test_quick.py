#!/usr/bin/env python3
"""Teste rápido do pipeline - rode com: python test_quick.py"""

import sys
sys.path.insert(0, ".")

from tokemize.orchestrator import run_pipeline

print("Testando pipeline com diretório atual...")
result = run_pipeline(".", "add authentication")

print(f"\n✅ Success: {result.success}")
print(f"📝 Prompt length: {len(result.prompt)} chars")
print(f"⏱️  Time: {result.elapsed_seconds:.4f}s")
print(f"📊 Stages: {len(result.stages_completed)}/7")
print(f"🎯 Stages completed: {', '.join(result.stages_completed)}")

if result.success:
    print("\n✅ PIPELINE FUNCIONANDO!")
else:
    print(f"\n❌ Failed at: {result.failed_stage}")
    print(f"❌ Error: {result.error_message}")
