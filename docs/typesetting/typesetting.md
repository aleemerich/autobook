# Tiposetagem no Autobook

## Visão Geral

O sistema de tiposetagem do Autobook converte o texto gerado dos capítulos em formatos de publicação finais como PDF, EPUB e outros formatos de documento.

> **Status v0:** a automacao efetiva gera `typeset/chapters_content.tex` a
> partir de `chapters/ch_*.md` via `typeset/build_tex.py`. A compilacao final
> de PDF e a geracao de EPUB dependem de ferramentas externas e de passos
> manuais.

## Estrutura do Diretório de Tiposetagem

```
/typeset
├── epub_colophon.md
├── epub_back_cover.md
├── epub_front_matter.md
├── epub_style.css
├── build_tex.py
├── chapters_content.tex
├── novel.tex
└── epub_metadata.yaml
```

## Componentes de Tiposetagem

### 1. Arquivos de Entrada LaTeX

#### novel.tex
- **Propósito**: Arquivo LaTeX principal que compila o livro completo

#### chapters_content.tex
- **Propósito**: Contém o conteúdo de todos os capítulos formatados para LaTeX

### 2. Arquivos de Metadata EPUB

#### epub_metadata.yaml
- **Propósito**: Define metadata básica para o arquivo EPUB

#### epub_front_matter.md
- **Propósito**: Conteúdo que aparece antes do conteúdo principal no EPUB

#### epub_back_cover.md
- **Propósito**: Conteúdo que aparece na capa traseira do EPUB

#### epub_colophon.md
- **Propósito**: Informações de produção que aparecem no final do livro

### 3. Arquivos de Estilo

#### epub_style.css
- **Propósito**: Define o estilo visual para versões EPUB do livro

### 4. Scripts de Processamento

#### build_tex.py
- **Propósito**: Gera o arquivo LaTeX principal e o conteúdo dos capítulos

## Fluxo de Trabalho de Tiposetagem

### Geração de PDF via LaTeX
1. **Preparação dos Capítulos**:
   - Os capítulos finais estão em `chapters/ch_XX.md`
   - Estes arquivos devem representar a versão final, aprovada do texto

2. **Conversão para LaTeX**:
   - `build_tex.py` lê cada arquivo de capítulo
   - Converte Markdown para LaTeX (cabeçalhos, ênfase, listas, etc.)
   - Estrutura o conteúdo usando comandos LaTeX apropriados (`\chapter`, `\section`, etc.)
   - Gera `chapters_content.tex` com todo o conteúdo do livro
   - Gera ou atualiza `novel.tex` com preâmbulo adequado e inclusão do conteúdo

3. **Compilação LaTeX**:
   - O usuário executa `pdflatex novel.tex` (ou similar) no diretório typeset/
   - O sistema LaTeX processa o arquivo, resolvendo referências, gerando sumário, etc.
   - Pode ser necessário executar múltiplas vezes para resolver todas as referências
   - Gera `novel.pdf` como saída final

4. **Pós-Processamento** (opcional):
   - Conversão de PDF para outros formatos se necessário
   - Verificação de qualidade do PDF gerado
   - Distribuição ou archivamento do arquivo final

### Geração de EPUB

Status v0: fluxo manual. O repositorio contem arquivos de metadados e estilo
para EPUB, mas nao ha pipeline Python ativo que gere um EPUB completo de ponta
a ponta.
1. **Preparação do Conteúdo**:
   - Os capítulos finais estão em `chapters/ch_XX.md`
   - Arquivos de metadata EPUB estão em `/typeset/` (`epub_metadata.yaml`, `epub_front_matter.md`, etc.)

2. **Processamento de Metadata**:
   - Ler `epub_metadata.yaml` para obter informações básicas do livro
   - Processar `epub_front_matter.md`, `epub_back_cover.md`, `epub_colophon.md` para conteúdo estrutural

3. **Conversão de Conteúdo**:
   - Converter cada arquivo de capítulo de Markdown para XHTML apropriado para EPUB
   - Aplicar estilos de `epub_style.css` apropriadamente
   - Estruturar o conteúdo com hierarquia de títulos correta (h1 para capítulos, h2 para seções, etc.)

4. **Montagem do EPUB**:
   - Combinar metadata, conteúdo e estilos em um arquivo EPUB válido
   - Gerar sumário eletrônico (toc.ncx ou nav.xhtml)
   - Incluir arquivos de capa (se fornecidos)
   - Validar o arquivo EPUB resultante contra padrões EPUB

5. **Pós-Processamento** (opcional):
   - Verificar o EPUB em diferentes leitores
   - Fazer ajustes de qualidade se necessário
   - Distribuir ou archivar o arquivo final


## Integração com o Sistema Principal

O sistema de tiposetagem está atualmente separado do pipeline principal de geração de livros, mas pode ser integrado de várias maneiras:

### Integração Atual
- Os capítulos devem ser movidos manualmente para o diretório `typeset/` ou acessados diretamente de `chapters/`
- O usuário executa os scripts de tiposetagem manualmente após concluir o processo de geração e revisão
- Não há automação direta do pipeline principal para o tiposetagem

### Possíveis Integrações Futuras
1. **Etapa de Pipeline de Tiposetagem**: Adicionar um step ao pipeline que execute automaticamente os scripts de tiposetagem após a conclusão de todos os capítulos
2. **Geração Sob Demanda**: Permitir que os usuários especifiquem um formato de saída (PDF, EPUB, etc.) como parte do comando `run.py`
3. **Notificação de Conclusão**: Integrar o tiposetagem com o sistema de notificação para alertar quando os capítulos estão prontos para tiposetagem
4. **Versionamento de saída**: Arquivar automaticamente versões diferentes do livro em diferentes formatos à medida que são gerados


## Customização e Extensão

### Customização de Preâmbulo LaTeX
O arquivo `novel.tex` (gerado por `build_tex.py`) pode ser modificado para:
- Alterar o tamanho da página (letter, A4, etc.)
- Ajustar margens e espaçamento
- Adicionar pacotes LaTeX específicos (para fontes, símbolos, etc.)
- Modificar o estilo de cabeçalhos e rodapés
- Alterar a aparência do sumário e outros elementos frontais
- Configurar hiperlinks e metadata PDF

### Customização de Estilos EPUB
O arquivo `epub_style.css` pode ser modificado para:
- Alterar famílias de fontes (serif, sans-serif, monospace)
- Ajustar tamanhos de fonte para diferentes elementos
- Modificar espaçamento e identação
- Alterar cores (se suportado pelo leitor EPUB)
- Personalizar o estilo de links e navegação
- Ajustar a aparência de blocos especiais (citações, notas, etc.)
- Customizar o sumário eletrônico appearance

### Customização de Metadata EPUB
O arquivo `epub_metadata.yaml` pode ser modificado para:
- Alterar título, autor, data de publicação
- Adicionar ou modificar identificadores (ISBN, DOI, etc.)
- Atualizar descrição, palavras-chave e categorias
- Modificar informações de direitos autorais e licença
- Adicionar metadata específica para distribuidores ou plataformas

## Fluxo de Trabalho Recomendado

### Após Concluir Geração e Revisão
1. **Verificar Capítulos Finais**:
   - Certificar-se de que todos os capítulos estão em `chapters/` com numeração correta (ch_01.md, ch_02.md, etc.)
   - Verificar que nenhum capítulo está marcado como tentante ou incompleto
   - Confirmar que o arquivo `state.json` reflete o número correto de capítulos concluídos

2. **Preparar Arquivos de Tiposetagem**:
   - Garantir que `build_tex.py` esteja atualizado e funcional
   - Verificar que os arquivos de metadata EPUB estejam completos e corretos
   - Confirmar que `epub_style.css` reflete o estilo desejado

3. **Gerar Arquivos LaTeX**:
   ```bash
   cd typeset/
   python build_tex.py
   # Isso deve gerar chapters_content.tex e atualizar novel.tex
   ```

4. **Compilar PDF** (se desejado):
   ```bash
   # Pode ser necessário instalar uma distribuição LaTeX como TeX Live ou MikTeX
   pdflatex novel.tex
   # Executar múltiplas vezes se necessário para referências
   bibtex novel  # Se usando bibliografia
   pdflatex novel.tex
   pdflatex novel.tex
   # Resultado: novel.pdf
   ```

5. **Gerar EPUB** (se desejado):
   - Usar ferramenta como `pandoc` ou `ebook-convert` (do Calibre)
   - Exemplo com pandoc:
     ```bash
     pandoc novel.tex -o novel.epub --epub-metadata=epub_metadata.yaml        --epub-stylesheet=epub_style.css        --epub-chapter-level=1
     ```
   - Exemplo com Calibre:
     ```bash
     ebook-convert novel.tex novel.epub --epub-metadata=epub_metadata.yaml        --epub-stylesheet=epub_style.css
     ```

6. **Verificar Saída**:
   - Abrir o PDF gerado em um leitor para verificar formatação
   - Abrir o EPUB em diferentes leitores ou dispositivos para verificar compatibilidade
   - Fazer ajustes nos arquivos de fonte ou estilo conforme necessário


## Pontos de Melhoria e Antipadrões

### Antipadrões Atuais
1. **Separação do Pipeline Principal**: O tiposetagem está completamente separado do pipeline de geração de livros
2. **Processo Manual**: Requer intervenção manual do usuário para executar scripts e comandos
3. **Falta de Integração de Estado**: Não usa `state.json` ou `book_data/` para determinar o que deve ser typesetado
4. **Dependência de Ferramentas Externas**: Requer que o usuário tenha instalado distribuições LaTeX ou ferramentas de conversão EPUB
5. **Personalização Limitada**: Alguns aspectos da geração podem ser difíceis de personalizar sem modificar scripts
6. **Tratamento de Erros Variável**: Consistência variável no tratamento de erros durante o processo de typesetagem

### Sugestões de Refatoramento
1. **Integrar ao Pipeline Principal**: Adicionar um step de tiposetagem ao pipeline que execute automaticamente após a conclusão de todos os capítulos
2. **Automatizar Geração de Saída**: Criar comandos ou opções que permitam especificar formatos de saída diretamente (ex: `run.py --pipeline book_generation --output-format pdf`)
3. **Melhorar Tratamento de Erros**: Adicionar detecção e recuperação de erros mais robustos durante o processo de typesetagem
4. **Fornecer Ferramentas de Conversão Integradas**: Em vez de depender exclusivamente de ferramentas externas, considerar integrar capacidades básicas de conversão
5. **Adicionar Suporte a Múltiplos Formatos**: Expandir além de PDF e EPUB para incluir outros formatos como MOBI, AZW3, HTML, etc.
6. **Mejorar Customização**: Tornar mais fácil para usuários personalizarem aspectos da saída sem modificar código-fonte
7. **Adicionar Geração de Sumário e Índice**: Integrar automaticamente geração de sumário detalhado e índice alfabético quando apropriado
8. **Integrar Verificação de Qualidade**: Adicionar verificações automáticas de qualidade do output gerado (por exemplo, verificar se todos os capítulos estão presentes, se a numeração está correta, etc.)

### Boas Práticas Presentes
1. **Separação de Responsabilidades Claras**: Cada componente tem uma responsabilidade bem definida (metadata, estilo, conteúdo, processamento)
2. **Modularidade**: Fácil substituir ou atualizar componentes individuais (por exemplo, trocar o arquivo de estilo sem afetar outros componentes)
3. **Uso de Formatos Padrão**: Baseia-se em padrões amplamente suportados (LaTeX para PDF, EPUB3 para livros eletrônicos)
4. **Flexibilidade de Personalização**: Permite personalização significativa através de arquivos de configuration externos
5. **Documentação Inline**: Alguns arquivos contêm comentários explicativos sobre seu propósito e uso
6. **Separação de Apresentação e Conteúdo**: Mantém uma distinção clara entre o conteúdo do livro e sua formatação


## Exemplo de Arquivos

O sistema de tiposetagem inclui vários arquivos de exemplo que demonstram como configurar a geração de PDF e EPUB.

### novel.tex (exemplo simplificado)
Este é o arquivo LaTeX principal que define a estrutura do documento:
- Configurações de página, fonte e espaçamento
- Estrutura do livro (preâmbulo, conteúdo principal, posfácio)
- Inclusão dos capítulos processados

### chapters_content.tex (exemplo simplificado)
Este arquivo contém o conteúdo formatado dos capítulos:
- Cada capítulo como uma seção LaTeX
- Formatação consistente de títulos e parágrafos
- Espaçamento adequado para leitura

### epub_metadata.yaml (exemplo simplificado)
Define a metadata para o arquivo EPUB:
- Título, autor e idioma do livro
- Identificador único (ISBN)
- Data de publicação e editora
- Descrição e palavras-chave

### epub_style.css (exemplo simplificado)
Controla a aparência visual do EPUB:
- Famílias e tamanhos de fonte
- Espaçamento e identação de parágrafos
- Estilo de títulos e blocos de citação
- Configuração de links e navegação

## Conclusão

O sistema de tiposetagem do Autobook fornece as ferramentas necessárias para converter o texto gerado dos capítulos em formatos de publicação profissionais como PDF e EPUB. Sua implementação demonstra:

1. **Separação de Responsabilidades Claras**: Cada componente tem uma responsabilidade bem definida (metadata, estilo, conteúdo, processamento)
2. **Uso de Padrões Abertos**: Baseia-se em formatos amplamente suportados e não proprietários (LaTeX para PDF, EPUB3 para livros eletrônicos)
3. **Flexibilidade de Personalização**: Permite significativa personalização através de arquivos de configuration externos
4. **Modularidade**: Fácil substituir ou atualizar componentes individuais sem afetar todo o sistema
5. **Documentação Adequada**: Contém informações suficientes para entender e usar o sistema de tiposetagem

Embora atualmente esteja separado do pipeline principal de geração de livros, o sistema de tiposetagem oferece uma base sólida para produzir saída de alta qualidade adequada para distribuição. Para melhorar ainda mais o sistema, recomenda-se integrar mais diretamente com o pipeline principal, automatizar o processo de geração de saída e expandir o suporte para outros formatos de saída além de PDF e EPUB.

O design atual permite que usuários com conhecimento técnico produzam livros com aparência profissional adequados para auto-publicação, compartilhamento ou arquivamento, mantendo ao mesmo tempo a separação entre a criação de conteúdo (tratada pelo pipeline principal) e sua apresentação final (tratada pelo sistema de tiposetagem).
