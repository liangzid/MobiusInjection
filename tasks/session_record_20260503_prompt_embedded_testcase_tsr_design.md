# Session Record: Prompt-Embedded Test Case TSR Design

Date: 2026-05-03

## User Request

Dr. Frost suggested that the benchmark test cases could be included directly in the agent prompt, requiring the final answer to report test-case results. The proposed Task Success definition is: the run completes and more than two test cases pass.

## Design Response

Embedding public test cases in the prompt is useful because it standardizes the agent's expected output and can make result extraction easier. However, self-reported test results should not be the only evidence for TSR, because a model can hallucinate, miscount, or claim that tests passed without executing them.

Recommended design:

- Include a bounded public test suite in the prompt.
- Require the agent to write a candidate solution file and a machine-readable final JSON report.
- Ask the agent to run the provided tests and report per-test pass/fail.
- Independently rerun the same provided tests from the monitor against the candidate solution.
- Define primary TSR from the monitor's independent verifier, not from self-report.
- Preserve the self-reported result as `agent_reported_*` diagnostic fields.

Recommended Task Success formula:

`TSR = runner_succeeded and verifier_ran and verified_tests_passed >= 2`

Optional diagnostic metric:

`REPORTED_TSR = runner_succeeded and agent_reported_tests_passed >= 2`

## Result

No production code was changed in this step. The result is a proposed metric and monitor design for the formal serial experiment.
