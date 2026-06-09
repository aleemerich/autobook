# Análise de Qualidade no Autobook

## Visão Geral

O sistema de análise de qualidade do Autobook implementa mecanismos especializados para detectar, medir e melhorar a qualidade do texto gerado, com foco particular na identificação e redução de "slop" (texto genérico, clichês de AI e padrões de escrita de baixa qualidade) e na garantia de consistência com lore e regras estabelecidas.

Este sistema é implementado principalmente através de:
1. Módulos especializados em `/skills/` (`redundancy_detector.py`, `create_agent.py`)
2. O módulo de avaliação (`evaluate.py`) que inclui detecção de slop e análise de conformidade
3. Scripts e utilitários que ajudam a monitorar e melhorar a qualidade ao longo do processo de geração

O foco da análise de qualidade é garantir que o texto gerado seja:
- **Original**: Livre de clichês de AI e padrões de escrita genéricos
- **Consistente**: Adere ao lore, cânone e regras estabelecidos para o projeto
- **Específico**: Usa linguagem precisa e concreta em vez de termos vagos e abstratos
- **Engajador**: Mantém o interesse do leitor através de boa prosa, voz consistente e desenvolvimento eficaz de personagens e trama

## Módulos de Habilidade de Análise de Qualidade

### 1. redundancy_detector.py
Detecta e analisa redundâncias no texto, incluindo repetições de palavras, frases e estruturas que podem indicar escrita de baixa qualidade ou falta de variedade.

#### Funções Principais
- Detecção de repetições de palavras próximas
- Análise de variação de comprimento de frases
- Identificação de estruturas de parágrafo repetitivas
- Medição de léxicos diversity (riqueza de vocabulário)
- Detecção de padrões de início de frase repetitivos

#### Integração com o Sistema
Usado principalmente durante:
- Avaliação de capítulo para contribuir com métricas de qualidade de prosa
- Feedback de revisão editorial para identificar áreas de melhoria
- Análise pós-geração para relatórios de qualidade

#### Métricas Fornecidas
- **Palavras repetidas**: Contagem de palavras que aparecem muito próximas umas das outras
- **Variação de comprimento de frases**: Desvio padrão do comprimento de frases (valores mais altos indicam melhor variação)
- **Repetição de estruturas de parágrafo**: Similaridade entre parágrafos consecutivos
- **Índice de diversidade léxica**: Relação entre palavras únicas e total de palavras
- **Padrões de início de frase**: Frequência de palavras iniciais repetitivas

#### Exemplos de Detecção
- Redundância: "Ela foi ao mercado. Ela comprou pão. Ela voltou para casa." (repetição de "Ela" no início de frases)
- Baixa variação: Sequência de 5 frases todas com 8-10 palavras
- Estrutura repetitiva: Múltiplos parágrafos seguindo o mesmo padrão "Descrição → Ação → Reflexão"

### 2. create_agent.py
Implementa mecanismos para criar agentes especializados dinamicamente, permitindo a extensão do sistema de agentes literários além dos tipos built-in.

#### Funções Principais
- Registro dinâmico de novas classes de agente
- Carregamento de agentes de habilidade a partir de arquivos em `/skills/`
- Integração com o `AgentFactory` para fornecer uma interface unificada
- Suporte para agentes com lógica personalizada de processamento

#### Integração com o Sistema de Qualidade
Permite criar agentes especializados para:
- Detecção específica de tipos de slop
- Análise de conformidade com regras de projeto específicas
- Geração de feedback especializado para melhoria de qualidade
- Agentes de revisão especializados por gênero ou tipo de texto

#### Como Funciona
1. Arquivos de habilidade em `/skills/` (ex: `redundancy_detector.py`, `create_agent.py`) seguem um padrão específico
2. Eles contêm uma função `register(factory)` que registra novos tipos de agente com o `AgentFactory`
3. O `AgentFactory.load_skill_agent()` carrega dinamicamente esses agentes quando solicitado
4. Os agentes registrados podem então serem usados como qualquer outro agente built-in

#### Exemplo de Arquivo de Habilidade
```python
# skills/my_quality_agent.py
from agents import Agent

def register(factory):
    """Registra este agente com o factory fornecido."""
    factory._agents_registry["my_quality"] = MyQualityAgent

class MyQualityAgent(Agent):
    def __init__(self, quality_threshold: float = 7.0):
        super().__init__(
            name="MyQualityAgent",
            system_prompt="Você é um agente especializado em análise de qualidade literária. "
                         "Seu trabalho é analisar texto e fornecer feedback específico "
                         "sobre como melhorar sua qualidade com base em critérios estabelecidos.",
            temperature=0.3
        )
        
    def execute(self, prompt: str) -> str:
        # Implementação específica de análise de qualidade
        # ...
        return analysis_result
```

## Integração com o Sistema de Avaliação

O módulo `evaluate.py` contém a maior parte da lógica de análise de qualidade, particularmente através de:

### Detecção de Slope
A função `_check_slop(text: str)` no `evaluate.py` implementa detecção abrangente de slop através de:

#### Tier 1 Palavras Proibidas
Palavras que devem ser evitadas completamente pois são fortes indicadores de escrita de AI genérica:
- "delve", "tapestry", "myriad", "leveraged", "navigate", "realm", "steadfast", "undertaken", "endeavor"
- Penalidade significativa quando encontradas (geralmente 1-2 pontos por ocorrência)

#### Tier 2 Palavras Suspeitas
Palavras que devem ser evitadas quando possível, mas que podem ter uso legítimo em contextos específicos:
- "utilize", "facilitate", "parameter", "interface", "synergy", "leverage", "robust", "comprehensive"
- Penalidade menor que Tier 1, mas ainda significativa

#### Tiques Estruturais de AI
Padrões de escrita estrutural que são comuns em texto gerado por AI:
- Uso excessivo de travessões — (mais de 15 por 1000 palavras)
- Uso excessivo de ponto e vírgula
- Uso excessivo de parênteses
- Uso excessivo de dois pontos
- Iniciação de frases com estruturas repetitivas

#### Tells de Ficção de AI
Clichês comuns em ficção gerada por AI:
- "suddenly", "inexplicably", "as if by magic", "fortunately", "unfortunately"
- "it turned out that", "little did they know", "unbeknownst to them"
- "couldn't help but", "found themselves", "found it"

#### Cálculo da Penalidade de Slope
A penalidade de slope é calculada usando uma fórmula ponderada:
```
slop_penalty = (tier1_count * peso1) + (tier2_count * peso2) + 
               (structural_tics_count * peso3) + (fiction_tells_count * peso4) + 
               (em_dash_excess * peso5)
```
Onde os pesos são ajustados para refletir o impacto relativo de cada tipo de slope na qualidade geral.

### Avaliação das Dimensões Narrativas
A função `_check_narrative_dimensions(text: str, chapter_num: int)` avalia sete aspectos específicos da qualidade narrativa:

#### 1. voice_adherence
Mede quão bem o texto mantém a voz e tom estabelecidos para o livro.
- Verifica consistência em nível de formalidade, escolha de palavras e estilo
- Detecta mudanças súbitas de tom que não são justificadas pelo contexto narrativo
- Analisa padrões de vocabulário e estruturas de frase ao longo do texto

#### 2. beat_coverage
Avalia quão bem o capítulo cobre os beats narrativos planejados no outline.
- Compara o conteúdo do capítulo com os beats especificados no outline.md
- Identifica beats que estão ausentes, parcialmente cobertos ou excessivamente enfatizados
- Verifica se a progressão emocional e lógica segue o plano

#### 3. character_voice
Mede a distinctividade e consistência das vozes dos personagens.
- Analisa padrões de diálogo para cada personagem
- Verifica se personagens têm vocabulário, comprimento de frase e estilo de fala distintos
- Identifica quando personagens soam muito parecidos ou quando a voz de um personagem muda inadequadamente

#### 4. plants_seeded
Avalia quão bem elementos são plantados para futuro pagamento (foreshadowing).
- Identifica menções a objetos, informações ou eventos que parecem ser importantes
- Verifica se esses elementos são adequadamente desenvolvidos ou explicados posteriormente
- Detecta quando elementos importantes são introduzidos sem preparo ou quando preparo é feito sem pagamento

#### 5. prose_quality
Mede a qualidade geral da escrita, fluência e legibilidade.
- Analisa variação de comprimento de frases
- Verifica uso adequado de pontuação e estrutura de frase
- Detecta repetições desnecessárias, construções awkward e falta de fluência
- Avalia a musicalidade e ritmo do texto

#### 6. lore_integration
Avalia quão bem elementos de mundo e lore são integrados naturalmente no texto.
- Detecta parágrafos explanatórios que interrompem o fluxo narrativo
- Verifica se informações de mundo são apresentadas através de ação e diálogo em vez de exposição direta
- Identifica quando lore parece "colado" em vez de orgânico ao narrative

#### 7. engagement
Mede quão envolvente e cativante é o texto para o leitor.
- Analisa presença de ganchos, tensão e questões narrativas
- Verifica variação no ritmo e pacing
- Detecta seções que são previsíveis, monótonas ou falta de impulso narrativo
- Avalia o uso eficaz de conflitos, descobertas e revelações

## Mecanismo de Feedback e Melhoria

O sistema de análise de qualidade não apenas mede, mas também fornece feedback específico para melhoria através de:

### Formatação de Feedback para LLMs
A função `format_eval_feedback(eval_data: dict, retry_idx: int)` no `evaluate.py` converte métricas de avaliação em diretrizes de texto que podem ser usadas por LLMs para melhorar o texto.

#### Exemplo de Saída de Feedback
```
### PROBLEMAS DE SLOP CRÍTICO:
- PALAVRAS PROIBIDAS usadas (MUDAR IMEDIATAMENTE): 'delve' (usado 2 vezes), 'tapestry' (usado 1 vezes)

### ESTILO & VOCABULÁRIO (SLOP SECUNDÁRIO):
- Palavras suspeitas usadas: 'utilize' (usado 3 vezes), 'parameter' (usado 1 vezes)
- Clichês/tells de IA detectados: 'suddenly' (usado 1 vezes), 'as if by magic' (usado 2 vezes)

### DEFICIÊNCIAS NAS DIMENSÕES NARRATIVAS:
#### Dimensão 'voice_adherence' (Nota 5.5):
  * Ponto fraco: "Mudança súbita de tom formal para informal no parágrafo 3"
  * Correção sugerida: "Manter consistência na voz narrativa ao longo do capítulo"

#### Dimensão 'beat_coverage' (Nota 4.0):
  * Ponto fraco: "O beat 3 ('Descobrir pista no laboratório') não foi adequadamente desenvolvido"
  * Correção sugerida: "Expandir a cena no laboratório para incluir a descoberta e sua análise inicial"

#### Dimensão 'lore_integration' (Nota 5.0):
  * Ponto fraco: "Parágrafo explicativo sobre limites da magia interrompe fluxo de ação"
  * Correção sugerida: "Integrar a explicação do sistema mágico através da ação e descoberta dos personagens"
```

#### Como o Feedback é Usado
1. Durante revisão editorial, o feedback é combinado com briefs específicos do capítulo
2. O texto resultante é passado para `gen_revision.py` como um brief de correção
3. A temperatura é ajustada baseado na tentativa de retry (tentativas iniciais usam temperatura menor para correções precisas, tentativas posteriores usam temperatura maior para explorar soluções criativas)
4. O LLM gera uma versão revisada do capítulo tentando abordar todos os pontos de feedback

## Scripts e Utilitários de Análise de Qualidade

### verify_continuity.py
Verifica consistência entre capítulos, particularmente focada em elementos que afetam capítulos futuros.

#### Funcionalidade
- Lê `editorial.md` para identificar mudanças declaradas como afetando capítulos futuros
- Verifica se essas mudanças são consistentes com o conteúdo real dos capítulos
- Detecta quando elementos que deveriam afetar capítulos futuros são omitidos ou alterados inadequadamente
- Identifica quando mudanças que deveriam ser locais estão afetando inadequadamente capítulos futuros

#### Saída
- Código de saída 0 se a continuidade passar
- Código de saída não-zero se falhar, com mensagem de erro detalhada
- Arquivo de log detalhado em `logs/eval_logs/` quando executado com verbose

### gen_revision.py
Script dedicado a realizar revisões de capítulo baseado em briefs editoriais.

#### Funcionalidade
- Lê um capítulo atual de `chapters/ch_XX.md`
- Aplica um brief editorial (arquivo de texto contendo diretrizes de revisão)
- Gera uma versão revisada do capítulo usando LLM
- Salva o resultado de volta no mesmo arquivo (sobrescrevendo o original)

#### Integração com Análise de Qualidade
- Os briefs editoriais são frequentemente gerados a partir da saída de `format_eval_feedback()`
- Permite que métricas de avaliação sejam convertidas diretamente em ações de revisão

## Fluxo de Trabalho de Análise de Qualidade

### Durante Geração de Capítulo (book_generation.py)
1. Após síntese sequencial de críticas, o capítulo é avaliado usando `evaluate_chapter(ch)`
2. A análise inclui:
   - Verificação de conformidade com cânone
   - Detecção de slop (Tier 1, Tier 2, tiques estruturais, tells de ficção)
   - Avaliação das sete dimensões narrativas
   - Identificação das três frases mais fracas
3. Se a `overall_score` >= `CHAPTER_THRESHOLD` E a validação de continuidade passar:
   - Capítulo é aceito e commitado no Git
4. Se não:
   - Capítulo passa por outra tentativa (até `MAX_CHAPTER_ATTEMPTS`)
   - Se todas as tentativas falharem, a melhor tentativa é mantida e um aviso é emitido

### Durante Revisão Editorial (editorial_revision.py)
1. **Baseline**: Avalia a versão atual do capítulo para estabelecer pontuação pré-revisão
2. **Para cada tentativa de revisão** (até `NUM_EDITORIAL_RETRIES`):
   - Gera feedback formatado usando `format_eval_feedback(eval_data, retry_idx)`
   - Combina com briefs específicos do capítulo e diretrizes gerais
   - Gera uma versão revisada usando `gen_revision.py`
   - Avalia o resultado
   - Se melhorar ou manter qualidade, considera a tentativa bem-sucedida
3. **Resultado Final**:
   - Se melhoria for alcançada, versão revisada é commitada
   - Se não, reverte para versão original ou mantém melhor tentativa até então

### Análise Pós-Geração
Após completar o livro ou em pontos específicos, análises adicionais podem ser feitas:
- Análise de tendências de qualidade ao longo dos capítulos
- Identificação de problemas recorrentes de slop ou consistência
- Geração de relatórios de qualidade resumidos
- Comparação com benchmarks estabelecidos

## Pontos de Melhoria e Antipadrões

### Antipadrões Atuais
1. **Detecção de Slope Baseada em Lista**: Depende fortemente de listas pré-definidas de palavras que podem não capturar todas as variações de slop
2. **Heurísticas Simplificadas para Dimensões Narrativas**: Algumas dimensões usam detecção baseada em regras simples que podem não capturar nuances complexas
3. **Falta de Consciência de Contexto**: Algumas verificações não levam em conta suficientemente o contexto narrativo específico ou justificativas para certas escolhas de escrita
4. **Escalonamento Linear de Penalidades**: Assumir que cada ocorrência de slop contribui igualmente para a penalidade total
5. **Métricas Estáticas**: Não se adaptam automaticamente baseado no gênero específico, estágio da história ou feedback acumulado

### Sugestões de Refatoramento
1. **Aprimorar Detecção de Slope**: 
   - Incorporar modelos de linguagem menores para detectar padrões de slop mais sofisticados
   - Usar abordagens de aprendizado de máquina treinados em exemplos de slop vs escrita de qualidade
   - Permitir que usuários adicionem palavras personalizadas às listas de proibição/suspeita
2. **Aprimorar Análise de Dimensões Narrativas**:
   - Incorporar análise de estrutura narrativa mais profunda (por exemplo, usando árvores de dependência ou análise semântica)
   - Usar modelos de linguagem para avaliar aspectos como voz, engajamento e integração de lore de forma mais sofisticada
   - Permitir pesos personalizados para diferentes dimensões baseado no gênero ou tipo de história
3. **Adicionar Consciência de Contexto**:
   - Melhorar verificações de lore para entender quando desvios são justificados pelo contexto narrativo
   - Incorporar análise de intenção do autor quando possível (por exemplo, através de notas do autor ou diretrizes específicas)
   - Considerar o estágio da história ao avaliar certos aspectos (por exemplo, expectativas diferentes para abertura vs clímax)
4. **Aprimorar Cálculo de Penalidades**:
   - Incorporar fatores de mitigação (por exemplo, uma palavra de nível 1 pode ser aceitável se for parte de uma citação intencional)
   - Usar abordagens mais sofisticadas para calcular o impacto relativo de diferentes tipos de problemas
   - Considerar a frequência e distribuição de problemas ao longo do texto (não apenas contagem total)
5. **Tornar Métricas Adaptativas**:
   - Permitir que o sistema aprenda quais métricas são mais preditivas de qualidade para este projeto específico
   - Ajustar pesos e thresholds baseado em feedback histórico
   - Incorporar aprendizagem online à medida que mais capítulos são gerados e avaliados

### Boas Práticas Presentes
1. **Separação de Responsabilidades Claras**: Cada aspecto da análise de qualidade é tratado por um mecanismo especializado
2. **Feedback Acionável**: Métricas são convertidas em diretrizes específicas que podem ser usadas para melhoria direta
3. **Abordagem Holística**: Analisa múltiplas dimensões da qualidade, não apenas um único aspecto
4. **Integração com Pipeline**: Bem integrado nos pontos críticos de tomada de decisão do sistema
5. **Escalabilidade**: Fácil adicionar novos tipos de análise ou aprimorar existentes
6. **Métodos Quantitativos e Qualitativos**: Combina medições objetivas com análise qualitativa para feedback mais rico
7. **Transparência**: Critérios e mecanismos de análise são bem documentados e compreensíveis

## Exemplo de Análise de Qualidade em Ação

Vamos considerar um parágrafo hipotético e como o sistema de análise de qualidade poderia responder:

### Texto Original
> Ela olhou para o horizonte infinito e de repente soube o que tinha que fazer. O mecanismo foi utilizado para facilitar a interface entre os componentes. Como por magia, a porta se abriu exatamente quando eles precisavam. Ela sentiu-se feliz porque tudo estava funcionando perfeitamente.

### Análise de Slope
- **Tier 1 Hits**: ["infinito" (não está na lista padrão, mas se estivesse), "delve" (não presente)]
- **Tier 2 Hits**: ["utilize" (1 vez), "facilitate" (1 vez), "interface" (1 vez)]
- **Fiction AI Tells**: ["de repente" (1 vez), "como por magia" (1 vez)]
- **Em Dash Density**: 0 (nenhum travessão usado)
- **Slop Penalty**: Calculada baseada nas contagens acima

### Análise das Dimensões Narrativas
- **voice_adherence**: Pode ser baixa se houver mudança súbita de tom
- **beat_coverage**: Depende se isso cobre adequadamente o beat planejado
- **character_voice**: Avalia se o diálogo soa natural para os personagens
- **plants_seeded**: Verifica se elementos importantes são adequadamente preparados
- **prose_quality**: Analisa variação de comprimento de frases, uso de pontuação, etc.
- **lore_integration**: Verifica se elementos de mundo são integrados naturalmente
- **engagement**: Avalia se o texto é cativante e mantém interesse

### Três Frases Mais Frágeis
Potencialmente identificaria as três frases como problemas devido ao uso combinado de slop, tells de fiction e possível falta de desenvolvimento adequado.

### Feedback Formatado
O sistema geraria feedback como:
```
### PROBLEMAS DE SLOP CRÍTICO:
- PALAVRAS PROIBIDAS usadas (MUDAR IMEDIATAMENTE): [nenhuma se nenhuma palavra de tier 1 estiver presente]

### ESTILO & VOCABULÁRIO (SLOP SECUNDÁRIO):
- Palavras suspeitas usadas: 'utilize' (usado 1 vezes), 'facilitate' (usado 1 vezes), 'interface' (usado 1 vezes)
- Clichês/tells de IA detectados: 'de repente' (usado 1 vezes), 'como por magia' (usado 1 vezes)

### DEFICIÊNCIAS NAS DIMENSÕES NARRATIVAS:
#### Dimensão 'voice_adherence' (Nota X.X):
  * Ponto fraco: [descrição específica]
  * Correção sugerida: [sugestão específica]

#### Dimensão 'lore_integration' (Nota X.X):
  * Ponto fraco: "Como por magia, a porta se abriu exatamente quando eles precisavam."
  * Correção sugerida: "Mostrar o mecanismo de abertura da porta através da ação dos componentes previamente estabelecidos"
```

### Texto Revisado (Exemplo)
> Ela analisou o horizonte distante, ponderando a tarefa que se apresentava diante dela. O mecanismo de acoplamento, previamente calibrado durante a semana de preparação, engatou suavemente os componentes principais. A pressão hidráulica nos pistões principais liberou a trava da porta, que se abriu com um sussurro de ar comprimido. Ela observou o medidor de pressão estabilizar-se nos níveis normais, confirmando que a sequência estava funcionando conforme planejado.

Este texto revisado:
- Remove palavras suspeitas de nível 2 ("utilize", "facilitate", "interface")
- Substitui tells de fiction ("de repente", "como por magia") por descrições mais específicas
- Melhora a voz através de vocabulário mais variado e estruturas de frase
- Integra melhor elementos de lore (mostrando o mecanismo em ação em vez de explicar)
- Mantém o engajamento através de descrição concreta e senso de progresso

## Conclusão

O sistema de análise de qualidade do Autobook fornece uma estrutura abrangente para garantir que o texto gerado atenda a padrões elevados de originalidade, consistência e qualidade literária. Sua implementação demonstra:

1. **Abordagem Multifacetada**: Analisa múltiplas dimensões da qualidade, desde detalhes técnicos de linguagem até aspectos mais abstratos de voz e engajamento
2. **Feedback Acionável**: Converte métricas abstratas em diretrizes específicas que podem ser usadas para melhoria direta
3. **Integração com Pipeline**: Bem integrado nos pontos críticos de tomada de decisão do sistema de geração de livros
4. **Escalabilidade**: Fácil aprimorar ou adicionar novos tipos de análise conforme necessário
5. **Transparência**: Critérios e mecanismos são bem documentados e compreensíveis
6. **Foco na Melhoria Contínua**: Não apenas mede qualidade, mas fornece mecanismos específicos para aprimorá-la

O design permite que escritores e editores tenham confiança de que o texto gerado não apenas é tecnicamente correto (em termos de conformidade com lore e regras), mas também possui qualidades literárias que o tornam engajador e valioso para leitores. Ao mesmo tempo, fornece aos desenvolvedores ferramentas poderosas para medir, entender e melhorar a qualidade do output do sistema ao longo do tempo.

Para melhorar ainda mais o sistema de análise de qualidade, recomenda-se:
1. Incorporar técnicas mais sofisticadas de detecção de slop (por exemplo, usando modelos de linguagem menores)
2. Aprimorar a análise de dimensões narrativas com abordagens mais profundas de compreensão de texto
3. Adicionar mais consciência de contexto às verificações de qualidade
4. Tornar as métricas mais adaptativas baseadas em feedback histórico
5. Expandir o sistema para incluir análise de qualidade em nível de livro, não apenas de capítulo