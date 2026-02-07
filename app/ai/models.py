from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Типы задач для ИИ"""
    CHAT = "chat"
    DASHBOARD_GENERATION = "dashboard_generation"
    PERSONALIZATION = "personalization"
    NEWS_CLASSIFICATION = "news_classification"
    FILTERING = "filtering"
    ANALYSIS = "analysis"


class ComplexityLevel(Enum):
    """Уровни сложности задач"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    HIGH = "high"


# Конфигурация моделей
MODEL_CONFIG = {
    # Дешевые модели (для персонализации и простых задач)
    "light_models": {
        # "google/gemini-2.0-flash-exp": {
        #     "cost_per_1k_input": 0.000075,
        #     "cost_per_1k_output": 0.0003,
        #     "max_tokens": 8192,
        #     "use_cases": [TaskType.PERSONALIZATION, TaskType.FILTERING, TaskType.CHAT],
        #     "complexity": [ComplexityLevel.SIMPLE],
        #     "speed": "very_fast"
        # },
        # "openai/gpt-3.5-turbo": {
        #     "cost_per_1k_input": 0.0005,
        #     "cost_per_1k_output": 0.0015,
        #     "max_tokens": 4096,
        #     "use_cases": [TaskType.CHAT, TaskType.PERSONALIZATION],
        #     "complexity": [ComplexityLevel.SIMPLE, ComplexityLevel.MEDIUM],
        #     "speed": "fast"
        # },
        "google/gemini-3-flash-preview": {
            "cost_per_1k_input": 0.0001,
            "cost_per_1k_output": 0.0004,
            "max_tokens": 4096,
            "use_cases": [TaskType.PERSONALIZATION, TaskType.FILTERING, TaskType.NEWS_CLASSIFICATION],
            "complexity": [ComplexityLevel.SIMPLE],
            "speed": "very_fast"
        }

    },

    # Мощные модели (для дашбордов и сложной аналитики)
    "heavy_models": {
        "anthropic/claude-sonnet-4.5": {
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
            "max_tokens": 200000,
            "use_cases": [TaskType.DASHBOARD_GENERATION, TaskType.ANALYSIS, TaskType.CHAT],
            "complexity": [ComplexityLevel.MEDIUM, ComplexityLevel.HIGH],
            "speed": "medium"
        },
        # "openai/gpt-4": {
        #     "cost_per_1k_input": 0.03,
        #     "cost_per_1k_output": 0.06,
        #     "max_tokens": 8192,
        #     "use_cases": [TaskType.DASHBOARD_GENERATION, TaskType.ANALYSIS],
        #     "complexity": [ComplexityLevel.HIGH],
        #     "speed": "slow"
        # },
        # "anthropic/claude-3-opus": {
        #     "cost_per_1k_input": 0.015,
        #     "cost_per_1k_output": 0.075,
        #     "max_tokens": 4096,
        #     "use_cases": [TaskType.DASHBOARD_GENERATION, TaskType.ANALYSIS],
        #     "complexity": [ComplexityLevel.HIGH],
        #     "speed": "slow"
        # }
    }
}


class ModelSelector:
    """Класс для умного выбора моделей"""

    def __init__(self):
        self.all_models = {**MODEL_CONFIG["light_models"], **MODEL_CONFIG["heavy_models"]}

    def select_model(
            self,
            task_type: TaskType,
            complexity: ComplexityLevel = ComplexityLevel.SIMPLE,
            prefer_speed: bool = False,
            prefer_cost: bool = True,
            max_budget_per_1k: float = 0.02
    ) -> str:
        """
        Выбор оптимальной модели для задачи

        Args:
            task_type: Тип задачи
            complexity: Сложность задачи
            prefer_speed: Приоритет скорости
            prefer_cost: Приоритет стоимости
            max_budget_per_1k: Максимальный бюджет на 1k токенов

        Returns:
            Название модели для OpenRouter
        """

        suitable_models = []

        for model_name, config in self.all_models.items():
            # Проверяем совместимость с типом задачи
            if task_type not in config["use_cases"]:
                continue

            # Проверяем совместимость со сложностью
            if complexity not in config["complexity"]:
                continue

            # Проверяем бюджет
            max_cost = max(config["cost_per_1k_input"], config["cost_per_1k_output"])
            if max_cost > max_budget_per_1k:
                continue

            suitable_models.append((model_name, config))

        if not suitable_models:
            logger.warning(f"No suitable models found for {task_type}/{complexity}, using fallback")
            return self._get_fallback_model(task_type)

        # Сортируем по приоритетам
        if prefer_speed:
            speed_priority = {"very_fast": 0, "fast": 1, "medium": 2, "slow": 3}
            suitable_models.sort(key=lambda x: speed_priority.get(x[1]["speed"], 4))
        elif prefer_cost:
            suitable_models.sort(key=lambda x: x[1]["cost_per_1k_output"])

        selected_model = suitable_models[0][0]
        logger.info(f"Selected model '{selected_model}' for {task_type.value}/{complexity.value}")

        return selected_model

    def _get_fallback_model(self, task_type: TaskType) -> str:
        """Fallback модель по умолчанию"""
        fallback_map = {
            TaskType.CHAT: "anthropic/claude-sonnet-4.5",
            TaskType.DASHBOARD_GENERATION: "anthropic/claude-sonnet-4.5",
            TaskType.PERSONALIZATION: "google/gemini-3-flash-preview",
            TaskType.NEWS_CLASSIFICATION: "google/gemini-3-flash-preview",
            TaskType.FILTERING: "google/gemini-3-flash-preview",
            TaskType.ANALYSIS: "anthropic/claude-sonnet-4.5"
        }

        return fallback_map.get(task_type, "anthropic/claude-sonnet-4.5")

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Получение информации о модели"""
        return self.all_models.get(model_name)

    def calculate_cost(
            self,
            model_name: str,
            input_tokens: int,
            output_tokens: int
    ) -> Dict[str, float]:
        """Расчет стоимости использования модели"""
        model_info = self.get_model_info(model_name)
        if not model_info:
            return {"input": 0, "output": 0, "total": 0}

        input_cost = (input_tokens / 1000) * model_info["cost_per_1k_input"]
        output_cost = (output_tokens / 1000) * model_info["cost_per_1k_output"]
        total_cost = input_cost + output_cost

        return {
            "input": round(input_cost, 6),
            "output": round(output_cost, 6),
            "total": round(total_cost, 6)
        }


# Singleton instance
model_selector = ModelSelector()


# Convenience functions
def select_model_for_chat(complexity: ComplexityLevel = ComplexityLevel.SIMPLE) -> str:
    """Быстрый выбор модели для чата"""
    return model_selector.select_model(TaskType.CHAT, complexity, prefer_speed=True)


def select_model_for_dashboard() -> str:
    """Быстрый выбор модели для генерации дашбордов"""
    return model_selector.select_model(
        TaskType.DASHBOARD_GENERATION,
        ComplexityLevel.HIGH,
        prefer_cost=False
    )


def select_model_for_classification() -> str:
    """Быстрый выбор модели для классификации новостей"""
    return model_selector.select_model(
        TaskType.NEWS_CLASSIFICATION,
        ComplexityLevel.SIMPLE,
        prefer_cost=True
    )


def select_model_for_personalization() -> str:
    """Быстрый выбор модели для персонализации"""
    return model_selector.select_model(
        TaskType.PERSONALIZATION,
        ComplexityLevel.SIMPLE,
        prefer_cost=True,
        prefer_speed=True
    )