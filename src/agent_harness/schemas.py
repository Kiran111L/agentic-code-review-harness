from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Role(str, Enum):
    planner = "planner"
    bug = "bug"
    security = "security"
    quality = "quality"
    checker = "checker"
    baseline = "baseline"

class Status(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    timed_out = "timed_out"
    partial = "partial"
    limited = "limited"

class FindingCategory(str, Enum):
    correctness = "correctness"
    security = "security"
    reliability = "reliability"
    performance = "performance"
    maintainability = "maintainability"
    testing = "testing"

class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    informational = "informational"

class RunLimits(BaseModel):
    max_wall_seconds: float = 240
    max_interactions: int = 40
    max_model_calls: int = 12
    max_input_tokens: int = 50000
    max_output_tokens: int = 12000
    max_agent_seconds: float = 30
    max_agent_interactions: int = 10
    max_retries: int = 2
    max_correction_rounds: int = 2
    max_cost_usd: float | None = None

class RunConfig(BaseModel):
    run_id: str
    task: str
    project_root: str
    mode: str
    model: str
    limits: RunLimits = Field(default_factory=RunLimits)
    paid_calls_approved: bool = False

class AgentTask(BaseModel):
    task_id: str
    role: Role
    description: str
    context: str = ""
    expected_output: str = "JSON Finding list"
    allowed_tools: list[str] = Field(default_factory=list)
    status: Status = Status.pending

class Finding(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    finding_id: str
    category: FindingCategory
    severity: Severity
    title: str = Field(min_length=4, max_length=180)
    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    evidence: str = Field(min_length=1, max_length=4000)
    explanation: str = Field(min_length=8, max_length=3000)
    conditions: str = Field(default="", max_length=1500)
    recommended_fix: str = Field(min_length=3, max_length=3000)
    confidence: float = Field(ge=0, le=1)
    specialist: Role
    checker_status: str = "candidate"
    checker_feedback: str = ""

class AgentResult(BaseModel):
    role: Role
    task_id: str
    status: Status
    findings: list[Finding] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    tool_call_count: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_input_tokens: int | None = None
    elapsed_seconds: float = 0
    retries: int = 0

class Handoff(BaseModel):
    message_id: str
    sender: Role
    recipient: Role
    task_id: str
    content: dict[str, Any]
    created_at: datetime = Field(default_factory=utcnow)

class CheckerDecision(BaseModel):
    finding_id: str
    decision: str
    reason: str = ""
    corrected_finding: Finding | None = None

class FinalReport(BaseModel):
    run_id: str
    status: Status
    task: str
    summary: str
    accepted_findings: list[Finding]
    rejected_findings: list[dict[str, Any]]
    agent_results: list[AgentResult]
    incomplete_reviews: list[str]
    metrics: dict[str, Any]
    limits_reached: list[str]
    safety_warnings: list[str]
    trace_file: str
    created_at: datetime = Field(default_factory=utcnow)
