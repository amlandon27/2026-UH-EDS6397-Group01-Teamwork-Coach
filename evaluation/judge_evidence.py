"""Approved evidence base for LLM-as-judge ``evidence_to_action`` scoring.

Both gated_rag and no_rag coaching answers are judged for conceptual alignment
with these sources — not capped by whether product-path chunk IDs were cited.
"""

from __future__ import annotations

# Injected into absolute + pairwise judge prompts.
JUDGE_EVIDENCE_BASE = """
## Approved evidence base (judge against this for evidence_to_action)

Score whether the coach advice is consistent with concepts, practices, and
frameworks from these sources. Explicit URLs/titles in the student-facing text
are NOT required. Fabricated or contradictory "research claims" still score low.
Product-path retrieved/cited chunk IDs are optional context only — do not
require them for high scores, and do not cap no_rag below gated_rag solely
because it lacks chunk IDs.

### Diagnostic and behavioral frameworks
- CATME five dimensions — https://info.catme.org/features/catme-five-dimensions/
  (Contributing to the Team’s Work; Interacting with Teammates; Keeping the Team
  on Track; Expecting Quality; Having Relevant Knowledge, Skills, and Abilities)
- CATME YouTube — Contributing to the Team’s Work
  https://www.youtube.com/watch?v=vZuvy6gnu2M&list=PLwyQhAxENQwvTfrfYu8jy5DUbAR6Obj9K&index=2
- CATME YouTube — Interacting with Teammates
  https://www.youtube.com/watch?v=FgS_-tEiKA0&list=PLwyQhAxENQwvTfrfYu8jy5DUbAR6Obj9K&index=3
- CATME YouTube — Keeping the Team on Track
  https://www.youtube.com/watch?v=Kg94gvxcTbw&list=PLwyQhAxENQwvTfrfYu8jy5DUbAR6Obj9K&index=4
- CATME YouTube — Expecting Quality
  https://www.youtube.com/watch?v=4NdMW4VoH94&list=PLwyQhAxENQwvTfrfYu8jy5DUbAR6Obj9K&index=5
- CATME YouTube — Having Relevant Knowledge, Skills, and Abilities
  https://www.youtube.com/watch?v=8HOXtBh-FYs&list=PLwyQhAxENQwvTfrfYu8jy5DUbAR6Obj9K&index=6
- ABET teamwork rubric (Marquette ECE) — focus on Meets / Exceeds criteria
  https://www.marquette.edu/electrical-computer-engineering/documents/abet-5.pdf
- Google re:Work — Understand team effectiveness
  https://rework.withgoogle.com/intl/en/guides/understand-team-effectiveness

### Conflict, coordination, and decision making
- HBS Online — Leadership communication
  https://online.hbs.edu/blog/post/leadership-communication
- ASEE — Constructive controversy: optimizing decision making in engineering design teams
  https://peer.asee.org/constructive-controversy-optimizing-decision-making-in-engineering-design-teams
- ASEE — Effect of different dimensions of conflict on team member effectiveness
  https://peer.asee.org/the-effect-of-different-dimensions-of-conflict-on-measures-of-team-member-effectiveness
- ASEE — Two student workshops on identifying and resolving teamwork conflict
  https://peer.asee.org/two-student-workshops-on-identifying-and-resolving-teamwork-conflict
- ASEE — Workshop: conflict management for undergraduate engineering students
  https://peer.asee.org/workshop-conflict-management-for-undergraduate-engineering-students
- PMC — Team conflict / effectiveness open-access article
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7654846/
- HBR IdeaCast transcript — The right way to collaborate
  https://hbr.org/podcast/2010/03/the-right-way-to-collaborate-i

### Psychological safety and team climate
- Psychological safety reference notes (shared doc)
  https://docs.google.com/document/d/1BISFyuPdalAsWP7oc03wIY4HviZggylXmoZFFjNhock/edit?tab=t.0
- PMC open-access — psychological safety / team climate
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7011517/
- PMC open-access — related team climate / safety article
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8827773/
- HBS Online — Emotional intelligence skills
  https://online.hbs.edu/blog/post/emotional-intelligence-skills
- BPS Psychologist — Welcoming dissent / thoughtful response to failure
  https://www.bps.org.uk/psychologist/well-placed-question-thoughtful-response-failure-welcoming-dissent-can-change-game

### Teamwork interventions
- PMC open-access — teamwork intervention evidence
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8327544/
- Frontiers in Education — teamwork intervention article (2025)
  https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2025.1637203/full
- Frontiers in Education — teamwork intervention article (2026)
  https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1840604/full
""".strip()
