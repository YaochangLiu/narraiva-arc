# Architecture baseline

Narraiva Arc is organized around a portable engine rather than a hosted application extracted from
an existing monolith.

```text
Browser / CLI / future clients
            |
     Narraiva Arc product
            |
        Arc Engine
       /          \
provider ports   storage/event ports
       \          /
 optional Narraiva Cloud adapters
```

Arc Engine owns interpretation of creative input, planning, generation orchestration, validation,
transport-neutral Stage Events, checkpoint semantics, and portable Story Artifacts. It does not
own accounts, subscriptions, deployment topology, cloud-specific queues, WebSocket messages, or
user-content retention policy. Those are product or infrastructure concerns connected by hosts.

The Arc Engine interface is deliberately small:

```python
result = engine.run(request)
result = engine.resume(checkpoint_id)
```

Planning, drafting, and refinement are hidden behind the Story Provider seam. Checkpoint storage
and output safety are internal seams with local adapters. The engine returns data instead of
writing exports or emitting network events, allowing CLI, local Web, and Cloud Worker hosts to use
the same module.

See `ARC_ENGINE_V1.md` for the versioned contract and `MIGRATION_EVIDENCE_NAR32.md` for the legacy
evidence that informed this design.
