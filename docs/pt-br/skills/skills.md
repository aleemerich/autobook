# Skills

A pasta `skills/` contem extensoes Python que podem registrar agentes ou
capacidades auxiliares.

## Arquivos Atuais

| Arquivo | Status | Papel |
| --- | --- | --- |
| `skills/create_agent.py` | Funcional como exemplo/extensao | Define `CustomLocalizerAgent` e registra via `register(factory)`. |
| `skills/redundancy_detector.py` | Funcional como utilitario | Define `RedundancyDetector` para detectar repeticoes de termos. |

## Integracao Com `AgentFactory`

`agents.py` possui `AgentFactory.load_skill_agent(skill_name, **kwargs)`.
O metodo procura `skills/{skill_name}.py`, importa dinamicamente o modulo e
espera que ele exponha uma funcao `register(factory)`.

Contrato minimo de uma skill carregavel:

```python
def register(factory):
    factory.register_agent("nome_do_papel", ClasseDoAgente)
```

Depois do registro, o agente pode ser criado com:

```python
factory.get_agent("nome_do_papel", **kwargs)
```

## Estado Atual

A extensibilidade existe e e testada pelo contrato da factory. Ainda nao ha CLI
propria para listar ou validar skills.

## Melhorias Recomendadas

1. Definir um contrato padrao de metadados por skill.
2. Adicionar exemplos de uso real dentro de pipelines.
3. Documentar exemplos reais de uso dentro dos pipelines.
4. Separar utilitarios que nao sao agentes de skills que registram agentes.
