# Capacity Note

- **Locked model:** Qwen/Qwen2.5-1.5B-Instruct-AWQ
- **Target p95 SLO:** 2.0 seconds
- **Knee concurrency:** 2
- **Tokens/s at knee:** 144.2
- **Max sustainable request rate:** ~20 requests per tier under SLO constraints
- **Limiting family:** Memory-bound / Tail-latency constrained (latency increases past the 2.0s SLO threshold at concurrency 4, restricting higher sustainable loads)
- **Why knee, not peak:** Peak throughput reaches 663.6 tok/s at concurrency 16, but p95 latency spikes to 2.429s (violating our 2.0s SLO target). The knee at concurrency 2 is the maximum safe operating load we can promise while strictly respecting the latency SLO.
