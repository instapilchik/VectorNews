from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class InformationStyle(str, Enum):
    SUMMARIES = "краткие сводки"
    DETAILED = "развернутые анализы"
    FACTS_ONLY = "только факты"


class CommunicationTone(str, Enum):
    NEUTRAL = "нейтральный"
    EMOTIONAL = "с эмоциями"
    TECHNICAL = "технический"


class AnalysisDepth(str, Enum):
    SUPERFICIAL = "поверхностно"
    DETAILED = "детально"
    EXPERT = "экспертный уровень"


class AgentSettingsSchema(BaseModel):
    agent_name: str = Field(default="Аналитик", description="Имя агента")
    focus_interests: List[str] = Field(default_factory=list, description="Фокус интересов (категории новостей)")

    information_style: InformationStyle = Field(default=InformationStyle.SUMMARIES)
    communication_tone: CommunicationTone = Field(default=CommunicationTone.NEUTRAL)
    analysis_depth: AnalysisDepth = Field(default=AnalysisDepth.DETAILED)

    historical_context_days: int = Field(default=7, ge=1, le=30, description="Глубина исторического контекста в днях")

    class Config:
        use_enum_values = True

