# Arc Story Generation

The language of turning a creator's unstructured intent into a durable contract that Arc Engine can consume.

## Language

**Creative Input**:
The creator's original sentence or free-form text, preserved as private task data.
_Avoid_: Prompt, query

**Creative Input Mode**:
The contract signal that classifies Creative Input as automatic, a direct premise, or free-form material.
_Avoid_: Prompt type, parser mode

**Story Brief**:
A versioned, structured statement of story intent that Arc Engine can generate from.
_Avoid_: Form, generation config, prompt

**Brief Field**:
One story-intent value paired with its provenance.
_Avoid_: Parameter, setting

**Field Source**:
The provenance of a Brief Field: explicit, inferred, or default.
_Avoid_: Confidence, origin type

**Explicit Constraint**:
A structured value deliberately supplied by the creator; it cannot be replaced by inference or defaults.
_Avoid_: Hard prompt, manual field

**Inference Result**:
Structured candidate values derived from Creative Input by an interpreter.
_Avoid_: User choice, explicit value

**System Understanding**:
A privacy-safe view of the Story Brief and each Field Source that a creator may review before generation.
_Avoid_: Raw prompt dump, debug view

**Arc Engine**:
The portable deep module that turns a Generation Request into a Story Artifact through a fixed stage sequence.
_Avoid_: Pipeline orchestrator, Web runner

**Generation Request**:
The versioned Arc Engine input containing a Story Brief and an optional supported pause point.
_Avoid_: Job payload, config dictionary

**Engine Stage**:
A durable statement that one generation step has completed: intake, planned, drafted, refined,
validated, or exported.
_Avoid_: Current handler, progress string

**Stage Event**:
A transport-neutral, versioned observation returned by Arc Engine when an Engine Stage completes.
_Avoid_: WebSocket message, log line

**Engine Checkpoint**:
Private task data that records the last completed Engine Stage and the state required to continue
strictly after it.
_Avoid_: Snapshot of internal objects, resume phase

**Story Artifact**:
The versioned, portable output produced only after the Safety Gate passes.
_Avoid_: Export file, response blob

**Safety Gate**:
The mandatory seam that can prevent refined story text from becoming a Story Artifact.
_Avoid_: Warning flag, optional review

**Story Provider**:
The internal model seam used by Arc Engine for planning, drafting, and refinement.
_Avoid_: Private LLM field, model client singleton
