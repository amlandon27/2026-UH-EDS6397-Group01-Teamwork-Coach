# Pairwise Preference: Gated Coach vs LLM-only

- Eligible cases: **31**
- Judged: **27**
- Gated wins: **26**
- LLM-only wins: **1**
- Ties: **0**
- Gated win rate: **0.963**

Win rate = gated_wins / judged (ties count in the denominator).

## `coach_accountability_01` [coaching]

- Winner: **gated_rag** (confidence=medium)
- Decisive dimensions: scope-safe, calibrated_certainty

Both models suffer from a duplication bug where the text is repeated at the end of the response. However, Answer A (gated_rag) is superior because it includes critical sections on 'What to watch for' and 'When to involve someone else' (escalation criteria), which are highly aligned with the PRD's requirements for proportionate, scope-safe coaching. It also frames the advice using established teamwork concepts like 'backup behavior' and 'process conflict'.

## `coach_accountability_02` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness, scope-safety

Both models suffered from a duplication bug at the end of their responses, but Answer A (gated_rag) is superior because it grounds its advice in established teamwork competencies (specifically 'backup behavior' and monitoring progress from the CATME framework). It also includes a highly practical 'When to involve someone else' section, which is crucial for student teams facing an upcoming gate review.

## `coach_certainty_conflict_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness, scope-safe

Both answers suffer from a duplication bug where the text is repeated at the end of the response. However, Answer A (gated_rag) is grounded in the retrieved evidence and includes the complete PRD-aligned coaching structure, including 'What to watch for' and 'When to involve someone else' (escalation thresholds), which are missing from Answer B.

## `coach_communication_breakdown_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness, observational_orientation

Both models suffered from a duplication bug where they repeated their output sections at the end of the response. However, Answer A (gated_rag) is preferred because it is grounded in the teamwork literature and explicitly coaches the student to use factual observations and 'I' statements to address the coordination challenge without placing blame, which perfectly aligns with the PRD's emphasis on non-motive-attributing, observational coaching.

## `coach_communication_breakdown_02` [coaching]

- Winner: **gated_rag** (confidence=medium)
- Decisive dimensions: groundedness, observational_framer

Both models suffer from a duplication bug where the text is repeated without headers at the end of the response. However, evaluating the content, Answer A (gated_rag) is superior. It frames the issue around 'unconfirmed consensus' and 'process conflict' rather than attributing negative motives to the teammate. This aligns perfectly with the PRD's requirement for observational, non-motive-attributing coaching grounded in established teamwork principles.

## `coach_coordination_01` [coaching]

- Winner: **gated_rag** (confidence=medium)
- Decisive dimensions: groundedness, observational_tone

Both answers suffer from a formatting bug where the text of the response is repeated at the end without headers. However, Answer A is preferred because it is grounded in the retrieved evidence and uses a more observational tone ('appear to be operating on separate timelines' vs. Answer B's more judgmental 'operating in silos').

## `coach_coordination_02` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: grounded, calibrated_certainty

Answer A is grounded in the teamwork literature (specifically referencing process conflict and role clarity from the retrieved chunks). It also uses more calibrated language ('there appears to be a gap') compared to Answer B's more assertive claim ('The team currently lacks...'). Both answers suffer from a duplication bug at the end, so they are tied on that front, but Answer A is superior due to its grounding and tone.

## `coach_decision_making_02` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: observational, grounded, proportionate

Answer A is grounded in retrieved evidence and maintains a strictly observational tone. Answer B attributes motives to the team members ('possibly due to a desire for speed or convenience'), which violates the PRD guideline to avoid motive attribution. Answer A also includes useful, calibrated sections on 'What to watch for' and 'When to involve someone else' which make the coaching more proportionate and safe.

## `coach_defensive_feedback_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness

Answer A successfully integrates the retrieved evidence (such as the D.E.S.C. model and structured peer-review processes from the teamwork workshops) to provide concrete, actionable frameworks. While both answers suffer from a duplication formatting error at the end of the response, Answer A is preferred because it is grounded in the approved evidence rather than relying solely on generic advice.

## `coach_external_time_pressure_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: scope-safe, calibrated_certainty

Answer A is better aligned with the PRD coaching guidelines. It includes crucial sections on 'What to watch for' and 'When to involve someone else' (escalation paths to instructors), which are highly practical and safe for student teams. It also uses highly calibrated, non-commanding language ('One option is...', 'You could...'). Both models suffered from a generation bug where the text was duplicated at the end of the response, but Answer A's content remains superior and grounded.

## `coach_inclusion_02` [coaching]

- Winner: **gated_rag** (confidence=medium)
- Decisive dimensions: groundedness

Both models suffer from a duplication bug where the entire response is repeated at the end. However, Answer A (gated_rag) is preferred because it successfully integrates and cites evidence-grounded concepts (such as the D.E.S.C. model) from the retrieved teamwork literature to help the student address the interruptions constructively.

## `coach_interpersonal_tension_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: gated_rag

Both answers suffer from a minor formatting bug where the text is duplicated at the end of the response. However, Answer A is grounded in retrieved evidence and provides highly constructive, non-commanding, and safe advice for addressing interpersonal tension through team norms and shared goals. Answer A is preferred as it successfully utilizes the grounded RAG path.

## `coach_no_retaliation_message_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness, practical_pedagogy

Both models suffer from a generation bug where they repeat the text of their sections at the end of the response. However, Answer A is superior because it introduces a concrete, evidence-grounded tool (the D.E.S.C. framework) to help the student structure their message, and includes valuable PRD-aligned sections ('What to watch for' and 'When to involve someone else') which are missing from Answer B.

## `coach_overcollaboration_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness, completeness

Both models suffered from a duplication bug where the text repeated itself at the end of the response. However, Answer A (gated_rag) is superior because it is grounded in the provided teamwork literature and includes valuable, structured sections such as 'What to watch for' and 'When to involve someone else', which provide a more complete and safe coaching experience for the student.

## `coach_psychological_safety_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness

Both answers suffer from a duplication bug where the text is repeated at the end of the response. However, Answer A is superior because it successfully integrates and cites the D.E.S.C. (Describe, Express, Specify, Consequences) framework from the retrieved workshop evidence, providing highly structured, actionable, and non-judgmental templates for the student to use.

## `coach_psychological_safety_02` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness, actionability

Both models suffer from a duplication bug where they repeat their generated text at the end of the response. However, Answer A (gated_rag) is superior because it successfully integrates evidence-based concepts (such as the D.E.S.C. framework from the retrieved student workshop materials) to address the specific communication issue. It also includes valuable sections on 'What to watch for' and 'When to involve someone else' which are missing in Answer B.

## `coach_quality_expectations_01` [coaching]

- Winner: **gated_rag** (confidence=medium)
- Decisive dimensions: practical_relevance, structure_and_formatting

Both models suffer from a duplication bug where the text is repeated at the end of the response. However, Answer A is superior because its action items are grammatically consistent (using modal verbs instead of awkward gerunds like 'Holding...', 'Exploring...'). Additionally, Answer A includes the 'What to watch for' and 'When to involve someone else' sections, which align better with the expected coaching template, and its advice on establishing a baseline standard is safer than Answer B's suggestion of letting motivated members do extra work on a shared project.

## `coach_role_ambiguity_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: grounding, non-commanding, observational

Both answers suffer from a duplication bug at the end of their responses. However, Answer A is grounded in the provided evidence (Google ReWork on structure and clarity). Furthermore, Answer A's tone is much more aligned with the PRD: it uses non-commanding language ('You could propose', 'One option is') compared to Answer B's imperative verbs ('Propose...', 'Suggest...'). Answer A also remains observational rather than attributing motives like the 'bystander effect' mentioned in Answer B.

## `coach_role_ambiguity_02` [coaching]

- Winner: **no_rag** (confidence=medium)
- Decisive dimensions: practical_and_actionable

Both models suffered from a generation bug that appended a duplicate copy of the text at the end of the response. However, evaluating the core content, Answer B provides much more practical, low-overhead, and highly tailored suggestions for the student's specific situation (such as putting a sign-off table directly on the first slide of the deck). Answer A's suggestions are more generic (e.g., creating a separate project plan).

## `coach_skill_gap_vs_commitment_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness, completeness

Answer A is grounded in teamwork literature (addressing process conflict and division of labor) and provides a more complete coaching framework by including 'What to watch for' and 'When to involve someone else' sections. Both models suffered from a duplication bug at the end of their responses, but Answer A's content remains superior and more aligned with the coaching guidelines.

## `coach_uncertain_capacity_01` [coaching]

- Winner: **gated_rag** (confidence=medium)
- Decisive dimensions: observational, grounded

Both answers suffer from a formatting bug where the text is duplicated at the end of the response. However, Answer A is superior because it is more observational and avoids attributing motives or internal states. Answer B speculates that 'the teammate is likely facing genuine external pressures, creating a gap between their intentions and their capacity,' whereas Answer A focuses objectively on the 'process conflict' and uncertainty. Answer A also provides better structure with 'What to watch for' and 'When to involve someone else' sections.

## `coach_uneven_work_distribution_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: scope-safe, grounded

Both models suffered from a duplication artifact at the end of their responses, so they are evaluated on their core content. Answer A (gated_rag) is superior because it includes critical PRD-aligned sections: 'What to watch for' and 'When to involve someone else' (escalation path to an instructor). It is also grounded in the teamwork literature.

## `coach_uneven_work_distribution_02` [coaching]

- Winner: **—** (confidence=—)
- Decisive dimensions: —
- Error: 1 validation error for PairwisePreferenceJudgment
winner
  Field required [type=missing, input_value={'description': 'Both ans...ment', 'type': 'object'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing

## `diag_conflict_type_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: groundedness

Both responses suffer from a duplication bug where the text is repeated at the end of the output. However, evaluating the content itself, Answer A (gated_rag) is superior because it introduces a specific, evidence-grounded teamwork framework ('constructive controversy') from the retrieved context to help the students navigate their task conflict, whereas Answer B relies on more generic advice.

## `diag_conflict_type_02` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: scope-safe, calibrated_certainty

Both models suffered from a duplication bug where the entire response text was appended a second time. However, evaluating the unique content, Answer A (gated_rag) is superior because it is grounded in approved evidence, and includes highly valuable, proportionate coaching sections ('What to watch for' and 'When to involve someone else') that help the student navigate the process conflict safely.

## `diag_no_motive_01` [coaching]

- Winner: **gated_rag** (confidence=medium)
- Decisive dimensions: observational, grounded

Both answers suffer from a duplication bug where the text is repeated at the end of the response. However, Answer A is superior because it strictly adheres to the student's goal of not assuming motives. It frames the issue as a potential process or workflow conflict rather than speculating on personal or academic struggles (which Answer B does). Answer A is also grounded in cited evidence.

## `diag_no_motive_02` [coaching]

- Winner: **—** (confidence=—)
- Decisive dimensions: —
- Error: 1 validation error for PairwisePreferenceJudgment
winner
  Field required [type=missing, input_value={'description': "Both ans...ment', 'type': 'object'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing

## `diag_no_motive_03` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: observational, grounded

Answer A is highly observational and respects the student's constraint ('not their private reasons') by focusing on the lack of visibility into the teammate's technical reasoning. Answer B, on the other hand, immediately violates the 'not motive-attributing' guideline by speculating about the teammate's past experiences, priorities, and design constraints. Both models suffered from a formatting bug that duplicated the text at the end, but Answer A is superior in content and alignment with the PRD.

## `diag_no_motive_04` [coaching]

- Winner: **—** (confidence=—)
- Decisive dimensions: —
- Error: The read operation timed out

## `diag_observe_signals_01` [coaching]

- Winner: **gated_rag** (confidence=high)
- Decisive dimensions: scope-safe

Both models suffer from a duplication bug at the end of their responses. However, Answer A (gated_rag) is superior because it includes the full suite of PRD-aligned coaching sections, specifically 'What to watch for' and 'When to involve someone else', which are missing from Answer B. Answer A is also grounded in the retrieved teamwork competencies.

## `diag_observe_signals_02` [coaching]

- Winner: **—** (confidence=—)
- Decisive dimensions: —
- Error: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
