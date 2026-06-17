# Sistema de Avaliação do Autobook

## Visão Geral

O sistema de avaliação do Autobook implementa um conjunto abrangente de métricas e verificações para garantir a qualidade dos capítulos gerados. A entrada operacional continua sendo `evaluate.py`, mas a implementação foi dividida no pacote `evaluation/`, que separa detecção mecânica de slop, parsing/reparo de JSON, carregamento de arquivos, prompts e relatórios.

O sistema de avaliação é usado em múltiplos pontos do pipeline:
1. **Durante a geração de capítulo**: Para determinar se um capítulo atingiu o threshold de qualidade antes de avançar
2. **Durante a revisão editorial**: Para medir melhorias e guiar loops de correção
3. **Para validação de continuidade global**: Para garantir consistência entre capítulos

## Arquitetura e Design

### Fachada Principal: evaluate.py
Mantém a CLI (`--phase=foundation`, `--chapter=N`, `--full`) e as funções públicas compatíveis, como `evaluate_chapter(chapter_num: int) -> dict`, `evaluate_foundation()` e `evaluate_full()`.

### Pacote `evaluation/`
- `evaluation/slop.py`: detecção mecânica de slop.
- `evaluation/json_utils.py`: extração, reparo e validação de JSON retornado por LLM.
- `evaluation/io.py`: carregamento de arquivos de planejamento e capítulos.
- `evaluation/judge.py`: chamada ao juiz LLM.
- `evaluation/prompts.py`: prompts operacionais usados pela avaliação.
- `evaluation/reports.py`: escrita de `logs/eval_logs/` e `logs/edit_logs/`.

### Filosofia de Avaliação
O sistema adota uma abordagem holística que avalia:
- **Conformidade Técnica**: Consistência com lore, cânone e regras estabelecidas
- **Qualidade Literária**: Métricas de prosa, voz, estilo e engajamento
- **Adesão ao Gênero**: Conformidade com expectativas do gênero especificado
- **Estrutura e Progresso**: Cobertura de beats, plantação e pagamento de elementos narrativos
- **Originalidade e Qualidade**: Detecção e penalização de "slop" (texto genérico, clichês de AI)

## Componentes da Avaliação

O resultado de `evaluate_chapter()` é um dicionário com as seguintes seções principais:

### 1. canon_compliance
Avalia consistência com o lore estabelecido e cânone do livro.

#### Métricas:
- `score`: Pontuação de 0-10 (10 = perfeita conformidade)
- `violations`: Lista de violações específicas encontradas
- `details`: Informações adicionais sobre cada violação

#### O que é verificado:
- Nomes de personagens, objetos, locais
- Datas, idades e cronologia
- Regras do sistema mágico e suas limitações
- Fatos estabelecidos sobre personagens e mundo
- Relacionamentos e afiliações
- Eventos estabelecidos na história

#### Exemplo de violação:
```
"Cass tinha 25 anos no capítulo 3, mas agora tem 30 anos no capítulo 5 sem explicação temporal adequada"
```

### 2. slop
Detecta e penaliza "slop" - texto genérico, clichês de AI e padrões de escrita de baixa qualidade.

#### Sub-métricas:
- `tier1_hits`: Palavras proibidas de uso imediato (ex: "delve", "tapestry", "myriad")
- `tier2_hits`: Palavras suspeitas que devem ser evitadas quando possível
- `structural_ai_tics`: Tiques estruturais de escrita de AI
- `fiction_ai_tells`: Clichês e tells comuns de ficção de AI
- `em_dash_density`: Densidade de travessões (—) por 1000 palavras
- `slop_penalty`: Penalidade calculada baseada nas contagens acima (0-10 pontos)

#### Exemplos de slop detectado:
- **Tier 1**: "Ela olhou para o horizonte infinito, ponderando a complexa tapeçaria do destino."
- **Tier 2**: "O sistema foi utilizado para facilitar a interface entre os componentes."
- **Estrutural**: Uso excessivo de travessões — mais de 15 por 1000 palavras
- **Tell**: "Ela sentiu-se triste." (em vez de mostrar a tristeza através de ações)

### 3. Dimensões Narrativas
Avalia aspectos específicos da arte da narrativa em uma escala de 0-10.

#### Dimensões Avaliadas:
- `voice_adherence`: Quão bem o texto mantém a voz e tom estabelecidos para o livro
- `beat_coverage`: Quão bem o capítulo cobre os beats narrativos planejados no outline
- `character_voice`: Distinctividade e consistência das vozes dos personagens
- `plants_seeded`: Quão bem elementos são plantados para futuro pagamento (foreshadowing)
- `prose_quality`: Qualidade geral da escrita, fluência e legibilidade
- `lore_integration**: Quão bem elementos de mundo e lore são integrados naturalmente
- `engagement`: Quão envolvente e cativante é o texto para o leitor

#### Exemplos de baixa pontuação:
- **voice_adherence**: Mudança súbita de tom formal para informal sem justificativa narrativa
- **beat_coverage**: Ausência de beats importantes planejados no outline
- **character_voice**: Todos os personagens soando exatamente iguais
- **plants_seeded**: Menção de objeto importante sem nenhum contexto ou futuro pagamento aparente
- **prose_quality**: Frases repetitivas, construção pobre, falta de variação
- **lore_integration**: Parágrafos explanatórios de mundo que interrompem o fluxo narrativo
- **engagement**: Texto previsível, falta de tensão ou ganchos narrativos

### 4. three_weakest_sentences
Identifica as três frases mais fracas no capítulo para direcionar esforços de reescrita.

#### Formato:
- Array de strings contendo as três frases identificadas como mais problemáticas
- Baseado em combinação de fatores: grammar, estilo, clichês, fraqueza narrativa
- Usado no sistema de revisão editorial para gerar feedback específico

### 5. overall_score
Pontuação consolidada que combina todas as métricas acima em uma única medida de 0-10.

#### Cálculo:
A pontuação geral é calculada como uma média ponderada das diferentes componentes, com ajustes baseados nas penalidades de slop.

## Fluxo de Trabalho de Avaliação

### Durante Geração de Capítulo (book_generation.py)
1. Após síntese sequencial de críticas, o capítulo é avaliado usando `evaluate_chapter(ch)`
2. A `overall_score` é comparada com o `CHAPTER_THRESHOLD` (padrão: 6.0)
3. Se a pontuação ≥ threshold E a validação de continuidade passar, o capítulo é aceito
4. Se não, o capítulo passa por outra tentativa (até `MAX_CHAPTER_ATTEMPTS`, padrão: 3)

### Durante Revisão Editorial (editorial_revision.py)
1. **Baseline**: Avalia a versão atual do capítulo para estabelecer pontuação pré-revisão
2. **Após cada tentativa de revisão**: Avalia novamente para medir melhoria
3. **Formatação de Feedback**: `format_eval_feedback()` converte o dicionário de avaliação em diretrizes de texto para o LLM
4. **Critério de Sucesso**: A revisão é considerada bem-sucedida se:
   - `post_score >= pre_score` (não piorou)
   - `post_score >= 7.0` (atingiu threshold de qualidade editorial)
   - `slop_penalty == 0.0` (nenhum slop de nível 1 detectado)

### Durante Validação de Continuidade Global
- Usa o script separado `verify_continuity.py` que implementa verificações mais abrangentes
- Verifica consistência entre capítulos (elementos que afetam capítulos futuros)
- Retorna código de saída 0 se passar, não-zero se falhar
- Usado tanto durante geração de capítulo quanto como validação independente

## Detalhes de Implementação

### Fluxo de `evaluate_chapter(chapter_num: int) -> dict`
- Carrega camadas de planejamento e capítulo via `evaluation/io.py`.
- Monta o prompt de juiz usando `evaluation/prompts.py`.
- Tenta os modelos configurados em ciclos de degradação de contexto.
- Repara/valida JSON via `evaluation/json_utils.py`.
- Aplica penalidade mecânica de slop via `evaluation/slop.py`.
- Persiste logs de avaliação e edição via `evaluation/reports.py`.
- Orquestra todas as verificações acima
- Combina resultados em dicionário de retorno estruturado
- Calcula `overall_score` baseado nas componentes individuais

## Critérios e Thresholds

### Thresholds de Aceitação
- **Geração de Capítulo**: `overall_score >= CHAPTER_THRESHOLD` (padrão: 6.0)
- **Validação de Continuidade**: Script `verify_continuity.py` com threshold padrão de 7.0
- **Revisão Editorial**: `post_score >= 7.0` e `slop_penalty == 0.0` para considerar tentativa bem-sucedida

### Escalas de Pontuação
Todas as métricas individuais usam escala de 0-10 onde:
- **9-10**: Excelente, quase ou perfeitamente conforme o critério
- **7-8**: Bom, atende às expectativas com pequenas áreas para melhoria
- **5-6**: Satisfatório, atende ao mínimo necessário mas com espaço significativo para melhoria
- **3-4**: Insuficiente, problemas notables que afetam a qualidade
- **0-2**: Deficiente, falha básica em atender ao critério

## Integração com o Sistema de Agentes

Embora o sistema de avaliação não chame diretamente os LLMs, ele é usado pelos pipelines para:

1. **Tomada de Decisão**: Determinar se um capítulo é bom o suficiente para avançar no pipeline
2. **Geração de Feedback**: Converter métricas em diretrizes legíveis por humanos e LLMs para melhoria
3. **Validação de Qualidade**: Garantir que o texto gerado atende aos padrões estabelecidos antes de considerar o trabalho completo

### Exemplo de Uso em Pipeline
```python
from evaluate import evaluate_chapter

# Após gerar um capítulo
eval_result = evaluate_chapter(chapter_number)
score = eval_result.get("overall_score", 0.0)

if score >= CHAPTER_THRESHOLD:
    # Capítulo aceito, prosseguir para o próximo
    advance_to_next_chapter()
else:
    # Capítulo rejeitado, tentar novamente ou manter melhor tentativa até agora
    handle_rejected_chapter(eval_result)
```

### Exemplo de Geração de Feedback
```python
from evaluate import format_eval_feedback

# Após avaliação, gerar feedback para correção
feedback_str = format_eval_feedback(eval_data, retry_attempt_number)
# feedback_str contém diretrizes formatadas para o LLM seguir
```

## Pontos de Melhoria e Antipadrões

### Antipadrões Atuais
1. **Heurísticas Simplificadas**: Algumas métricas usam detecção baseada em palavras simples que podem gerar falsos positivos/negativos
2. **Falta de Consciência de Contexto**: Algumas verificações não levam em conta suficientemente o contexto narrativo específico
3. **Escalonamento Linear**: Assumir que todos os aspectos contribuem igualmente para a qualidade geral
4. **Limitações de Linguagem**: Otimizado principalmente para português do Brasil, pode não funcionar tão bem para outros idiomas
5. **Métricas Estáticas**: Não se adaptam automaticamente baseado no gênero específico ou estágio da história

### Sugestões de Refatoramento
1. **Aprimorar Detecção de Slop**: Usar abordagens mais sofisticadas como modelos de linguagem menores para detectar padrões de AI
2. **Incorporar Análise de Contexto**: Melhorar verificações de lore e continuidade com compreensão contextual maior
3. **Ponderação Dinâmica**: Ajustar pesos das métricas baseado no gênero, estágio da história ou tipo de capítulo
4. **Extensibilidade para Múltiplos Idiomas**: Projetar métricas para serem mais facilmente adaptáveis a outros idiomas
5. **Aprendizado Adaptativo**: Permitir que o sistema aprenda quais métricas são mais preditivas de qualidade para este projeto específico
6. **Visualização de Métricas**: Adicionar capacidades de relatório para rastrear tendências de métricas ao longo do tempo

### Boas Práticas Presentes
1. **Separação de Responsabilidades Claras**: Cada aspecto da avaliação é tratado por uma função especializada
2. **Métricas Abrangentes**: Cobrem múltiplas dimensões da qualidade literária e técnica
3. **Feedback Acionável**: Fornece informações específicas que podem ser usadas para melhoria direta
4. **Escalabilidade**: Fácil adicionar novas métricas ou aprimorar existentes
5. **Integração Pipeline**: Bem integrado nos pontos de tomada de decisão críticos do sistema
6. **Logging Detalhado**: Fornece informações suficientes para diagnóstico quando necessário
7. **Thresholds Configuráveis**: Permite ajustar padrões de aceitação conforme necessário

## Exemplo de Saída de Avaliação

Aqui está um exemplo simplificado do que `evaluate_chapter()` retorna:

```json
{
  "overall_score": 7.2,
  "canon_compliance": {
    "score": 9.0,
    "violations": [],
    "details": "Nenhuma violação de canon detectada"
  },
  "slop": {
    "tier1_hits": [],
    "tier2_hits": [
      ["utilize", 2],
      ["parameter", 1]
    ],
    "structural_ai_tics": [],
    "fiction_ai_tels": [
      ["suddenly", 1]
    ],
    "em_dash_density": 8.5,
    "slop_penalty": 1.5
  },
  "voice_adherence": {
    "score": 8.0,
    "fix": "Manter consistência na voz narrativa ao longo do capítulo",
    "weakest_moment": "Parágrafo 3 muda subitamente para tom mais formal",
    "score_threshold": 7
  },
  "beat_coverage": {
    "score": 6.5,
    "fix": "O beat 3 ('Descobrir pista no laboratório') não foi adequadamente desenvolvido",
    "weakest_moment": "Transição muito rápida entre a descoberta e a consequência",
    "score_threshold": 7
  },
  "character_voice": {
    "score": 7.5,
    "fix": "Diferenciar mais claramente os padrões de fala dos personagens secundários",
    "weakest_moment": "Diálogo do personagem X soa muito parecido com o do personagem Y",
    "score_threshold": 7
  },
  "plants_seeded": {
    "score": 8.0,
    "fix": "Plantear melhor o objeto que será importante no capítulo 7",
    "weakest_moment": "Menção do objeto X parece inesperada sem preparo adequado",
    "score_threshold": 7
  },
  "prose_quality": {
    "score": 7.0,
    "fix": "Variar mais o comprimento das frases para melhorar o ritmo",
    "weakest_moment": "Sequência de 3 frases curtas seguidas no parágrafo 5",
    "score_threshold": 7
  },
  "lore_integration": {
    "score": 8.5,
    "fix": "Integrar melhor a explicação do sistema mágico na ação em vez de exposição",
    "weakest_moment": "Parágrafo explicativo sobre limites da magia interrompe fluxo de ação",
    "score_threshold": 7
  },
  "engagement": {
    "score": 7.0,
    "fix": "Aumentar a tensão na cena de confronto inicial",
    "weakest_moment": "A cena começa muito calma considerando o contexto de perigo iminente",
    "score_threshold": 7
  },
  "three_weakest_sentences": [
    "Ela olhou para o horizonte e de repente soube o que tinha que fazer.",
    "O mecanismo foi utilizado para parameterizar a interface entre os componentes.",
    "Como por magia, a porta se abriu exatamente quando eles precisavam."
  ]
}
```

## Conclusão

O sistema de avaliação do Autobook fornece uma estrutura robusta e multidimensional para garantir a qualidade dos capítulos gerados literariamente. Sua implementação demonstra:

1. **Abordagem Holística**: Avalia múltiplas dimensões da qualidade literária e técnica, não apenas um único aspecto
2. **Feedback Acionável**: Fornece informações específicas que podem ser usadas diretamente para melhoria
3. **Integração Pipeline**: Bem integrado nos pontos críticos de tomada de decisão do sistema de geração de livros
4. **Extensibilidade**: Fácil aprimorar ou adicionar novas métricas conforme necessário
5. **Transparência**: Critérios claros e pontuações compreensíveis facilitam o ajuste e o diagnóstico
6. **Adaptação ao Contexto**: Considera o lore específico, outline e outros elementos de referência do projeto

O design permite que escritores e editores tenham confiança de que o texto gerado atende aos padrões de qualidade estabelecidos, enquanto fornece aos desenvolvedores uma ferramenta poderosa para medir e melhorar o desempenho do sistema ao longo do tempo.
