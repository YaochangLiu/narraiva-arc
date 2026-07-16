"""Generate a deterministic synthetic story without network access."""

from narraiva_arc import ArcEngine, GenerationRequest

request = GenerationRequest.from_input(
    "A lighthouse keeper receives a letter from a ship that vanished thirty years ago."
)
result = ArcEngine.offline().run(request)

if result.artifact is None:
    raise SystemExit(f"Generation stopped: {result.status.value}")

print(result.artifact.markdown)
