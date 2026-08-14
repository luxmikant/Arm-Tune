# ArmTune Serve Benchmark Report

**Generated:** 2026-08-14 10:04:51 UTC

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
| balanced | Q4_K_M | 4 | 0.453 | 1.929 | 2.516 | 2.522 | 26.1 | 98.0 | 1701 | 1.00 | LlamaServerAdapter |
| thread_1 |  |  | 1.649 | 6.396 | 7.959 | 8.117 | 8.1 | 26.0 | 1700 | 1.00 |  |
| thread_2 |  |  | 0.845 | 3.414 | 4.271 | 4.359 | 15.1 | 51.1 | 1700 | 1.00 |  |
| thread_4 |  |  | 0.442 | 1.818 | 2.280 | 2.326 | 28.1 | 100.0 | 1700 | 1.00 |  |
| concurrency_1 |  |  | 0.444 | 1.827 | 2.284 | 2.334 | 28.1 | 99.1 | 1701 | 1.00 |  |
| balanced | Q4_0 | 4 | 0.331 | 1.635 | 1.915 | 1.936 | 33.0 | 134.0 | 1616 | 1.00 | LlamaServerAdapter |
| thread_1 |  |  | 1.214 | 5.660 | 6.607 | 6.690 | 9.7 | 34.8 | 1615 | 1.00 |  |
| thread_2 |  |  | 0.623 | 3.032 | 3.541 | 3.585 | 17.9 | 68.8 | 1616 | 1.00 |  |
| thread_4 |  |  | 0.330 | 1.635 | 1.908 | 1.931 | 32.9 | 134.0 | 1616 | 1.00 |  |
| concurrency_1 |  |  | 0.330 | 1.630 | 1.920 | 1.947 | 33.0 | 134.5 | 1616 | 1.00 |  |
## Runtime evidence

### balanced

## Recommendation

**Objective:** balanced
**Recommended:** `concurrency_1`

'concurrency_1' provides the best balance of latency, throughput, and memory.

### Deploy it

```bash
llama-server -m <model.gguf> -t 4 -c 2048 -np 1  # quantization: Q4_K_M
```

### Metrics

- **p50_latency_s:** 1.63
- **p95_latency_s:** 1.92
- **throughput_tok_s:** 33.0
- **peak_memory_mb:** 1890.0
- **quality_score:** 1.0