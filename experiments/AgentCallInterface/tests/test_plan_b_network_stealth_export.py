import experiments.scripts.plan_b_network_stealth_export as plan_b
from experiments.scripts.plan_b_network_stealth_export import (
    aggregate_quantitative_rows,
    detector_flags,
    detector_thresholds,
    summarize_events,
    timing_rows,
)


def test_summarize_events_uses_real_record_fields() -> None:
    rows = [
        {
            "method": "POST",
            "request_bytes": 100,
            "response_bytes": 50,
            "latency_ms": 10,
            "status_code": 200,
            "total_tokens": 12,
        },
        {
            "method": "POST",
            "request_bytes": 200,
            "response_bytes": 75,
            "latency_ms": 40,
            "status_code": 500,
            "total_tokens": None,
        },
        {"method": "HEAD", "request_bytes": 0, "response_bytes": 0, "status_code": 200},
    ]

    feature = summarize_events(
        traffic_type="Mobius Stealth",
        sample_id="sample",
        records=rows,
        duration_seconds=30,
        component_events=2,
        notes="unit",
    )

    assert feature["http_requests"] == 2
    assert feature["connection_attempts"] == 3
    assert feature["requests_per_min"] == 4.0
    assert feature["bytes_per_sec"] == 14.167
    assert feature["failed_request_rate"] == 0.5
    assert feature["total_tokens"] == 12
    assert feature["component_events"] == 2


def test_detector_flags_separate_component_signal_from_network_rate() -> None:
    rows = [
        {
            "traffic_type": "Benign Agent",
            "sample_id": "benign",
            "requests_per_min": 4.0,
            "connections_per_min": 4.0,
            "component_events": 0,
            "notes": "benign",
        },
        {
            "traffic_type": "Mobius Stealth",
            "sample_id": "stealth",
            "requests_per_min": 5.0,
            "connections_per_min": 5.0,
            "component_events": 2,
            "notes": "stealth",
        },
        {
            "traffic_type": "HTTP Flood",
            "sample_id": "http",
            "requests_per_min": 120.0,
            "connections_per_min": 120.0,
            "component_events": 0,
            "notes": "http",
        },
    ]

    thresholds = detector_thresholds(rows)
    stealth = detector_flags(rows[1], thresholds)
    http = detector_flags(rows[2], thresholds)

    assert stealth["flow_detector"] == "low"
    assert stealth["http_rate_detector"] == "low"
    assert stealth["ace_component_signal"] == "high"
    assert http["flow_detector"] == "high"
    assert http["http_rate_detector"] == "high"
    assert http["ace_component_signal"] == "none"


def test_timing_rows_place_ace_before_resource_detectors() -> None:
    features = [
        {
            "traffic_type": "Mobius Stealth",
            "sample_id": "stealth",
            "total_tokens": 100,
        }
    ]
    flags = [
        {
            "traffic_type": "Mobius Stealth",
            "sample_id": "stealth",
            "flow_detected": False,
            "http_detected": False,
            "ace_detected": True,
        }
    ]

    timing = timing_rows(features, flags)[0]

    assert timing["ace_stage"] == "component snapshot"
    assert timing["flow_stage"] == "none"
    assert timing["http_stage"] == "none"
    assert timing["tokens_before_ace_detection"] == 0
    assert timing["tokens_before_flow_detection"] == 100


def test_aggregate_quantitative_rows_reports_numeric_alert_counts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(plan_b, "IDS_PCAP_CSV", tmp_path / "missing_ids.csv")
    features = [
        {
            "traffic_type": "Benign Agent",
            "sample_id": "benign",
            "requests_per_min": 4.0,
            "connections_per_min": 5.0,
            "total_tokens": 10,
            "component_events": 0,
        },
        {
            "traffic_type": "Mobius Stealth",
            "sample_id": "stealth",
            "requests_per_min": 3.0,
            "connections_per_min": 3.0,
            "total_tokens": 100,
            "component_events": 2,
        },
    ]
    flags = [
        {
            "sample_id": "benign",
            "flow_detected": False,
            "http_detected": False,
            "ace_detected": False,
        },
        {
            "sample_id": "stealth",
            "flow_detected": False,
            "http_detected": False,
            "ace_detected": True,
        },
    ]

    rows = aggregate_quantitative_rows(features, flags)
    stealth = next(row for row in rows if row["traffic_type"] == "Mobius Stealth")

    assert stealth["n"] == 1
    assert stealth["median_requests_per_min"] == 3.0
    assert stealth["median_tokens"] == 100.0
    assert stealth["ace_alerts"] == "1/1"
    assert stealth["flow_alerts"] == "0/1"
    assert stealth["zeek_conn_median"] == "n/r"
    assert stealth["suricata_alerts"] == "n/r"
