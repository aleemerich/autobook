FOUNDATION_PROMPT = """Evaluate these book planning documents.

SCORING CALIBRATION (read this before scoring anything):

  9-10: Could not improve this with a month of focused editorial work.
        Published-novel quality. You can name the specific published
        novel it competes with. Reserve 10 for work that SURPRISES you.
  7-8:  Strong. A skilled author could draft from this document with
        minimal invention. Gaps exist but are minor and enumerable.
  5-6:  Functional but thin. A writer would need to invent significant
        material on the fly. Major gaps or generic choices.
  3-4:  Sketchy. More questions than answers. Would require heavy
        supplementation before drafting.
  1-2:  Placeholder or stub. Not usable for drafting.
  0:    Empty or missing.

  A score of 8+ requires ZERO major gaps. A score of 9+ requires
  that you genuinely struggled to find flaws. Err toward lower scores.

MANDATORY: For EVERY dimension, before scoring, you must identify:
  (a) The single biggest GAP or WEAKNESS in that area
  (b) A specific, actionable improvement that would raise the score
  If you cannot find a gap, explain why you believe one doesn't exist.

VOICE DEFINITION:
{voice}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

OUTLINE:
{outline}

CANON (established facts):
{canon}

CROSS-CHECKS (perform these before scoring):
1. Check all example dialogue lines against ANTI-SLOP patterns:
   - Look for structural formulas repeated across characters
     ("not X, but Y" / "either X, or Y" / "there's a difference")
   - Check for AI rhetorical tics disguised as character voice
   - Deduct from character_distinctiveness if multiple characters
     share the same sentence structures
2. Check for missing NEGATIVE SPACE -- what's absent?
   - Are there gaps in any central system, relationship, technology,
     profession, law, magic, institution, or social rule that would block
     a specific plot scene? What happens during the climax -- what rule,
     cost, relationship, or prior setup resolves it?
   - Are there characters needed for the plot who don't exist?
   - Are there scenes the outline demands that the world can't support?
3. Check for CONVENIENT GAPS vs DELIBERATE MYSTERY:
   - Convenient: "the details are unclear" where specifics are needed
   - Deliberate: withholding information from the READER while the
     AUTHOR knows the answer. If the planning docs dodge a question
     that a writer would need answered to draft a scene, that's a gap,
     not an iceberg.
4. Check the canon for INTERNAL CONTRADICTIONS:
   - Cross-reference dates, ages, and timelines
   - Check if character abilities, permissions, knowledge, tools, or choices
     match the established world and canon rules
   - Look for factual conflicts between documents

Score these dimensions (gap + improvement required for each):

LORE & WORLDBUILDING:
- magic_system: This dimension covers any central system in the book:
  magic, technology, law, profession, crime, religion, economics, social
  codes, institutions, or other governing logic. Are there hard rules with
  COSTS and LIMITATIONS? Could a writer resolve the CLIMACTIC CONFLICT using
  only rules already established? Are costs plot-driving, not decorative?
  Are there at least 3 societal implications explored with specificity?
  Is the system TESTABLE -- could you write key scenes without inventing
  new rules?
- world_history: Timeline of events creating PRESENT-DAY tensions.
  Each historical event should map to a current faction conflict or
  character motivation. Decorative history (cool but plot-irrelevant)
  counts against the score, not for it.
- geography_and_culture: Locations distinct with sensory signatures.
  Cultures with specific customs that GENERATE CONFLICT. Economy that
  creates class tension. Check: could two different scenes set in two
  different locations feel meaningfully different based on what's here?
- lore_interconnection: Does changing one element force changes in
  at least two others? Test by mentally removing the central system,
  institution, technology, relationship, or governing constraint -- does
  the political structure, class system, plot, or character motivation
  change? If elements are modular/detachable, score low.
- iceberg_depth: Implied depth vs stated depth. But CHECK: does the
  author actually know the answers to the mysteries, or are they
  handwaving? If a planning doc says "the answer will be revealed"
  without specifying WHAT the answer is, that's a gap wearing an
  iceberg costume.

CHARACTER:
- character_depth: Wound/want/need/lie chains that are CAUSALLY LINKED
  (not just thematically associated). The lie must logically follow
  from the wound. The want must be the wrong solution to the lie.
  The need must directly oppose the want. Check each chain for
  logical gaps. Also check: are ANY characters missing wound/want/need
  chains who probably need them?
- character_distinctiveness: Remove all dialogue tags from the example
  lines. Can you identify the speaker from sentence structure alone?
  Check for REPEATED STRUCTURAL FORMULAS across characters (e.g.,
  multiple characters using "X. Not Y." or balanced antithesis).
  Check that metaphor domains don't overlap. Check that speech
  patterns reflect character background, age, education, class, profession,
  region, confidence, and emotional pressure.
- character_secrets: Each major character's secret should be something
  that, if revealed, changes the plot's trajectory. Vague secrets
  ("he knows more than he says") score lower than specific ones
  ("he knows the harmonic means X, which would invalidate Y").

STRUCTURE:
- outline_completeness: Chapters with beats, POV, emotional arc,
  try-fail cycle type. Save the Cat beats at correct % marks.
  Score 0 if empty. Score 5+ only if act structure exists.
- foreshadowing_balance: Every planted thread has a planned payoff.
  Score 0 if ledger is empty regardless of implicit threads in
  other documents -- foreshadowing must be TRACKED to count.

CRAFT:
- internal_consistency: Actively hunt for contradictions. Cross-ref
  dates, ages, character counts, named locations. Flag any case
  where documents disagree. A single major contradiction caps this
  at 6. Three or more caps at 4.
- voice_clarity: Voice definition must be specific and ACTIONABLE.
  Exemplar passages must demonstrate the voice. Anti-exemplars must
  define boundaries. Check exemplar dialogue for AI slop patterns.
  A voice doc that is beautiful but contains slop in its own examples
  is undermined -- deduct.
- canon_coverage: Facts logged, sourced, and sufficient to catch
  contradictions. Check: if a writer introduced a NEW fact in
  chapter 5, could they verify it against the canon? Is the canon
  granular enough? Are there known facts from other docs that
  AREN'T in the canon?

Respond with JSON:
{{
  "magic_system": {{"score": N, "gap": "biggest weakness", "fix": "specific improvement", "note": "..."}},
  "world_history": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "geography_and_culture": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "lore_interconnection": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "iceberg_depth": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "character_depth": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "character_distinctiveness": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "character_secrets": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "outline_completeness": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "foreshadowing_balance": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "internal_consistency": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "voice_clarity": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "canon_coverage": {{"score": N, "gap": "...", "fix": "...", "note": "..."}},
  "slop_in_planning_docs": {{"found": ["list any AI slop patterns found in exemplar dialogue, voice examples, or character descriptions"], "note": "..."}},
  "contradictions_found": ["list any factual contradictions between documents"],
  "overall_score": N,
  "lore_score": N,
  "weakest_dimension": "...",
  "top_3_improvements": ["ranked list of the 3 highest-leverage improvements"]
}}

WEIGHTING: lore/worldbuilding 40%, character 30%, structure 20%, craft 10%.
A novel with thin worldbuilding but a complete outline is WORSE than deep
worldbuilding with an incomplete outline.

FINAL CHECK: If your overall_score is above 7, re-read your gap lists.
If any gap describes a problem that would force a writer to stop and
invent something during drafting, your score is too high. Revise down.
"""


CHAPTER_PROMPT = """Evaluate this book chapter against the planning docs.

SCORING CALIBRATION:
  9-10: Among the best chapters you've read in published fiction. Name
        a specific published chapter it competes with, or don't give 9+.
  7-8:  Strong, publishable with editorial polish. Specific flaws exist
        but don't break the reading experience.
  5-6:  Functional but flat. A competent draft that needs substantial revision.
        Generic where it should be specific. Safe where it should risk.
  3-4:  Significant problems. Voice breaks, beats missed, prose generic.
  1-2:  Not usable. Rewrite from scratch.

  The MEDIAN score for a competent AI-generated chapter should be 6.
  A 7 means it does something a generic AI draft wouldn't.
  An 8 means a human editor would keep it with minor notes.
  Most dimensions should score 6-7. Reserve 8+ for genuine excellence.

MANDATORY: For each dimension, you must identify:
  (a) The single WEAKEST MOMENT -- quote the specific sentence or passage
  (b) What would make it better -- a concrete revision, not a vague note
  If every sentence is perfect, you're not reading carefully enough.

VOICE DEFINITION:
{voice}

WORLD BIBLE (summary):
{world}

CHARACTER REGISTRY:
{characters}

CANON (established hard facts -- violations are bugs):
{canon}

CHAPTER OUTLINE ENTRY:
{chapter_outline}

PREVIOUS CHAPTER (last 1500 words):
{prev_chapter_tail}

THE CHAPTER TO EVALUATE:
{chapter_text}

CROSS-CHECKS (perform before scoring):
1. QUOTE TEST: Find the 3 best sentences and 3 weakest sentences.
   If you can't find 3 weak ones, lower your standards -- every
   chapter has weak moments. Look for: generic phrasing where
   specificity was possible, rhythmic monotony in any paragraph,
   metaphors that don't come from the character's experience,
   emotional moments that tell instead of show, transitions that
   summarize instead of dramatize.
2. DIALOGUE REALISM: Read all dialogue aloud (mentally). Does it
   sound like speech or like written prose? Do characters speak in ways
   that match their established age, background, education, profession,
   status, relationship, and emotional state?
3. SCENE VS SUMMARY: How much of the chapter is in-scene (moment
   by moment, with dialogue and action) vs summary (narrator
   compressing time)? Chapters heavy on summary score lower on
   engagement regardless of prose quality.
4. AI PATTERN CHECK: Look for these common AI writing patterns:
   - Every paragraph the same length
   - Observations always in threes (X, Y, and Z)
   - Emotional beats that arrive on schedule rather than surprising
   - Characters who never say the wrong thing or talk past each other
   - Description that catalogs instead of selecting (listing 5 sensory
     details when 2 specific ones would be sharper)
   - Internal monologue explaining what the scene already showed
5. EARNED VS GIVEN: Is tension earned through scene work or handed to
   the reader through the narrator's assertions? Is mystery maintained
   through genuine withholding or through the character conveniently
   not thinking about things they'd think about?
6. WORLD, TECH, MAGIC, LAW, AND SOCIAL SYSTEM RULES: Check all character
   abilities, access, knowledge, permissions, tools, social constraints,
   injuries, relationships, technologies, and supernatural elements against
   the planning documents. Any plot point that gives a character an
   unearned capability or violates an established limitation is a MAJOR
   canon violation.

Score these dimensions:

- voice_adherence: Does the prose match voice.md Part 2? Check: sentence
  rhythm variation, vocabulary wells, body-before-emotion principle,
  the specific tone described. Quote the strongest voice moment AND
  the weakest. Does ANY passage sound like generic genre prose that
  could appear in any book with names swapped? If yes, score 7 max.

- beat_coverage: Did it hit every beat from the outline? Were beats
  dramatized or merely mentioned? A beat that's summarized in a sentence
  instead of lived in a scene counts as half-hit. Score reflects
  QUALITY of beat execution, not just presence.

- character_voice: Remove all dialogue tags mentally. Can you tell who's
  speaking? Do characters ever sound alike? Does dialogue read as speech
  or as written prose? Do characters sound like specific people with their
  established age, background, training, status, and current pressure, or
  like generic role labels? Does anyone say something surprising -- not just
  the right thing, but a REAL thing? Characters who never stumble, hesitate,
  or say something slightly wrong are AI-pattern characters.

- plants_seeded: Were foreshadowing elements placed naturally? A plant
  that's obvious is worse than a plant that's invisible. Score based on
  HOW WELL they're integrated, not just whether they're present.

- prose_quality: Sentence variety (measure: do 3+ consecutive sentences
  start the same way?). Specificity (concrete nouns > abstract).
  Metaphors should come from the viewpoint character's lived experience,
  profession, body, culture, setting, and current pressure, not from a
  thesaurus. Show-don't-tell at emotional peaks. QUOTE the weakest sentence
  and explain why. Also check for: repeated phrases, leaned-on constructions,
  paragraphs that could be cut without loss.

- continuity: Does it follow logically from the previous chapter? Emotional
  continuity as well as plot continuity. Does the character's state of
  mind track?

- canon_compliance: Check ALL facts against canon. List violations.
  One major violation caps score at 6. Check: character names, locations,
  central system rules, timeline, established events, physical descriptions.

- lore_integration: Does the world do WORK in this chapter, or is it
  set dressing? A scene that could happen in any generic setting with
  find-and-replace on proper nouns scores 5 max.

- engagement: Would a reader turn the page? Where does tension come from --
  plot, character, mystery, prose? Is there a moment that SURPRISES?
  Predictable excellence is still predictable. Score 8+ only if the
  chapter does something unexpected.

Respond with JSON:
{{
  "voice_adherence": {{"score": N, "weakest_moment": "quote the specific weak passage", "fix": "how to improve it", "note": "..."}},
  "beat_coverage": {{"score": N, "weakest_moment": "...", "fix": "...", "note": "..."}},
  "character_voice": {{"score": N, "weakest_moment": "...", "fix": "...", "note": "..."}},
  "plants_seeded": {{"score": N, "weakest_moment": "...", "fix": "...", "note": "..."}},
  "prose_quality": {{"score": N, "weakest_sentence": "quote it", "fix": "rewrite suggestion", "strongest_sentence": "quote it", "note": "..."}},
  "continuity": {{"score": N, "note": "..."}},
  "canon_compliance": {{"score": N, "violations": ["list any found"], "note": "..."}},
  "lore_integration": {{"score": N, "weakest_moment": "...", "fix": "...", "note": "..."}},
  "engagement": {{"score": N, "weakest_moment": "...", "fix": "...", "note": "..."}},
  "three_weakest_sentences": ["quote 1", "quote 2", "quote 3"],
  "three_strongest_sentences": ["quote 1", "quote 2", "quote 3"],
  "ai_patterns_detected": ["list any AI writing patterns found"],
  "overall_score": N,
  "weakest_dimension": "...",
  "top_3_revisions": ["specific, actionable revision 1", "revision 2", "revision 3"],
  "new_canon_entries": ["any new facts established in this chapter"]
}}

FINAL CHECK: If your overall_score is above 7, re-read your weakest_moment
quotes. If any of them describe a problem that an editor would flag, your
score is too high. The median AI chapter is a 6. An 8 is exceptional. A 9
is rare. A 10 does not exist for a first draft.
"""

CHAPTER_PROMPT_REDUCED = """Evaluate this book chapter.

SCORING CALIBRATION:
  9-10: Published quality.
  7-8:  Strong, minor polish needed.
  5-6:  Functional but flat. Median score is 6.
  3-4:  Significant problems.
  1-2:  Rewrite from scratch.

VOICE DEFINITION (reduced):
{voice}

WORLD BIBLE (reduced):
{world}

CHARACTER REGISTRY (reduced):
{characters}

CANON (reduced):
{canon}

CHAPTER OUTLINE ENTRY:
{chapter_outline}

PREVIOUS CHAPTER (reduced):
{prev_chapter_tail}

THE CHAPTER TO EVALUATE:
{chapter_text}

Score these dimensions:
- voice_adherence: Style matching.
- beat_coverage: All beats hit.
- character_voice: Distinct dialogue.
- plants_seeded: Natural plants.
- prose_quality: Sentence variety, no AI patterns.
- continuity: Flow.
- canon_compliance: Violations.
- lore_integration: World importance.
- engagement: Tension.

Respond with JSON:
{{
  "voice_adherence": {{"score": N, "weakest_moment": "quote", "fix": "suggestion", "note": ""}},
  "beat_coverage": {{"score": N, "weakest_moment": "", "fix": "", "note": ""}},
  "character_voice": {{"score": N, "weakest_moment": "", "fix": "", "note": ""}},
  "plants_seeded": {{"score": N, "weakest_moment": "", "fix": "", "note": ""}},
  "prose_quality": {{"score": N, "weakest_sentence": "quote", "fix": "suggestion", "strongest_sentence": "", "note": ""}},
  "continuity": {{"score": N, "note": ""}},
  "canon_compliance": {{"score": N, "violations": [], "note": ""}},
  "lore_integration": {{"score": N, "weakest_moment": "", "fix": "", "note": ""}},
  "engagement": {{"score": N, "weakest_moment": "", "fix": "", "note": ""}},
  "three_weakest_sentences": [],
  "three_strongest_sentences": [],
  "ai_patterns_detected": [],
  "overall_score": N,
  "weakest_dimension": "prose_quality",
  "top_3_revisions": ["revision 1", "revision 2", "revision 3"],
  "new_canon_entries": []
}}
"""

CHAPTER_PROMPT_MINIMAL = """Evaluate this book chapter under these minimal instructions.

CHAPTER OUTLINE ENTRY:
{chapter_outline}

THE CHAPTER TO EVALUATE:
{chapter_text}

Analyze only outline beat coverage and prose quality.
Respond with JSON containing the overall score and 3 key revisions:
{{
  "overall_score": N,
  "top_3_revisions": ["revision 1", "revision 2", "revision 3"],
  "weakest_moment": "...",
  "canon_compliance": {{"score": N, "violations": []}},
  "prose_quality": {{"score": N, "fix": "", "weakest_sentence": ""}}
}}
"""


FULL_NOVEL_PROMPT = """Evaluate this complete book holistically.
You have the planning docs and ALL chapter summaries with their individual scores.

VOICE DEFINITION:
{voice}

WORLD BIBLE:
{world_summary}

CHARACTER REGISTRY:
{characters}

OUTLINE + FORESHADOWING LEDGER:
{outline}

CHAPTER SUMMARIES AND SCORES:
{chapter_summaries}

Score these novel-level dimensions 0-10:
- arc_completion: Do character arcs resolve satisfyingly?
- pacing_curve: Does tension build properly across the book?
- theme_coherence: Are themes explored consistently?
- foreshadowing_resolution: Are all planted threads harvested?
- world_consistency: Any lore contradictions across chapters?
- voice_consistency: Is the voice steady throughout?
- overall_engagement: Is this a compelling read start to finish?

Respond with JSON:
{{
  "arc_completion": {{"score": N, "note": "..."}},
  "pacing_curve": {{"score": N, "note": "..."}},
  "theme_coherence": {{"score": N, "note": "..."}},
  "foreshadowing_resolution": {{"score": N, "note": "..."}},
  "world_consistency": {{"score": N, "note": "..."}},
  "voice_consistency": {{"score": N, "note": "..."}},
  "overall_engagement": {{"score": N, "note": "..."}},
  "novel_score": N,
  "weakest_dimension": "...",
  "weakest_chapter": N,
  "top_suggestion": "..."
}}
"""

