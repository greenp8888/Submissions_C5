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


class SourceChannel(str, Enum):
    LOCAL_RAG = "local_rag"
    WEB = "web"
    ARXIV = "arxiv"


class DatePreset(str, Enum):
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_1_YEAR = "last_1_year"
    LAST_5_YEARS = "last_5_years"
    ALL_TIME = "all_time"


class RunMode(str, Enum):
    SINGLE = "single"
    BATCH = "batch"
