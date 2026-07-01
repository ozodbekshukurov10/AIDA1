from __future__ import annotations
import json
import logging
import shutil
import time
from pathlib import Path
from threading import Lock
from typing import Any

from .config import Proposal, ProposalStatus, ProposalType

logger = logging.getLogger("webapp.self_improvement.approval")


class ApprovalSystem:
    _instance: ApprovalSystem | None = None
    _lock: Lock = Lock()

    def __init__(self):
        self._history: list[dict] = []
        self._max_history = 500
        self._backup_dir = Path(".self_improvement_backups")
        self._backup_dir.mkdir(exist_ok=True)

    @classmethod
    def get_instance(cls) -> ApprovalSystem:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def propose(self, proposal: Proposal) -> Proposal:
        logger.info(f"[APPROVAL] New proposal: [{proposal.severity.value}] {proposal.title}")
        return proposal

    def approve(self, proposal: Proposal) -> Proposal:
        if proposal.status != ProposalStatus.PENDING:
            return proposal
        proposal.status = ProposalStatus.APPROVED
        proposal.approved_at = time.time()
        logger.info(f"[APPROVAL] Approved: {proposal.title}")
        self._log_action("approve", proposal)
        return proposal

    def reject(self, proposal: Proposal, reason: str = "") -> Proposal:
        if proposal.status != ProposalStatus.PENDING:
            return proposal
        proposal.status = ProposalStatus.REJECTED
        proposal.rejected_reason = reason
        logger.info(f"[APPROVAL] Rejected: {proposal.title} (reason: {reason[:50]})")
        self._log_action("reject", proposal)
        return proposal

    def defer(self, proposal: Proposal) -> Proposal:
        if proposal.status != ProposalStatus.PENDING:
            return proposal
        proposal.status = ProposalStatus.DEFERRED
        logger.info(f"[APPROVAL] Deferred: {proposal.title}")
        self._log_action("defer", proposal)
        return proposal

    def mark_applied(self, proposal: Proposal, success: bool = True) -> Proposal:
        proposal.status = ProposalStatus.APPLIED if success else ProposalStatus.FAILED
        proposal.applied_at = time.time()
        self._log_action("applied" if success else "failed", proposal)
        return proposal

    def backup_file(self, file_path: str) -> str | None:
        src = Path(file_path)
        if not src.exists():
            return None
        backup_name = f"{src.name}.{int(time.time())}.bak"
        dest = self._backup_dir / backup_name
        try:
            shutil.copy2(str(src), str(dest))
            logger.info(f"[APPROVAL] Backed up {file_path} -> {dest}")
            return str(dest)
        except Exception as e:
            logger.error(f"[APPROVAL] Backup failed: {e}")
            return None

    def apply_change(self, proposal: Proposal) -> bool:
        if proposal.status != ProposalStatus.APPROVED:
            logger.warning(f"[APPROVAL] Cannot apply unapproved proposal: {proposal.id}")
            return False
        if not proposal.target_file or not proposal.suggested_content:
            logger.warning(f"[APPROVAL] Proposal {proposal.id} has no content to apply")
            return False
        backup = self.backup_file(proposal.target_file)
        if backup is None:
            logger.warning(f"[APPROVAL] No backup created for {proposal.target_file}")
        try:
            with open(proposal.target_file, "w", encoding="utf-8") as f:
                f.write(proposal.suggested_content)
            proposal.metrics_after["backup"] = backup or ""
            self.mark_applied(proposal, True)
            logger.info(f"[APPROVAL] Applied changes to {proposal.target_file}")
            return True
        except Exception as e:
            self.mark_applied(proposal, False)
            logger.error(f"[APPROVAL] Failed to apply: {e}")
            return False

    def rollback(self, proposal: Proposal) -> bool:
        backup = proposal.metrics_after.get("backup", "")
        if not backup or not Path(backup).exists():
            logger.warning(f"[APPROVAL] No backup to rollback for {proposal.id}")
            return False
        try:
            shutil.copy2(backup, proposal.target_file)
            logger.info(f"[APPROVAL] Rolled back {proposal.target_file}")
            return True
        except Exception as e:
            logger.error(f"[APPROVAL] Rollback failed: {e}")
            return False

    def _log_action(self, action: str, proposal: Proposal):
        entry = {
            "action": action,
            "proposal_id": proposal.id,
            "title": proposal.title,
            "type": proposal.type.value,
            "severity": proposal.severity.value,
            "timestamp": time.time(),
        }
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_history(self, limit: int = 50) -> list[dict]:
        return self._history[-limit:]

    def get_stats(self) -> dict:
        action_map = {
            "approve": "approved", "reject": "rejected", "defer": "deferred",
            "applied": "applied", "failed": "failed",
        }
        stats = {"approved": 0, "rejected": 0, "deferred": 0, "applied": 0, "failed": 0}
        for entry in self._history:
            action = entry.get("action", "")
            key = action_map.get(action, action)
            if key in stats:
                stats[key] += 1
        return stats
