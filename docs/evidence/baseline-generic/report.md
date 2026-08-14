# ArmTune Serve Benchmark Report

**Generated:** 2026-08-14 10:01:20 UTC

## Hardware

- Architecture: `aarch64`
- CPU: unknown
- Cores: 4P / 4L
- Memory: 15.57 GB
- NUMA nodes: 1
- Arm features: `sve2 sve i8mm bf16 asimddp asimd fp`

## Results

| Profile | Quant | Threads | TTFT (s) | P50 (s) | P95 (s) | P99 (s) | tok/s | Prompt tok/s | Peak RSS (MB) | Quality | Runtime |
|---------|-------|---------|----------|---------|---------|---------|-------|--------------|---------------|---------|---------|
| baseline | Q4_K_M | 4 | 0.457 | 1.952 | 2.180 | 2.200 | 27.3 | 97.3 | 1700 | 0.85 | LlamaServerAdapter |
| thread_1 |  |  | 1.648 | 6.403 | 7.548 | 7.599 | 8.1 | 26.0 | 1700 | 0.85 |  |
| thread_2 |  |  | 0.844 | 3.354 | 3.966 | 3.993 | 15.3 | 51.3 | 1700 | 0.85 |  |
| thread_4 |  |  | 0.444 | 1.800 | 2.111 | 2.124 | 28.5 | 99.3 | 1700 | 0.85 |  |
| concurrency_1 |  |  | 0.444 | 1.788 | 2.119 | 2.130 | 28.5 | 99.6 | 1700 | 0.85 |  |
| baseline | Q4_0 | 4 | 0.334 | 1.721 | 1.993 | 2.000 | 33.2 | 132.7 | 1616 | 1.00 | LlamaServerAdapter |
| thread_1 |  |  | 1.231 | 5.936 | 6.891 | 6.921 | 9.7 | 34.4 | 1616 | 1.00 |  |
| thread_2 |  |  | 0.632 | 3.225 | 3.736 | 3.749 | 17.8 | 67.8 | 1616 | 1.00 |  |
| thread_4 |  |  | 0.333 | 1.719 | 1.984 | 1.991 | 33.3 | 133.0 | 1616 | 1.00 |  |
| concurrency_1 |  |  | 0.334 | 1.714 | 1.986 | 1.991 | 33.4 | 133.0 | 1616 | 1.00 |  |
## Runtime evidence

### baseline

## Recommendation

**Objective:** balanced
**Recommended:** `concurrency_1`

'concurrency_1' provides the best balance of latency, throughput, and memory.

### Deploy it

```bash
llama-server -m <model.gguf> -t 4 -c 2048 -np 1  # quantization: Q8_0
```

### Metrics

- **p50_latency_s:** 1.714
- **p95_latency_s:** 1.9859
- **throughput_tok_s:** 33.4
- **peak_memory_mb:** 1866.0
- **quality_score:** 1.0