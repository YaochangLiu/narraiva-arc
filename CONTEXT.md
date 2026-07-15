# Arc Story Generation

The language of turning a creator's unstructured intent into a durable contract that Arc Engine can consume.

## Language

**Creative Input**:
The creator's original sentence or free-form text, preserved as private task data.
_Avoid_: Prompt, query

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
