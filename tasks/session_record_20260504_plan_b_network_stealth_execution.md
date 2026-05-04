# 2026-05-04 - Plan B network-stealth execution

## User request

Dr. Frost asked to check `/home/zi/paper_mobius/exper.tex` and execute the
2026-05-02 Research Plan B under `tasks/`.

## Files checked

- `/home/zi/paper_mobius/exper.tex`
- `tasks/research_plan_0502_ddos_b_network_stealth_ids.md`
- Existing local Ollama/proxy result summaries and proxy logs under:
  - `experiments/results/multiagent_datadog_fileedit_ollama_20260504/`
  - `experiments/results/opencode_datadog_fileedit_ollama_20260503/`
  - `experiments/results/opencode_time_window_free_run_20260503/`
  - `/data2/zi/agentcodingdos_plan_a_logs/`

## Actions performed

- Identified Plan B as `tasks/research_plan_0502_ddos_b_network_stealth_ids.md`.
- Added `experiments/scripts/plan_b_network_stealth_export.py`.
  - It consumes real local Ollama proxy traces for benign, Mobius stealth, and
    Mobius aggressive rows.
  - It runs bounded localhost dummy-service baselines for HTTP flood-like and
    TCP connection-pressure traffic with rate caps.
  - It exports traffic features, detector comparison, detection timing, and
    paper figures.
- Added focused tests in
  `experiments/AgentCallInterface/tests/test_plan_b_network_stealth_export.py`.
- Generated Plan B artifacts:
  - `experiments/results/plan_b_network_stealth_ids_20260504/traffic_features.csv`
  - `experiments/results/plan_b_network_stealth_ids_20260504/detector_comparison.csv`
  - `experiments/results/plan_b_network_stealth_ids_20260504/detection_timing.csv`
  - `experiments/results/plan_b_network_stealth_ids_20260504/classical_local_traffic.jsonl`
  - `/home/zi/paper_mobius/curves/plan_b_network_feature_space.pdf`
  - `/home/zi/paper_mobius/curves/plan_b_detection_timing.pdf`
  - `/home/zi/paper_mobius/scripts/generated/plan_b_network_stealth/`
- Updated `/home/zi/paper_mobius/exper.tex` with a new
  `Network-Layer Stealth and Detector Mismatch` subsection, a detector-layer
  table, and the two Plan B figures.

## Results

- Unit tests passed:
  `uv run pytest experiments/AgentCallInterface/tests/test_plan_b_network_stealth_export.py`
  reported `3 passed`.
- Plan B export completed with generated CSVs and PDFs.
- Paper compile passed:
  `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` completed and
  wrote `/home/zi/paper_mobius/main.pdf`.

## Internal results and caveats

- Measured benign median request rate: `4.80` requests/minute.
- Measured Mobius stealth request rate: `3.66` requests/minute, while still
  showing component mutation evidence.
- Maximum measured aggressive Mobius request rate: `21.19` requests/minute.
- Detector table result:
  - benign agent: flow low, HTTP low, ACE none;
  - Mobius stealth: flow low, HTTP low, ACE high;
  - Mobius aggressive: flow low, HTTP mixed/high, ACE high;
  - TCP pressure: flow high, HTTP low, ACE none;
  - HTTP flood: flow high, HTTP high, ACE none.
- Suricata/Zeek were not available locally, so off-the-shelf IDS results were
  not fabricated. The paper and output table mark IDS as not run.
- The LaTeX build still reports pre-existing unresolved citations/references
  unrelated to this Plan B change: `fig:`, `fig:mobius-example`, `Liu-Prompt`,
  `Greshake-Not`, `Abdelnabi-Not`, `clawbench`, `swebench`, and `humaneval`.

## Follow-up correction after table review

Dr. Frost reviewed the inserted detector table and pointed out that the
`low/high` table was not quantitative enough for academic reporting. I agree
with that criticism.

Actions performed:

- Extended `experiments/scripts/plan_b_network_stealth_export.py` to write a
  quantitative detector table:
  `experiments/results/plan_b_network_stealth_ids_20260504/detector_quantitative.csv`.
- Added a unit test for the quantitative aggregation logic.
- Regenerated Plan B artifacts.
- Replaced the qualitative table in `/home/zi/paper_mobius/exper.tex` with a
  quantitative table reporting:
  - traffic-class sample count;
  - median API requests/minute;
  - median connection events/minute;
  - median tokens;
  - median component events;
  - flow/HTTP/ACE alert fractions;
  - IDS status.

Results:

- `uv run pytest experiments/AgentCallInterface/tests/test_plan_b_network_stealth_export.py`
  reported `4 passed`.
- `python3 experiments/scripts/plan_b_network_stealth_export.py` regenerated
  CSVs and figures.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` completed and
  wrote `/home/zi/paper_mobius/main.pdf`.

## Zeek and Suricata PCAP follow-up

Dr. Frost asked to install Zeek and Suricata and complete the corresponding
Plan-B IDS/NSM experiment.

Installation/configuration actions:

- Direct host `apt` install was blocked because `sudo` requires a password in
  this session.
- Installed the tools as Docker analysis images instead:
  - `zeek/zeek:lts`, verified as Zeek `8.0.7`;
  - `jasonish/suricata:latest`, verified as Suricata `8.0.4`.
- Created and later removed a temporary host-network capture container
  `plan_b_tcpdump_20260504` with `tcpdump` installed inside it.

Experiment actions:

- Added `experiments/scripts/plan_b_ids_pcap_experiment.py`.
- Captured PCAPs for representative local runs:
  - benign OpenCode agent traffic;
  - Mobius stealth OpenCode traffic;
  - Mobius aggressive OpenCode traffic;
  - bounded localhost HTTP flood-like baseline;
  - bounded localhost TCP connection-pressure baseline.
- Ran Zeek and Suricata offline on each PCAP.
- Wrote:
  - `experiments/results/plan_b_network_stealth_ids_20260504/ids_pcap_summary.csv`;
  - per-run PCAP files under
    `experiments/results/plan_b_network_stealth_ids_20260504/pcaps/`;
  - Zeek logs under
    `experiments/results/plan_b_network_stealth_ids_20260504/zeek/`;
  - Suricata logs under
    `experiments/results/plan_b_network_stealth_ids_20260504/suricata/`.

Internal results:

- Zeek emitted connection logs for all representative PCAPs.
- Suricata emitted flow and HTTP telemetry, but no default signature alerts for
  any local class.
- Representative PCAP telemetry:
  - benign: Zeek conn `39`, Suricata HTTP `13`, Suricata alerts `0`;
  - Mobius stealth: Zeek conn `57`, Suricata HTTP `19`, Suricata alerts `0`;
  - Mobius aggressive: Zeek conn `25`, Suricata HTTP `7`, Suricata alerts `0`;
  - TCP pressure: Zeek conn `160`, Suricata HTTP `0`, Suricata alerts `0`;
  - HTTP flood: Zeek conn `160`, Suricata HTTP `80`, Suricata alerts `0`.
- This supports a narrower and more accurate claim: Zeek/Suricata provide
  useful network telemetry, but default offline Suricata processing did not
  produce signature alerts for the local valid-API Mobius traces. Component
  visibility remains necessary for early Mobius attribution.

Paper/update actions:

- Extended `experiments/scripts/plan_b_network_stealth_export.py` to consume
  `ids_pcap_summary.csv` and include Zeek/Suricata columns in
  `detector_quantitative.csv`.
- Updated `/home/zi/paper_mobius/exper.tex` to report Zeek and Suricata
  versions, telemetry columns, and the observed zero Suricata-alert result.
- Regenerated Plan-B figures and compiled the paper.

Verification:

- `uv run pytest experiments/AgentCallInterface/tests/test_plan_b_network_stealth_export.py`
  reported `4 passed`.
- `python3 experiments/scripts/plan_b_ids_pcap_experiment.py` completed and
  wrote `ids_pcap_summary.csv`.
- `python3 experiments/scripts/plan_b_network_stealth_export.py` completed.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` completed and
  wrote `/home/zi/paper_mobius/main.pdf`.
