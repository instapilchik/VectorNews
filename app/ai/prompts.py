from typing import Dict, List, Optional
from datetime import datetime


class PromptTemplates:
    """Шаблоны промптов для разных типов задач"""

    # Базовый системный промпт с ограничениями
    BASE_SYSTEM_PROMPT = """Ты специализированный новостной аналитик для трейдеров и инвесторов.

СТРОГИЕ ОГРАНИЧЕНИЯ:
1. Работай ТОЛЬКО с новостной информацией из предоставленной базы данных
2. НЕ давай торговых советов или инвестиционных рекомендаций
3. НЕ обсуждай темы, не связанные с финансовыми новостями и рынками
4. НЕ генерируй информацию, которой нет в доступных новостях
5. НЕ предсказывай будущие движения цен или курсов

ТВОЯ ЗАДАЧА:
- Анализировать и интерпретировать новостную информацию
- Структурировать данные для удобного восприятия
- Объяснять связи между событиями и рынками
- Предоставлять контекст для понимания новостей

СТИЛЬ ОБЩЕНИЯ:
- Профессиональный, но доступный
- Фактологичный и объективный
- Краткий, но информативный
- Избегай излишних эмоций и сенсационности

При ответе всегда ссылайся на источники новостей и время публикации."""

    # Промпт для персонализированного агента
    PERSONALIZED_AGENT_PROMPT = """Ты персонализированный новостной аналитик "{agent_name}".

ПЕРСОНАЛЬНЫЕ НАСТРОЙКИ:
{agent_config}

ТВОЯ РОЛЬ:
- Фокусируйся на интересах пользователя согласно настройкам
- Адаптируй стиль общения под предпочтения пользователя
- Приоритизируй информацию согласно заданным секторам и темам
- Поддерживай контекст предыдущих обсуждений

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
У тебя есть доступ к инструментам для поиска новостей, анализа трендов и получения данных дашбордов. Используй их для предоставления актуальной и релевантной информации.

{base_restrictions}"""

    # Промпт для генерации дашбордов
    DASHBOARD_GENERATION_PROMPT = """Ты эксперт по созданию аналитических дашбордов для трейдеров.

ЗАДАЧА: Создать {dashboard_type} на основе предоставленных новостей.

ТРЕБОВАНИЯ К ДАШБОРДУ:
1. Структурированная подача информации
2. Выделение ключевых событий и трендов
3. Группировка по важности и темам
4. Краткие, но содержательные выводы
5. Указание источников и времени

ФОРМАТ ОТВЕТА:
- Заголовок дашборда
- Ключевые события (3-5 пунктов)
- Анализ трендов
- Важные цифры и метрики
- Краткие выводы

Основывайся ТОЛЬКО на предоставленных новостях. Не добавляй информацию из других источников."""

    # Промпт для персонализации контента
    PERSONALIZATION_PROMPT = """Ты специалист по персонализации новостного контента.

ЗАДАЧА: Адаптировать предоставленный контент под настройки пользователя.

ПОЛЬЗОВАТЕЛЬСКИЕ ПРЕДПОЧТЕНИЯ:
{user_preferences}

ПРИНЦИПЫ ПЕРСОНАЛИЗАЦИИ:
1. Фильтруй контент по интересующим секторам
2. Адаптируй стиль подачи под предпочтения пользователя
3. Выделяй наиболее релевантную информацию
4. Убирай или минимизируй нерелевантные темы
5. Сохраняй структуру и основную информацию

НЕ ДОБАВЛЯЙ новую информацию - только адаптируй существующую под пользователя.

Отвечай в том же формате, что и исходный контент, но персонализированно."""


class PromptBuilder:
    """Класс для построения промптов под конкретные задачи"""

    def __init__(self):
        self.templates = PromptTemplates()

    def build_agent_prompt(
            self,
            agent_name: str,
            agent_config: Dict,
            task_context: Optional[str] = None
    ) -> str:
        """Построение промпта для персонализированного агента"""

        # Форматируем конфигурацию агента
        config_text = self._format_agent_config(agent_config)

        prompt = self.templates.PERSONALIZED_AGENT_PROMPT.format(
            agent_name=agent_name,
            agent_config=config_text,
            base_restrictions=self.templates.BASE_SYSTEM_PROMPT
        )

        if task_context:
            prompt += f"\n\nКОНТЕКСТ ЗАДАЧИ:\n{task_context}"

        return prompt

    def build_dashboard_prompt(self, dashboard_type: str, context: Optional[str] = None) -> str:
        """Построение промпта для генерации дашборда"""

        dashboard_types = {
            "daily_summary": "ежедневную сводку новостей",
            "trending_topics": "обзор трендовых тем",
            "sectoral_overview": "секторальный обзор рынков"
        }

        dashboard_name = dashboard_types.get(dashboard_type, "новостной дашборд")

        prompt = self.templates.DASHBOARD_GENERATION_PROMPT.format(
            dashboard_type=dashboard_name
        )

        if context:
            prompt += f"\n\nДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ:\n{context}"

        return prompt

    def build_personalization_prompt(self, user_preferences: Dict) -> str:
        """Построение промпта для персонализации"""

        prefs_text = self._format_user_preferences(user_preferences)

        return self.templates.PERSONALIZATION_PROMPT.format(
            user_preferences=prefs_text
        )

    def build_chat_system_prompt(
            self,
            agent_config: Dict,
            conversation_context: Optional[List[Dict]] = None
    ) -> str:
        """Построение системного промпта для чата"""

        base_prompt = self.templates.BASE_SYSTEM_PROMPT

        # Добавляем контекст агента
        if agent_config:
            config_text = self._format_agent_config(agent_config)
            base_prompt += f"\n\nНАСТРОЙКИ АГЕНТА:\n{config_text}"

        # Добавляем контекст разговора
        if conversation_context:
            context_summary = self._summarize_conversation_context(conversation_context)
            base_prompt += f"\n\nКОНТЕКСТ РАЗГОВОРА:\n{context_summary}"

        base_prompt += f"\n\nТЕКУЩЕЕ ВРЕМЯ: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC"

        return base_prompt

    def _format_agent_config(self, config: Dict) -> str:
        """Форматирование конфигурации агента в текст"""

        lines = []

        if "focus_sectors" in config:
            sectors = ", ".join(config["focus_sectors"])
            lines.append(f"Основные секторы интереса: {sectors}")

        if "style" in config:
            style_map = {
                "brief": "краткий и по существу",
                "detailed": "подробный и аналитический",
                "casual": "неформальный и доступный",
                "technical": "технический и профессиональный"
            }
            style = style_map.get(config["style"], config["style"])
            lines.append(f"Стиль общения: {style}")

        if "time_preference" in config:
            time_map = {
                "realtime": "акцент на последние новости",
                "daily": "ежедневные сводки",
                "weekly": "еженедельная аналитика"
            }
            time_pref = time_map.get(config["time_preference"], config["time_preference"])
            lines.append(f"Временные предпочтения: {time_pref}")

        if "watchlist" in config and config["watchlist"]:
            watchlist = ", ".join(config["watchlist"])
            lines.append(f"Отслеживаемые активы: {watchlist}")

        return "\n".join(lines) if lines else "Стандартные настройки"

    def _format_user_preferences(self, preferences: Dict) -> str:
        """Форматирование предпочтений пользователя в текст"""

        lines = []

        if "sectors" in preferences:
            lines.append(f"Интересующие секторы: {', '.join(preferences['sectors'])}")

        if "style" in preferences:
            lines.append(f"Предпочитаемый стиль: {preferences['style']}")

        if "detail_level" in preferences:
            lines.append(f"Уровень детализации: {preferences['detail_level']}")

        if "exclude_topics" in preferences:
            lines.append(f"Исключить темы: {', '.join(preferences['exclude_topics'])}")

        return "\n".join(lines) if lines else "Стандартные предпочтения"

    def _summarize_conversation_context(self, context: List[Dict]) -> str:
        """Суммирование контекста разговора"""

        if not context:
            return "Новая беседа"

        recent_topics = []
        for msg in context[-5:]:  # Последние 5 сообщений
            if msg.get("role") == "user" and len(msg.get("content", "")) > 10:
                # Простое извлечение темы (первые 50 символов)
                topic = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                recent_topics.append(topic)

        if recent_topics:
            return f"Недавние темы обсуждения: {'; '.join(recent_topics[-3:])}"
        else:
            return "Продолжение беседы"


# Singleton instance
prompt_builder = PromptBuilder()