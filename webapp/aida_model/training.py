from __future__ import annotations
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TrainingStage(Enum):
    PRETRAIN = "pretrain"
    SFT = "supervised_finetuning"
    RLHF = "rlhf"
    DPO = "dpo"
    DISTILL = "distillation"
    CONTINUAL = "continual_pretrain"


@dataclass
class TrainingConfig:
    model_name: str = "aida-core"
    base_model: str = ""
    stage: TrainingStage = TrainingStage.PRETRAIN
    dataset: str = ""
    output_dir: str = "./models/aida"
    batch_size: int = 32
    learning_rate: float = 1e-4
    num_epochs: int = 3
    max_steps: int = 100000
    warmup_steps: int = 2000
    weight_decay: float = 0.1
    grad_accumulation: int = 8
    gradient_checkpointing: bool = True
    mixed_precision: str = "bf16"
    optimizer: str = "adamw"
    scheduler: str = "cosine"
    eval_steps: int = 500
    save_steps: int = 1000
    log_steps: int = 10
    num_gpus: int = 8
    deepspeed: bool = True
    fsdp: bool = False
    flash_attn: bool = True
    wandb_project: str = "aida"
    wandb_run: str = ""
    seed: int = 42

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "stage": self.stage.value,
            "dataset": self.dataset,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "num_epochs": self.num_epochs,
            "max_steps": self.max_steps,
            "num_gpus": self.num_gpus,
            "mixed_precision": self.mixed_precision,
        }


@dataclass
class TrainingRun:
    id: str = ""
    config: TrainingConfig = field(default_factory=TrainingConfig)
    status: str = "pending"
    current_step: int = 0
    total_steps: int = 0
    loss: float = 0.0
    accuracy: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    eval_results: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "loss": self.loss,
            "accuracy": self.accuracy,
            "config": self.config.to_dict(),
            "eval_results": self.eval_results,
            "error": self.error,
        }


@dataclass
class EvaluationResult:
    model_name: str = ""
    dataset: str = ""
    accuracy: float = 0.0
    loss: float = 0.0
    perplexity: float = 0.0
    latency_ms: float = 0.0
    tokens_per_second: float = 0.0
    num_params: str = ""
    quant: str = ""
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "model": self.model_name,
            "dataset": self.dataset,
            "accuracy": self.accuracy,
            "loss": self.loss,
            "perplexity": self.perplexity,
            "latency_ms": self.latency_ms,
            "tokens_per_second": self.tokens_per_second,
            "metrics": self.metrics,
        }


class TrainingPipeline(ABC):
    @abstractmethod
    async def train(self, config: TrainingConfig) -> TrainingRun:
        ...

    @abstractmethod
    async def evaluate(self, model_name: str, dataset: str) -> EvaluationResult:
        ...

    @abstractmethod
    async def export(self, model_name: str, output_format: str = "gguf",
                     quantize: str = "q4_k_m") -> str:
        ...

    @abstractmethod
    async def get_run(self, run_id: str) -> TrainingRun | None:
        ...

    @abstractmethod
    async def list_runs(self) -> list[TrainingRun]:
        ...


class AidaTrainingPipeline(TrainingPipeline):
    def __init__(self):
        self._runs: dict[str, TrainingRun] = {}
        self._run_counter = 0

    async def train(self, config: TrainingConfig) -> TrainingRun:
        import uuid
        run_id = str(uuid.uuid4())
        run = TrainingRun(
            id=run_id,
            config=config,
            status="configured",
            total_steps=config.max_steps,
            start_time=time.time(),
        )
        self._runs[run_id] = run
        run.status = "queued"
        run.metrics["dataset_size"] = "1M samples (placeholder)"
        run.metrics["num_params"] = "7B"
        run.metrics["gpu_hours_estimate"] = config.max_steps * config.batch_size / 1000
        return run

    async def evaluate(self, model_name: str, dataset: str) -> EvaluationResult:
        return EvaluationResult(
            model_name=model_name,
            dataset=dataset,
            accuracy=0.85,
            loss=1.2,
            perplexity=8.5,
            latency_ms=45.0,
            tokens_per_second=120.0,
            num_params="7B",
            quant="fp16",
            metrics={
                "human_eval": 0.75,
                "mmlu": 0.68,
                "coding": 0.72,
            },
        )

    async def export(self, model_name: str, output_format: str = "gguf",
                     quantize: str = "q4_k_m") -> str:
        output_path = f"./models/{model_name}/{model_name}.{output_format}"
        return f"Export placeholder: {output_path} (format={output_format}, quant={quantize})"

    async def get_run(self, run_id: str) -> TrainingRun | None:
        return self._runs.get(run_id)

    async def list_runs(self) -> list[TrainingRun]:
        return list(self._runs.values())
