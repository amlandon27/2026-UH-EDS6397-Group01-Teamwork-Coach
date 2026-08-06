# AI-Powered Teamwork & Leadership Coach for Engineering Education

**Status:** In Development  
**Course:** EDS 6397 – Generative AI Final Project  
**Institution:** University of Houston  
**Document Type:** Product Requirements Document / README

---

## 1. Product Overview

This project will create an AI-powered teamwork and leadership coach for engineering students.

Students will describe a teamwork challenge, and the system will:

1. Remove personally identifiable information.
2. Identify likely teamwork challenges.
3. Retrieve relevant evidence from an approved knowledge base.
4. Generate practical, evidence-grounded coaching.
5. Validate the response for safety, scope, evidence, and citations.
6. Display the response, abstain, or route the student to human support.

The system will use:

- Retrieval-Augmented Generation
- LangGraph-based workflow orchestration
- Structured model outputs
- Programmatic privacy and safety guardrails
- Research-grounded recommendations
- Deterministic routing and fallback behavior

The product is intended to support student reflection and skill development. It does not replace instructors, advisors, counselors, university officials, emergency services, or formal reporting processes.

---

## 2. Problem Statement

Engineering students commonly experience:

- Communication breakdowns
- Uneven work distribution
- Missed commitments
- Role ambiguity
- Poor coordination
- Unresolved conflict
- Difficulty making decisions
- Low psychological safety
- Unequal participation
- Difficulty giving or receiving feedback

Generic AI systems may respond with unsupported, overly confident, harmful, or privacy-invasive advice.

This product must therefore combine useful coaching with:

- Structured diagnosis
- Evidence retrieval
- Citation traceability
- Privacy protection
- Safety validation
- Escalation logic
- Safe fallback behavior

---

## 3. Product Goals

The system should:

1. Help students describe teamwork and leadership concerns.
2. Separate observable behavior from assumptions.
3. Identify primary and secondary teamwork challenges.
4. Retrieve relevant, publicly verifiable evidence.
5. Produce practical and proportionate recommendations.
6. Encourage action without commanding the student.
7. Cite the evidence supporting substantive recommendations.
8. Avoid unsupported diagnoses, accusations, and motive claims.
9. Protect PII throughout the workflow.
10. Stop ordinary coaching when a situation requires human support.
11. Fail safely when evidence or validation is insufficient.
12. Demonstrate a modular, technically credible LangGraph application.

---

## 4. Target Users

### Primary users

Engineering students working in:

- Course projects
- Design teams
- Laboratories
- Research groups
- Capstone teams
- Student organizations
- Engineering competitions

### Initial positioning

The MVP is a student-facing reflection and coaching tool.

It is not:

- An instructor-surveillance system
- A disciplinary system
- A formal team-performance rating system
- An automated misconduct investigator
- A replacement for peer evaluation

---

## 5. Non-Goals

The system will not:

- Diagnose mental-health or personality conditions
- Determine another person’s motives, intentions, or character
- Provide medical, legal, or emergency advice
- Determine whether misconduct occurred
- Conduct investigations
- Contact teammates, instructors, or administrators
- Submit reports or complaints
- Access Canvas, student records, email, calendars, or university systems
- Perform actions on behalf of a user
- Use arbitrary external tools
- Store long-term student profiles in the MVP

The system is advisory only.

---

## 6. MVP Scope

The MVP will demonstrate this end-to-end outcome:

> A student submits a de-identified reflection, the system identifies likely teamwork challenges, retrieves relevant research, generates practical advice, validates it, and either displays it or fails safely.

### Included

- Lightweight Streamlit reflection interface
- Privacy notice
- Basic PII detection and redaction
- Research-derived teamwork taxonomy
- One tagged evidence corpus (hand-built for MVP; replaceable later)
- Local embeddings via `sentence-transformers/all-MiniLM-L6-v2`
- Local ChromaDB vector store
- Ollama `llama3.1:8b` for diagnosis and advice
- Structured diagnosis
- Diagnosis-guided retrieval
- Evidence-grounded advice
- Citation display
- Safety and evidence validation
- High-risk escalation
- Safe fallback
- Synthetic and de-identified evaluation cases
- LangSmith end-to-end nested tracing (optional, sanitized; one trace per coach run)

### Deferred

- Long-term memory
- Persistent profiles
- Instructor dashboards
- Live institutional integrations
- Multi-institution deployment
- Advanced indirect-identifier detection
- Production authentication
- Large-scale multi-tenant observability beyond LangSmith
- Automatic sentence-level citation entailment
- Full document-ingestion pipeline replacing the hand-built corpus

---

## 7. User Workflow

```text
Student Reflection
        │
        ▼
PII Detection and Redaction
        │
        ▼
Diagnosis + Evidence Retrieval
        │
        ├── Insufficient evidence ──► Safe Fallback
        │
        ▼
Advice Generation
        │
        ▼
Validation
        │
        ├── Valid ──────────────────► Final Response
        ├── Repairable ─────────────► One Repair Attempt
        ├── Unsafe/unsupported ─────► Safe Fallback
        └── High-risk ──────────────► Escalation Resources

```

Diagnosis and retrieval remain conceptually separate but will be implemented in one LangGraph node for the MVP.

The MVP uses a one-shot interaction model: one student reflection produces one
validated response. It does not provide a user-facing conversation loop or retain
cross-session memory. The single repair attempt is an internal validation step,
not an additional conversation round.

---

## 8. Knowledge Base Design

### 8.1 One tagged evidence corpus

The system will use one evidence corpus containing:

- Open-access research
- Publicly verifiable professional guidance
- Engineering teamwork frameworks
- Behavioral rubrics
- Approved summaries and excerpts
- Citation and licensing metadata

**MVP approach:** Start with a small hand-built set of human-reviewed, tagged chunks so the end-to-end workflow can ship quickly. The corpus format and metadata contract should allow later replacement with a fuller ingestion pipeline without redesigning diagnosis, retrieval, or citation handling.

The taxonomy is not a separate evidence base. It is a controlled vocabulary used to organize evidence, guide diagnosis, improve retrieval, and support evaluation.

### 8.2 Knowledge domains

The corpus will cover five domains:

1. **Diagnostic and Behavioral Frameworks**
  - Contribution
  - Accountability
  - Reliability
  - Role clarity
  - Shared understanding
  - Team-member effectiveness
2. **Psychological Safety and Communication Climate**
  - Speaking up
  - Listening
  - Feedback
  - Asking for help
  - Responding to mistakes
  - Emotional regulation
  - Respectful disagreement
3. **Conflict, Coordination, and Decision-Making**
  - Task conflict
  - Process conflict
  - Interpersonal conflict
  - Certainty conflict
  - Miscommunication
  - Commitment differences
  - Uneven work distribution
  - Delegation
  - Decision processes
  - Time pressure
4. **Teamwork Interventions and Practical Tools**
  - Team charters
  - Team norms
  - Role clarification
  - Task ownership
  - Progress checkpoints
  - Shared notebooks
  - Shared file systems
  - Peer feedback
  - Team reflection
5. **Inclusion and Equitable Participation**
  - Unequal voice
  - Belonging
  - Idea dismissal
  - Exclusion
  - Bias
  - Skill and confidence differences
  - Inclusive participation practices

The uploaded engineering-team study supports treating conflict type and conflict source as separate diagnostic dimensions. It identifies accountability, commitment, miscommunication, time pressure, and uneven work distribution as common conflict sources, while distinguishing task, interpersonal, process, and certainty conflict.

---

## 9. Taxonomy and Tagging

### 9.1 Controlled vocabularies

The team will define approved values for:

- Challenge tags
- Signal tags
- Conflict types
- Possible conflict sources
- Supported intervention tags
- Evidence roles
- Action levels
- Source types

Example:

```yaml
challenge_tags:
  - accountability
  - communication_breakdown
  - coordination
  - decision_making
  - inclusion
  - psychological_safety
  - role_ambiguity
  - uneven_work_distribution

conflict_types:
  - task_conflict
  - process_conflict
  - interpersonal_conflict
  - certainty_conflict

signal_tags:
  - missed_deadlines
  - unclear_task_ownership
  - uneven_contribution
  - repeated_miscommunication
  - meeting_domination
  - silence_in_meetings
  - idea_dismissal
  - decisions_without_input

supported_intervention_tags:
  - assign_task_ownership
  - clarify_roles
  - clarify_shared_goal
  - create_team_charter
  - establish_checkpoints
  - establish_team_norms
  - invite_team_input
  - use_behavior_specific_feedback

```

### 9.2 Tagging process

Evidence will be tagged at the chunk level.

```text
Define taxonomy
      ↓
Create tagging guide
      ↓
Chunk source
      ↓
LLM suggests tags
      ↓
Human reviews and edits
      ↓
Approved evidence enters corpus

```

The LLM may suggest tags, but a human must approve them.

### 9.3 Support versus mention

The metadata must distinguish between:

```yaml
supported_intervention_tags:
mentioned_intervention_tags:

```

An intervention should be marked as supported only when the chunk provides evidence or implementation guidance for it.

### 9.4 Evidence roles

Allowed roles may include:

- Problem definition
- Observable signals
- Contributing factor
- Intervention support
- Implementation guidance
- Limitation
- Diagnostic caution
- Escalation guidance
- Student-reported strategy

### 9.5 Applicability and limitations

Each chunk should record relevant context and limitations, such as:

- Workplace rather than student-team context
- Qualitative rather than causal evidence
- Does not establish individual motivation
- Requires team participation
- May not apply to very short projects

---

## 10. Evidence and Citation Metadata

Citation details will be stored once at the source level and referenced by evidence chunks.

### 10.1 Source-level metadata

```yaml
source_id:
citation_key:
citation_style:
citation_text:
authors:
publication_year:
source_title:
publication_title:
doi:
url:
date_accessed:
source_type:
access_status:
license:
publicly_verifiable:
full_text_ingestion_allowed:
excerpt_ingestion_allowed:

```

Missing fields must remain blank or `null`. The system must not invent citation information.

### 10.2 Chunk-level metadata

```yaml
chunk_id:
source_id:
text:
challenge_tags:
conflict_types:
possible_conflict_sources:
signal_tags:
supported_intervention_tags:
mentioned_intervention_tags:
evidence_roles:
action_levels:
applicable_contexts:
limitations:
human_reviewed:
tagging_confidence:

```

### 10.3 Citation rules

The system must:

- Cite only retrieved sources.
- Use stored citation metadata.
- Confirm that citations support the recommendation.
- Preserve page or section information when available.
- Provide a DOI or stable URL when available.
- Use one consistent citation style.

**Proposed MVP style:** APA 7.

---

## 11. Source Access and Licensing

The corpus should prioritize sources that users and evaluators can access without institutional credentials.

### Preferred sources

- Open-access research
- Public institutional repositories
- University and government resources
- Open professional guidance
- Public engineering education papers

### Paywalled sources

Paywalled sources may inform discovery but will not be ingested unless an authorized open version is available.

### Public but copyrighted sources

For sources with restrictive or unclear terms, store:

- Citation
- URL
- Tags
- Team-created summary
- Approved short excerpt, when appropriate
- Licensing notes

The repository must not include unauthorized copies of complete articles, webpages, or transcripts.

---

## 12. Retrieval Strategy

Retrieval will use:

- The redacted reflection
- Primary and secondary challenges
- Observable signals
- Conflict type
- Possible conflict sources
- Student goal
- Desired action level

Tags should generally act as ranking boosts rather than hard filters.

The system should retrieve, when available:

- Problem-understanding evidence
- Intervention support
- Implementation guidance
- Relevant limitations

The retrieval result must include an evidence-sufficiency decision.

If evidence is insufficient, conflicting, or irrelevant, the system must abstain.

---

## 13. Diagnosis Requirements

The diagnosis should include:

```yaml
primary_challenge:
secondary_challenges:
conflict_type:
observed_signals:
possible_conflict_sources:
student_goal:
confidence:
uncertainty_notes:

```

The diagnosis must:

- Separate observation from interpretation.
- Treat possible causes as hypotheses.
- Avoid inferring motivation from contribution level.
- Avoid assuming silence means agreement.
- Avoid treating one reflection as a complete account.
- Recognize that uneven contribution may reflect skill, confidence, capacity, access, role clarity, or competing commitments.
- Because the MVP is one-shot (no clarifying-question turn), thin or conflicting
  signal must lower confidence so the system abstains with a safe fallback
  rather than asking follow-up questions.

The uploaded study’s “iceberg” framing reinforces that visible conflict, conflict sources, and underlying issues are not the same and that hidden causes cannot be confidently inferred from brief reflections.

---

## 14. Advice Generation Requirements

Advice must:

- Remain within teamwork and leadership coaching.
- Use only the redacted reflection, diagnosis, and retrieved evidence.
- Provide specific and proportionate options.
- Encourage action without issuing commands.
- Avoid unsupported diagnoses, accusations, and motive claims.
- Avoid overconfidence.
- Avoid PII.
- Include evidence references.
- Avoid external tool calls.

### Recommended response structure

1. **What may be happening**
2. **What you could do next**
3. **How you might say it**
4. **Why this may help**
5. **What to watch for**
6. **When to involve someone else**

---

## 15. Privacy Requirements

The system must detect and redact PII before content reaches:

- LLM prompts
- Embedding requests
- Retrieval queries
- Logs
- Traces
- Evaluation data
- Stored workflow state

Privacy protection applies to students, teammates, instructors, advisors, and others mentioned in a reflection.

Examples include:

- Names
- Email addresses
- Phone numbers
- Student IDs
- Addresses
- Usernames
- Account identifiers

For the MVP:

- Only redacted text is processed downstream.
- Raw reflections are not sent to external telemetry.
- When LangSmith tracing is enabled, telemetry payloads omit `raw_input` and PII-redact other sensitive string fields before upload.
- Logs are sanitized.
- Evaluation cases are synthetic or de-identified.
- User history is not retained beyond the session.

The team must decide whether detected PII results in automatic redaction, confirmation, or resubmission.

---

## 16. Validation Requirements

No recommendation may be displayed until it passes validation.

The validator must check:

- Is the response within teamwork and leadership coaching?
- Is it supported by retrieved evidence?
- Do citations correspond to retrieved sources?
- Does the evidence support the recommendation?
- Does it contain unsupported diagnoses or accusations?
- Does it assign unsupported motives?
- Does it recommend retaliation, humiliation, deception, coercion, manipulation, or unsafe confrontation?
- Does it encourage discrimination or harassment?
- Does it encourage concealment of misconduct or safety concerns?
- Does it overstate certainty?
- Does it contain PII?
- Does it require escalation?
- Is it safe to display?

A response may be displayed only when:

```text
safe_to_display = true

```

---

## 17. High-Risk Escalation

High-risk or out-of-scope situations include:

- Self-harm
- Threats or violence
- Immediate danger
- Stalking
- Sexual harassment
- Discrimination
- Severe bullying or intimidation
- Medical or mental-health concerns
- Legal concerns
- Serious academic misconduct
- Serious university-policy violations
- Situations requiring formal reporting

When detected, the system must:

1. Stop ordinary coaching.
2. Avoid generating a standard recommendation.
3. State that the situation requires human support.
4. Display generic guidance.
5. Display verified University of Houston resources.
6. Direct the student to emergency services when immediate danger may be present.
7. Avoid determining fault or claiming that a violation definitely occurred.

Escalation resources must be stored in configuration, not generated from model memory.

---

## 18. Safe Fallback and Repair

The system may attempt one controlled repair when a response fails for a repairable reason, such as:

- Excessive certainty
- Missing citation
- Weak evidence connection
- PII in the draft
- Incomplete structured output

If the repaired response fails validation, the system must show a safe fallback.

The system must not display:

- Rejected advice
- Partial advice
- Unvalidated advice
- Internal errors

---

## 19. External Tool Restrictions

The system may use:

- Approved LLM APIs
- Approved embedding APIs
- The project-controlled knowledge base
- The project vector store
- Optional LangSmith tracing with sanitized payloads (raw reflections omitted)

The system must not access:

- Email
- Messaging platforms
- Canvas or another LMS
- Student records
- University databases
- Calendars
- Personal accounts
- Shell commands
- Web-search tools
- Reporting or complaint systems

No LLM node should receive an external operational tool registry.

---

## 20. Technology Stack

### Core stack

- Python
- LangGraph
- LangChain Core
- Pydantic v2
- pytest
- python-dotenv
- LangSmith (optional, sanitized nested tracing; configurable via env)

### Selected MVP stack

| Component | Selection |
| --- | --- |
| LLM provider / model | Local Ollama `llama3.1:8b` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| Vector store | ChromaDB (local) |
| Interface | Streamlit |
| Observability | LangSmith (optional; one nested trace per `run_coach` call; sanitized) |
| Evidence corpus (MVP) | Hand-built tagged chunks; replaceable with fuller ingestion later |

### RAG components

- Tagged evidence corpus
- Taxonomy configuration
- Meaning-based chunking
- Embeddings
- Vector store
- Hybrid retrieval
- Citation metadata
- Evidence-sufficiency checks

### Proposed dependencies

```text
langgraph
langchain-core
langchain-ollama
langchain-huggingface
langchain-chroma
sentence-transformers
chromadb
streamlit
pydantic>=2
langsmith
pytest
python-dotenv

```

---

## 21. Shared State Contract

The team must define and freeze a root-level `contract.py`.

Core models should include:

- `ReflectionInput`
- `TeamworkDiagnosis`
- `CitationMetadata`
- `RetrievedEvidence`
- `CoachingRecommendation`
- `ValidationResult`
- `AgentState`

Key state fields should include:

```yaml
raw_input:
redacted_input:
student_goal:
round_number: 1  # Fixed for the one-shot MVP; not a user conversation counter.
regeneration_count:
pii_detected:
diagnosis_payload:
retrieved_evidence:
retrieval_sufficient:
draft_recommendation:
validation_result:
escalation_required:
safe_to_display:
final_response:

```

Contract changes require documented team review and updated tests.

---

## 22. Evaluation

The MVP should measure:

### Privacy

- PII detection and redaction
- PII leakage
- False positives

### Diagnosis

- Reasonable challenge identification
- Observation-versus-interpretation accuracy
- Unsupported-cause inference

### Retrieval

- Relevance
- Intervention-evidence coverage
- Evidence-sufficiency accuracy

### Evidence and citations

- Citation accuracy
- Citation-support rate
- Unsupported-recommendation rate
- Source traceability

### Safety

- Harmful-advice detection
- Unsupported-diagnosis detection
- High-risk routing accuracy
- Unvalidated responses displayed
- Prohibited tool calls

### Actionability

- Specificity
- Feasibility
- Evidence-to-action alignment

### Reliability

- End-to-end completion
- Validation failure
- Repair success
- Fallback activation
- Response latency
- Token use

### Core acceptance criterion

> No recommendation may be displayed unless it passes privacy, evidence, citation, scope, and safety checks.

---

## 23. Testing

The team should create representative tests for:

- PII
- Role ambiguity
- Accountability
- Uneven contribution
- Communication breakdown
- Task, process, interpersonal, and certainty conflict
- Unsupported motive attribution
- Weak or conflicting evidence
- Incorrect or fabricated citations
- Retaliation
- Humiliation
- Deception
- Coercion
- Unsafe confrontation
- Discrimination
- Concealment of misconduct
- Excessive certainty
- High-risk escalation
- Model or retrieval failure
- Unauthorized tool use
- End-to-end safe fallback

Each test should record:

- Input
- Expected route
- Expected output type
- Actual result
- Pass or fail

---

## 24. Repository Structure

```text
/teamwork-leadership-coach/
├── README.md
├── requirements.txt
├── .env.example
├── contract.py
├── main_system.py
│
├── config/
│   ├── settings.py
│   ├── teamwork_taxonomy.yaml
│   ├── safety_policy.py
│   └── escalation_resources.py
│
├── corpus/
│   ├── sources/
│   ├── chunks/
│   ├── metadata/
│   └── tagging_guide.yaml
│
├── ingestion/
│   ├── document_loader.py
│   ├── text_chunker.py
│   ├── tag_suggester.py
│   └── build_index.py
│
├── agents/
│   ├── coordinator.py
│   ├── diagnosis_retrieval_node.py
│   ├── advice_agent.py
│   ├── validation_agent.py
│   ├── escalation_node.py
│   └── fallback_node.py
│
├── guardrails/
│   ├── pii_redaction.py
│   ├── evidence_validation.py
│   ├── citation_validation.py
│   └── harmful_advice_validation.py
│
├── services/
│   ├── llm_service.py
│   ├── embedding_service.py
│   ├── retrieval_service.py
│   └── tracing_service.py
│
├── interface/
│   └── app.py
│
├── evaluation/
├── tests/
└── report/

```

---

## 25. Team Members and Roles

### All Team Members

- Corpus development
- Taxonomy and tagging review
- Integration
- Testing
- Documentation
- Demo preparation

### Francisco

- Advice Generation Agent

### Alex

- Project management
- Model evaluation

### Luija

- Reflection interface
- Workflow design

### Kashfin

- Diagnosis and evidence retrieval
- RAG implementation

### Roberto

- Security
- Data privacy
- System reliability


---

## 26. Expected Outcome

The final prototype should demonstrate:

- A functioning student interface
- Structured diagnosis
- A tagged evidence corpus
- Diagnosis-guided retrieval
- Evidence-grounded, action-oriented coaching
- Traceable citations
- PII protection
- Safety validation
- High-risk escalation
- Safe fallback
- External-tool restrictions
- Quantitative evaluation
- A modular LangGraph workflow
- End-to-end LangSmith observability (optional, sanitized nested traces)

---

## 27. Key Design Decisions for Team Review


| Decision                | Current direction                                                                             | Status   |
| ----------------------- | --------------------------------------------------------------------------------------------- | -------- |
| Product role            | Student-facing reflection and coaching tool                                                   | Selected |
| Knowledge base          | One tagged evidence corpus                                                                    | Selected |
| Taxonomy                | Research-derived controlled vocabulary                                                        | Selected |
| Knowledge domains       | Five domains covering diagnosis, psychological safety, conflict, interventions, and inclusion | Selected |
| Diagnosis and retrieval | Separate logically, combined in one MVP node                                                  | Selected |
| Conflict representation | Separate conflict type from possible source                                                   | Selected |
| Tagging                 | LLM-assisted, human-reviewed, chunk-level                                                     | Selected |
| Intervention metadata   | Distinguish supported from merely mentioned interventions                                     | Selected |
| Citation metadata       | Store at source level and reference from chunks                                               | Selected |
| Citation style          | APA 7                                                                                         | Proposed |
| Source policy           | Prioritize publicly accessible, verifiable sources                                            | Selected |
| Paywalled content       | Do not ingest without an authorized open version                                              | Selected |
| Retrieval               | Semantic search with metadata boosting                                                        | Selected |
| Evidence sufficiency    | Abstain when support is insufficient                                                          | Selected |
| Advice format           | Cautious interpretation plus concrete action                                                  | Selected |
| PII handling            | Redact before downstream processing                                                           | Selected |
| PII user flow           | Automatic redaction before downstream processing; show redacted text in UI                    | Selected |
| Validation              | Required before display                                                                       | Selected |
| High-risk behavior      | Stop coaching and show generic plus UH resources                                              | Selected |
| Internal repair         | At most one controlled internal repair attempt                                                 | Selected |
| External tools          | No operational tools or user actions                                                          | Selected |
| Framework               | Python, LangGraph, LangChain Core, Pydantic                                                   | Selected |
| LLM provider            | Local Ollama `llama3.1:8b`                                                                    | Selected |
| Embedding model         | `sentence-transformers/all-MiniLM-L6-v2` (local via sentence-transformers)                    | Selected |
| Vector store            | ChromaDB (local)                                                                              | Selected |
| Interface               | Streamlit                                                                                     | Selected |
| MVP corpus approach     | Hand-built tagged evidence chunks; replaceable with fuller ingestion later                    | Selected |
| Data retention          | Session-only for the MVP                                                                      | Selected |
| Cross-session memory    | None                                                                                          | Selected |
| Demo inputs             | Synthetic or de-identified                                                                    | Proposed |
| LangSmith               | Optional nested end-to-end tracing; sanitized (raw input omitted); project `teamwork-leadership-coach` | Selected |
| User interaction        | One reflection produces one validated response                                                 | Selected |
| Conversational rounds   | No user-facing conversation loop in the MVP                                                    | Selected |
| Contract                | Root-level frozen `contract.py`                                                               | Selected |


