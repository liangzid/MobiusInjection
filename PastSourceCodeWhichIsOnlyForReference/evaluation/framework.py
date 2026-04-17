"""
Evaluation Framework for DoS Attack Vectors
============================================
This module provides the framework for evaluating the effectiveness
of DoS attacks against Agent systems.

Metrics:
- Attack Success Rate
- API Quota Consumption
- Response Time Impact
- Detection Rate
"""

import time
import json
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class ExperimentStatus(Enum):
    """Status of an experiment"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AttackOutcome(Enum):
    """Outcome of an attack attempt"""
    SUCCESS = "success"           # Attack successfully executed
    PARTIAL = "partial"          # Attack partially executed
    FAILED = "failed"            # Attack failed to execute
    DETECTED = "detected"        # Attack was detected/blocked
    TIMEOUT = "timeout"          # Experiment timed out


@dataclass
class ExperimentMetrics:
    """Metrics collected during an experiment"""
    # Basic metrics
    start_time: float = 0
    end_time: float = 0
    duration_seconds: float = 0

    # API metrics
    total_api_calls: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost_estimate: float = 0

    # Attack metrics
    outcome: AttackOutcome = AttackOutcome.FAILED
    attack_iterations: int = 0
    resource_consumption_mb: float = 0

    # Detection metrics
    was_detected: bool = False
    detection_method: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "total_api_calls": self.total_api_calls,
            "total_tokens_input": self.total_tokens_input,
            "total_tokens_output": self.total_tokens_output,
            "total_cost_estimate": self.total_cost_estimate,
            "outcome": self.outcome.value,
            "attack_iterations": self.attack_iterations,
            "resource_consumption_mb": self.resource_consumption_mb,
            "was_detected": self.was_detected,
            "detection_method": self.detection_method
        }


@dataclass
class Experiment:
    """Represents a single experiment"""
    id: str
    name: str
    attack_vector_id: str
    target_system: str
    status: ExperimentStatus = ExperimentStatus.PENDING
    metrics: ExperimentMetrics = field(default_factory=ExperimentMetrics)
    config: dict = field(default_factory=dict)
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "attack_vector_id": self.attack_vector_id,
            "target_system": self.target_system,
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
            "config": self.config,
            "error_message": self.error_message
        }


class ExperimentRunner:
    """
    Runs DoS attack experiments against Agent systems.
    This is a framework that needs to be configured with actual API clients.
    """

    def __init__(self, api_client=None, max_duration_seconds: int = 300):
        self.api_client = api_client
        self.max_duration_seconds = max_duration_seconds
        self.experiments: list[Experiment] = []

    def create_experiment(
        self,
        name: str,
        attack_vector_id: str,
        target_system: str,
        config: Optional[dict] = None
    ) -> Experiment:
        """Create a new experiment"""
        experiment_id = f"exp_{len(self.experiments)}_{int(time.time())}"
        experiment = Experiment(
            id=experiment_id,
            name=name,
            attack_vector_id=attack_vector_id,
            target_system=target_system,
            config=config or {}
        )
        self.experiments.append(experiment)
        return experiment

    def run_experiment(self, experiment: Experiment, malicious_prompt: str) -> ExperimentMetrics:
        """
        Run a single experiment with the given malicious prompt.

        This is a template that should be customized based on the target system.
        """
        experiment.status = ExperimentStatus.RUNNING
        experiment.metrics.start_time = time.time()

        # Placeholder for actual implementation
        # In a real implementation, this would:
        # 1. Initialize the target Agent system
        # 2. Inject the malicious prompt
        # 3. Monitor API calls, resource usage, etc.
        # 4. Determine attack outcome

        print(f"Running experiment: {experiment.name}")
        print(f"Attack vector: {experiment.attack_vector_id}")
        print(f"Target system: {experiment.target_system}")
        print(f"Malicious prompt: {malicious_prompt[:100]}...")

        # Simulate experiment duration
        time.sleep(0.1)

        experiment.metrics.end_time = time.time()
        experiment.metrics.duration_seconds = experiment.metrics.end_time - experiment.metrics.start_time
        experiment.status = ExperimentStatus.COMPLETED

        return experiment.metrics

    def generate_report(self, output_file: Optional[str] = None) -> dict:
        """Generate a report of all experiments"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_experiments": len(self.experiments),
            "experiments": [exp.to_dict() for exp in self.experiments],
            "summary": {
                "success_rate": self._calculate_success_rate(),
                "average_duration": self._calculate_average_duration(),
                "total_api_calls": self._calculate_total_api_calls(),
            }
        }

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {output_file}")

        return report

    def _calculate_success_rate(self) -> float:
        """Calculate attack success rate"""
        if not self.experiments:
            return 0.0

        successful = sum(
            1 for exp in self.experiments
            if exp.metrics.outcome == AttackOutcome.SUCCESS
        )
        return successful / len(self.experiments)

    def _calculate_average_duration(self) -> float:
        """Calculate average experiment duration"""
        if not self.experiments:
            return 0.0

        total = sum(exp.metrics.duration_seconds for exp in self.experiments)
        return total / len(self.experiments)

    def _calculate_total_api_calls(self) -> int:
        """Calculate total API calls across all experiments"""
        return sum(exp.metrics.total_api_calls for exp in self.experiments)


def create_sample_experiments() -> list[Experiment]:
    """Create sample experiments for demonstration"""
    from experiments.attack_vectors.dos_attack_vectors import AttackVectorLibrary

    experiments = []
    runner = ExperimentRunner()

    for vector in AttackVectorLibrary.get_all_vectors():
        exp = runner.create_experiment(
            name=f"Test_{vector.name.replace(' ', '_')}",
            attack_vector_id=vector.type.value,
            target_system=vector.target_system
        )
        experiments.append(exp)

    return experiments


if __name__ == "__main__":
    # Demonstrate the framework
    print("=" * 80)
    print("EXPERIMENT FRAMEWORK DEMONSTRATION")
    print("=" * 80)

    experiments = create_sample_experiments()
    print(f"\nCreated {len(experiments)} sample experiments:")
    for exp in experiments:
        print(f"  - {exp.name} (target: {exp.target_system})")

    # Generate sample report
    runner = ExperimentRunner()
    runner.experiments = experiments

    # Simulate some results
    for exp in experiments:
        exp.status = ExperimentStatus.COMPLETED
        exp.metrics.outcome = AttackOutcome.SUCCESS
        exp.metrics.total_api_calls = 100
        exp.metrics.duration_seconds = 10.5

    report = runner.generate_report()
    print(f"\nSummary:")
    print(f"  Success rate: {report['summary']['success_rate']*100:.1f}%")
    print(f"  Total API calls: {report['summary']['total_api_calls']}")
