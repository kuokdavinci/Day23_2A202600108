# Day 23 Lab Reflection

**Student:** Kuok Da Vinci
**Submission date:** 2026-05-11
**Lab repo URL:** https://github.com/VinUni-AI20k/Day23-Track2-Observability-Lab

---

## 1. Hardware + setup output

Paste output of `python3 00-setup/verify-docker.py`:

```
Docker:        OK  (29.4.3)
Compose v2:    OK  (5.1.3)
RAM available: 15.44 GB (OK)
Ports free:    BOUND: [8000, 9090, 9093, 3000, 3100, 16686, 4317, 4318, 8888]
Report written: /home/kuokdavinci/VinProject/Day23-Track2-Observability-Lab/00-setup/setup-report.json
```

---

## 2. Track 02 — Dashboards & Alerts

### 6 essential panels (screenshot)

Evidence: `submission/screenshots/AI_service.png`

### Burn-rate panel

Evidence: `submission/screenshots/burnrate.png`

### Alert fire + resolve

| When | What | Evidence |
|---|---|---|
| _T0_ | killed `day23-app`         | screenshot `submission/screenshots/alertmanaer.png` |
| _T0+90s_ | `ServiceDown` fired   | screenshot `submission/screenshots/slack.png` (FIRE message) |
| _T1_ | restored app              | — |
| _T1+60s_ | alert resolved        | screenshot `submission/screenshots/slack.png` (RESOLVE message) |

### One thing surprised me about Prometheus / Grafana

I was surprised by how powerful the multi-window multi-burn-rate alerting logic is in Prometheus. Instead of just looking at instantaneous spikes which cause alert fatigue, burn-rates allow us to compute how fast we are exhausting our error budget over distinct time windows (e.g., 1h and 6h) to trigger alarms only on sustained, severe degradations.

---

## 3. Track 03 — Tracing & Logs

### One trace screenshot from Jaeger

Evidence: `submission/screenshots/jeager.png` showing `predict → embed-text → vector-search → generate-tokens` spans.

### Log line correlated to trace

Paste the log line and the trace_id it links to:

```json
{"model": "llama3-mock", "input_tokens": 4, "output_tokens": 22, "quality": 0.759, "duration_seconds": 0.2953, "trace_id": "f0cce4191e7bf17519c05b5717f2304e", "event": "prediction served", "level": "info", "timestamp": "2026-05-11T15:20:16.571776Z"}
```
Linked Trace ID: `f0cce4191e7bf17519c05b5717f2304e`

### Tail-sampling math

Let $N$ be the total number of traces generated per second. Let $E$ represent the fraction of requests that fail (returning errors) or are slow ($>2\text{s}$), and let $1-E$ represent the fraction of successful, fast (healthy) requests. 

The composite tail-sampling policy keeps $100\%$ of failures/slow traces and only $1\%$ of healthy traces. Therefore, the total sampled rate $S$ is:
$$S = N \times [E + 0.01 \times (1 - E)]$$

For example, if the system produces $N = 100\text{ traces/sec}$ with an error/slow rate of $2\%$ ($E = 0.02$):
* We keep $100\%$ of the $2\text{ failed/slow traces/sec} = 2\text{ traces/sec}$.
* We keep $1\%$ of the remaining $98\text{ healthy traces/sec} = 0.98\text{ traces/sec}$.
* Total kept: $2 + 0.98 = 2.98\text{ traces/sec}$.

This represents an ingestion and storage cost-saving of **$97.02\%$** while preserving $100\%$ visibility into every single system error and latency regression.

---

## 4. Track 04 — Drift Detection

### PSI scores

Paste `04-drift-detection/reports/drift-summary.json`:

```json
{
  "prompt_length": {
    "psi": 3.461,
    "kl": 1.7982,
    "ks_stat": 0.702,
    "ks_pvalue": 0.0,
    "drift": "yes"
  },
  "embedding_norm": {
    "psi": 0.0187,
    "kl": 0.0324,
    "ks_stat": 0.052,
    "ks_pvalue": 0.133853,
    "drift": "no"
  },
  "response_length": {
    "psi": 0.0162,
    "kl": 0.0178,
    "ks_stat": 0.056,
    "ks_pvalue": 0.086899,
    "drift": "no"
  },
  "response_quality": {
    "psi": 8.8486,
    "kl": 13.5011,
    "ks_stat": 0.941,
    "ks_pvalue": 0.0,
    "drift": "yes"
  }
}
```

### Which test fits which feature?

* **`prompt_length` (continuous numerical)**: We use **Kolmogorov-Smirnov (KS)**. Because prompt length is numerical and can vary widely in shape without following a normal distribution, KS is a powerful non-parametric test to check if two continuous distributions differ significantly in shape or location without assuming a specific distribution.
* **`embedding_norm` (continuous normalized numerical)**: We use **Maximum Mean Discrepancy (MMD)** in production. Since embeddings are high-dimensional vectors, checking just the 1D norm is limiting. MMD measures distance between distributions in a higher-dimensional Hilbert space, making it perfect for detecting subtle drift in semantic embeddings.
* **`response_length` (skewed continuous numerical)**: We use **Kullback-Leibler (KL) Divergence**. KL divergence is excellent when comparing response length distributions (which are typically heavily skewed) because it quantifies the precise information loss or entropy shift when replacing our reference distribution with our active production distribution.
* **`response_quality` (bounded continuous range $[0,1]$)**: We use **Population Stability Index (PSI)**. Quality scores represent a bounded grading metric. By segmenting scores into distinct business-meaningful bins (e.g. $[0,0.4]$ for bad, $[0.4,0.7]$ for moderate, and $[0.7,1.0]$ for high quality), we can use PSI to monitor if the proportion of high vs low quality answers is shifting significantly over time.

---

## 5. Track 05 — Cross-Day Integration

### Which prior-day metric was hardest to expose? Why?

Exposing llama.cpp metrics from Day 20 was the hardest because llama.cpp's standard server does not natively expose a structured Prometheus endpoint. We had to configure a custom sidecar script to tail the server logs or parse its API responses, convert the timing/tokens data on the fly into Prometheus gauge/counter formats, and serve them on a separate port. This introduces additional network hopping and potential latency in the metrics scraping loop.

### Cross-day dashboard

Evidence: `submission/screenshots/cross_day.png` — 6 panels covering Days 16–22.

---

## 6. The single change that mattered most

The single change that mattered most was the configuration of the composite tail-sampling policy in the OpenTelemetry Collector. In production AI workloads, logging and tracing every single request generates a massive volume of telemetry, which quickly bottlenecks network bandwidth and leads to exorbitant ingestion costs in Jaeger/Loki. In our composite sampling policy, we retained 100% of error traces and slow requests (>2s), but kept only 1% of successful, fast requests.

This ensures that our SREs have complete, 100% visibility into failures, high latency bottlenecks, and exceptions to run post-mortems and identify bugs, while saving 99% of storage and processing costs for healthy, repetitive requests. It strikes the perfect operational balance between cost efficiency and diagnostic completeness, illustrating the concept of Cardinality & Telemetry Volume Control covered in Section 6 and 8 of the lecture deck.
