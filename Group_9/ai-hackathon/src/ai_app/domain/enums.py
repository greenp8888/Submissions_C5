from __future__ import annotations

from enum import Enum


class Depth(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class ResearchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


class SourceType(str, Enum):
    WEB = "web"
    NEWS = "news"
    ACADEMIC = "academic"
    REPORT = "report"
    API = "api"
    PDF = "pdf"
    LOCAL_UPLOAD = "local_upload"


class ConfidenceLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InsightType(str, Enum):
    TREND = "trend"
    CROSS_DOMAIN = "cross_domain"
    HYPOTHESIS = "hypothesis"
    GAP = "gap"

