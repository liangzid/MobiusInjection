# Plan B Network-Stealth Export

Inputs are real local Ollama proxy traces plus fresh bounded localhost dummy-service baselines.

- Benign median request rate: 5.50/min; stealth Mobius request rate: 3.66/min.
- Maximum aggressive Mobius request rate: 8.49/min.
- Zeek/Suricata PCAP telemetry is included from `ids_pcap_summary.csv`.

## Detector Table

| Traffic Type | Flow | HTTP Rate | IDS Tool | ACE | Notes |
| --- | --- | --- | --- | --- | --- |
| Benign Agent | low | low | not run | none | normal local LLM API traffic |
| Mobius Stealth | low | low | not run | high | valid API calls with component mutation |
| Mobius Aggressive | low | low | not run | high | valid API calls; some runs exceed HTTP-rate rule |
| TCP Pressure | high | low | not run | none | bounded localhost connection-pressure baseline |
| HTTP Flood | high | high | not run | none | bounded localhost high-rate HTTP baseline |

## Quantitative Detector Table

| Traffic Type | N | Req/min | Conn/min | Tokens | Component Events | Flow Alerts | HTTP Alerts | ACE Alerts | Zeek Conn | Suricata HTTP | Suricata Alerts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Benign Agent | 3 | 5.5 | 5.5 | 123643.0 | 0.0 | 0/3 | 0/3 | 0/3 | 39.0 | 13.0 | 0/1 |
| Mobius Stealth | 1 | 3.66 | 3.66 | 65887.0 | 4.0 | 0/1 | 0/1 | 1/1 | 57.0 | 19.0 | 0/1 |
| Mobius Aggressive | 4 | 5.77 | 5.82 | 713645.5 | 8.0 | 0/4 | 0/4 | 4/4 | 25.0 | 7.0 | 0/1 |
| TCP Pressure | 1 | 0.0 | 1194.03 | 0.0 | 0.0 | 1/1 | 0/1 | 0/1 | 160.0 | 0.0 | 0/1 |
| HTTP Flood | 1 | 1177.23 | 1177.23 | 0.0 | 0.0 | 1/1 | 1/1 | 0/1 | 160.0 | 80.0 | 0/1 |
