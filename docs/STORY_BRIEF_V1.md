# Arc Story Brief v1

Arc Story Brief is the versioned boundary between Creative Input interpretation and Arc Engine.
The canonical version identifier is `arc.story-brief/v1`.

## Entry behavior

`interpret_story_brief(raw_input, explicit=..., inferred=...)` accepts:

- no input, producing a complete default brief;
- one sentence, used as an explicit premise when no structured premise is available;
- free-form Creative Input plus an `InferenceResult` represented by `BriefValues`;
- advanced settings represented by explicit `BriefValues`.

Provider adapters may produce inferred `BriefValues`, but the contract does not depend on an LLM,
network, FastAPI, cloud service, or GUI. Interpretation is deterministic once its three inputs are
known.

`input_mode` controls how unstructured input may become a premise:

- `auto` (default): a single-line input of at most 280 characters with at most one run of sentence
  punctuation is a direct explicit premise; other input is free-form material;
- `premise`: non-empty input is deliberately treated as an explicit premise;
- `freeform`: input is retained but never directly promoted to a premise.

Free-form input requires an inferred or explicitly structured premise to avoid the default premise.
This signal lets UI and adapter layers correct the deterministic `auto` classification without
changing the Story Brief schema.

## Fields

Every field is a `{value, source}` pair. `source` is exactly one of `explicit`, `inferred`, or
`default`.

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `premise` | string | `An unexpected choice changes an ordinary life.` | Core story proposition. |
| `genre` | string | `general fiction` | Primary genre lens. |
| `tone` | string | `balanced` | Intended emotional and stylistic tone. |
| `target_length` | `short \| medium \| long` | `short` | Length class, not an exact word guarantee. |
| `protagonist` | string or null | null | Central acting character or group. |
| `setting` | string or null | null | Primary time, place, and social environment. |
| `central_conflict` | string or null | null | Main opposition that sustains the story. |
| `ending_preference` | string | `open` | Desired ending direction, not a fixed final sentence. |
| `must_include` | string array | empty | Creator constraints that must survive generation. |
| `must_avoid` | string array | empty | Creator constraints that output must not contain. |
| `creative_freedom` | number from 0 to 1 | `0.8` | Freedom to fill unspecified story details. |

The original `raw_input` is retained separately as private Creative Input. It is not a Brief Field
and therefore has no Field Source.

## Resolution and conflict rules

For each field, precedence is:

1. `explicit`: a structured creator choice;
2. `inferred`: an interpreter's structured candidate;
3. `default`: the contract fallback.

An explicit value always wins over a different inferred value. The resolution is recorded in
`resolution_notes`; inference is never presented as an explicit creator choice. A direct premise
recognized by Creative Input Mode is explicit and therefore also wins over a different inferred
premise. Free-form text is never promoted to an explicit premise.

Blank structured text, unknown length classes, freedom outside 0–1, and blank constraint entries are
invalid. If normalized `must_include` and `must_avoid` overlap, interpretation fails with
`BriefConflictError`; the engine must not guess which explicit constraint to discard. Ambiguity in
unstructured Creative Input belongs to the interpreter and should be returned as inferred values or
left for defaults.

## Wire contract

`StoryBrief.to_engine_payload()` returns JSON-compatible data:

```json
{
  "schema_version": "arc.story-brief/v1",
  "raw_input": "A lighthouse keeper hears tomorrow's distress calls.",
  "fields": {
    "premise": {"value": "A lighthouse keeper hears tomorrow's distress calls.", "source": "explicit"},
    "genre": {"value": "general fiction", "source": "default"}
  },
  "resolution_notes": []
}
```

The example abbreviates `fields`; the real v1 payload requires all eleven fields exactly.
`StoryBrief.from_engine_payload()` rejects unknown versions, missing or additional fields, invalid
sources, invalid field types, and invalid values. Local and cloud integrations must pass this same
payload rather than create parallel Story Brief shapes. A future incompatible schema uses a new
version identifier and an explicit migration function; v1 meaning must not change in place.

## User experience and privacy

Generation starts automatically by default. A product may show `to_user_view()` and allow
confirmation before starting; confirmation is available but is not a mandatory form step.

- The engine payload contains `raw_input` and must be handled as private task data.
- The user view contains structured fields, Field Sources, and resolution notes, but not the
  original raw-input property.
- Ordinary logs use `to_log_context()`, which contains only schema version, character count,
  SHA-256 digest, and Field Sources.
- Provider adapters must not log raw requests or model responses merely to implement inference.
- Retention, deletion, and access control belong to the hosting product or local caller.

## Worked scenarios

1. **Zero input:** every field uses its default, so generation can still begin.
2. **One sentence:** the sentence is the explicit premise; other fields default.
3. **Messy free text:** the original text is retained privately while an interpreter supplies
   clearly marked inferred fields; absent fields default.
4. **Explicit advanced settings:** explicit values override different inferences and create
   resolution notes.
5. **Contradictory constraints:** the same normalized item in `must_include` and `must_avoid`
   raises a conflict instead of silently choosing.
