"""
Pydantic Schemas

Request/response models and guardrail data structures shared across the
application. These define the public contract for the API and the internal
contract between the orchestrator and the guardrail checks.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMRequest(BaseModel):
    """Incoming request to the guarded completions endpoint."""

    prompt: str = Field(..., description="User prompt to send to the LLM")
    user_id: str = Field(..., description="Unique identifier for the requesting user")
    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider to use for the completion",
    )
    model: Optional[str] = Field(
        default=None, description="Specific model to use (provider default if omitted)"
    )
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum number of tokens to generate"
    )
    temperature: Optional[float] = Field(
        default=None, description="Sampling temperature for the completion"
    )


class GuardrailViolation(BaseModel):
    """A single guardrail violation detected during a check."""

    guardrail_type: str = Field(..., description="Which guardrail produced the violation")
    severity: str = Field(..., description="Severity level, e.g. low/medium/high/critical")
    message: str = Field(..., description="Human-readable description of the violation")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Structured context about the violation"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the violation was detected"
    )


class GuardrailCheckResult(BaseModel):
    """Aggregated result of running a set of guardrail checks."""

    passed: bool = Field(..., description="True if no blocking violations were found")
    violations: List[GuardrailViolation] = Field(
        default_factory=list, description="All violations detected during the check"
    )
    modified_content: Optional[str] = Field(
        default=None, description="Sanitized content (e.g. redacted) when applicable"
    )
    processing_time_ms: float = Field(
        default=0.0, description="Time taken to run the checks, in milliseconds"
    )


class LLMResponse(BaseModel):
    """Response returned from the guarded completions endpoint."""

    # `model_used` would otherwise collide with Pydantic's protected `model_`
    # namespace and emit a UserWarning; this opts out of that protection.
    model_config = ConfigDict(protected_namespaces=())

    completion: Optional[str] = Field(
        default=None, description="Generated completion, or None if blocked"
    )
    blocked: bool = Field(..., description="True if the request was blocked by guardrails")
    input_guardrails: GuardrailCheckResult = Field(
        ..., description="Result of input guardrail checks"
    )
    output_guardrails: Optional[GuardrailCheckResult] = Field(
        default=None, description="Result of output guardrail checks, if run"
    )
    total_processing_time_ms: float = Field(
        default=0.0, description="End-to-end processing time, in milliseconds"
    )
    model_used: Optional[str] = Field(
        default=None, description="Model used to generate the completion"
    )
    tokens_used: int = Field(default=0, description="Approximate tokens used")
    request_id: str = Field(..., description="Unique identifier for this request")


class HealthCheckResponse(BaseModel):
    """Health check payload describing service and dependency status."""

    status: str = Field(..., description="Overall service status")
    version: str = Field(..., description="API version")
    guardrails_enabled: Dict[str, bool] = Field(
        ..., description="Map of guardrail name to enabled flag"
    )
    dependencies: Dict[str, bool] = Field(
        ..., description="Map of dependency name to health flag"
    )
