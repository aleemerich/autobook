#!/usr/bin/env python3
"""
test_llm.py — Connection test script for configured LLM in autobook.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR.parent / ".env")

try:
    from llm import call_llm
except ImportError as e:
    print(f"ERROR: Failed to import llm.py: {e}", file=sys.stderr)
    sys.exit(1)


def main():
    print("=" * 60)
    print("           AUTOBOOK: LLM CONNECTIVITY TEST")
    print("=" * 60)

    # 1. Print Configured State
    provider = os.environ.get("AUTOBOOK_PROVIDER", "anthropic").lower()
    prefix = provider.upper()
    
    writer_model = os.environ.get(f"{prefix}_WRITER_MODEL", "")
    if not writer_model:
        writer_model = os.environ.get("AUTOBOOK_WRITER_MODEL", "(default)")
        
    judge_model = os.environ.get(f"{prefix}_JUDGE_MODEL", "")
    if not judge_model:
        judge_model = os.environ.get("AUTOBOOK_JUDGE_MODEL", "(default)")
    
    print(f"  [Config] Provider:     {provider.upper()}")
    print(f"  [Config] Writer Model: {writer_model}")
    print(f"  [Config] Judge Model:  {judge_model}")
    print("-" * 60)

    # 2. Test Connection
    system_prompt = "You are a helpful and extremely concise assistant. Respond in Portuguese."
    prompt = "Diga 'Olá Mundo! Eu sou o autobook rodando no [provedor]' trocando [provedor] pelo nome do seu provedor."

    print("  [Action] Sending test prompt to WRITER model...")
    
    try:
        response = call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            is_judge=False
        )
        print("-" * 60)
        print("  [Response] Success! Reply from LLM:")
        print(f"\n{response.strip()}\n")
        print("=" * 60)
        print("  CONEXÃO VALIDADA COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print("-" * 60)
        print(f"  [ERROR] Connection failed: {e}", file=sys.stderr)
        print("  Por favor, verifique se a chave de API correta está configurada no seu .env.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
