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
and domain events. It must not own accounts, subscriptions, deployment topology, cloud-specific
queues, or user-content retention policy. Those are product or infrastructure concerns connected
through adapters.

No engine modules exist yet. NAR-32 will create the first domain boundary only after auditing the
legacy prototype. This baseline intentionally avoids placeholder job, worker, and web abstractions.
