# Estrategia de Genero

O modulo `genre_strategy.py` carrega regras de estilo por genero e idioma a
partir da pasta `genres/`.

## Entradas

Variaveis de ambiente:

- `AUTOBOOK_LANGUAGE`: idioma ativo. Valores usados hoje: `EN`, `PT-BR`.
- `AUTOBOOK_GENRE`: genero ativo. Exemplos existentes: `drama`, `crime_mystery`, `cyber_horror`, `light_novel`.

Arquivos:

- `genres/EN/*.txt`
- `genres/PT-BR/*.txt`

## Fallback

A classe `GenreStrategy` tenta carregar nesta ordem:

1. `genres/{AUTOBOOK_LANGUAGE}/{AUTOBOOK_GENRE}.txt`
2. `genres/EN/{AUTOBOOK_GENRE}.txt`
3. `genres/{AUTOBOOK_LANGUAGE}/drama.txt`
4. `genres/EN/drama.txt`

Se nenhum arquivo final existir, levanta `FileNotFoundError`.

## Uso No Codigo

`prompt_loader.load_genre_rules()` instancia `GenreStrategy` e retorna as
diretrizes completas de estilo. O pipeline de geracao usa essas regras ao
instanciar agentes e montar prompts.

## API Relevante

- `get_style_guidelines()`: retorna o texto integral das regras carregadas.
- `get_anti_patterns()`: tenta extrair linhas de secoes chamadas `PADROES A EVITAR` ou `PATTERNS TO AVOID`.

## Status v0

Funcional e testado indiretamente pelo carregamento de prompts/idioma. Ainda
falta documentar o contrato editorial esperado dentro de cada arquivo de genero.

