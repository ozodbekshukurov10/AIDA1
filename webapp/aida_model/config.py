from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AidaArchitectureConfig:
    vocab_size: int = 32768
    hidden_dim: int = 4096
    num_layers: int = 32
    num_heads: int = 32
    num_kv_heads: int = 8
    head_dim: int = 128
    max_seq_len: int = 131072
    dropout: float = 0.0
    activation_fn: str = "swiglu"
    norm_eps: float = 1e-5
    rope_theta: float = 1000000.0
    embed_dim: int = 4096
    reasoning_steps: int = 8
    planning_horizon: int = 10
    memory_capacity: int = 100000
    memory_dim: int = 2048
    tool_cache_size: int = 1000
    moe_num_experts: int = 8
    moe_top_k: int = 2
    use_flash_attn: bool = True
    kv_cache: bool = True
    quantize: str = "fp16"


@dataclass
class AidaConfig:
    architecture: AidaArchitectureConfig = field(default_factory=AidaArchitectureConfig)
    model_name: str = "aida-core"
    model_version: str = "1.0.0"
    model_type: str = "decoder-only"
    base_model: str = ""
    description: str = "AIDA - Artificial Intelligence for Development & Automation"
    author: str = "AIDA Team"
    license: str = "MIT"
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "model_type": self.model_type,
            "description": self.description,
            "architecture": {
                "vocab_size": self.architecture.vocab_size,
                "hidden_dim": self.architecture.hidden_dim,
                "num_layers": self.architecture.num_layers,
                "num_heads": self.architecture.num_heads,
                "num_kv_heads": self.architecture.num_kv_heads,
                "head_dim": self.architecture.head_dim,
                "max_seq_len": self.architecture.max_seq_len,
                "activation_fn": self.architecture.activation_fn,
                "moe_num_experts": self.architecture.moe_num_experts,
                "moe_top_k": self.architecture.moe_top_k,
                "quantize": self.architecture.quantize,
                "use_flash_attn": self.architecture.use_flash_attn,
            },
        }
