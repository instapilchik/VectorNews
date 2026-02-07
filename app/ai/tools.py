from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from app.services.news_service import NewsService
import logging

logger = logging.getLogger(__name__)


class AITools:
    """Набор инструментов для ИИ-агентов"""

    def __init__(self):
        self.news_service = NewsService()

    def get_tools_definition(self) -> List[Dict]:
        """Определение tools в формате OpenAI Function Calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_news",
                    "description": "Поиск новостей в базе данных по запросу и фильтрам",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Поисковый запрос (ключевые слова)"
                            },
                            "time_range": {
                                "type": "string",
                                "enum": ["1h", "6h", "1d", "3d", "1w"],
                                "description": "Временной диапазон для поиска",
                                "default": "1d"
                            },
                            "sectors": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["currency", "commodities", "stocks", "crypto", "geopolitics", "macro"]
                                },
                                "description": "Фильтр по секторам экономики"
                            },
                            "importance_threshold": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Минимальный уровень важности новости",
                                "default": 0.3
                            },
                            "limit": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 50,
                                "description": "Максимальное количество результатов",
                                "default": 20
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_dashboard_data",
                    "description": "Получение данных для дашбордов",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dashboard_type": {
                                "type": "string",
                                "enum": ["daily_summary", "trending_topics", "sectoral_overview"],
                                "description": "Тип дашборда"
                            },
                            "sector": {
                                "type": "string",
                                "enum": ["currency", "commodities", "stocks", "crypto", "geopolitics", "macro"],
                                "description": "Сектор для фильтрации (опционально)"
                            },
                            "time_range": {
                                "type": "string",
                                "enum": ["1h", "6h", "1d", "3d", "1w"],
                                "description": "Временной диапазон",
                                "default": "1d"
                            },
                            "fresh_data": {
                                "type": "boolean",
                                "description": "Требовать свежие данные (игнорировать кеш)",
                                "default": False
                            }
                        },
                        "required": ["dashboard_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_trend",
                    "description": "Анализ трендов по ключевому слову или теме",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "Ключевое слово или тема для анализа"
                            },
                            "time_range": {
                                "type": "string",
                                "enum": ["1d", "3d", "1w", "2w", "1m"],
                                "description": "Период для анализа тренда",
                                "default": "1w"
                            },
                            "include_sentiment": {
                                "type": "boolean",
                                "description": "Включить анализ настроений",
                                "default": True
                            }
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_user_context",
                    "description": "Получение контекста пользователя из предыдущих сессий",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "ID пользователя"
                            },
                            "lookback_hours": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 168,
                                "description": "Количество часов назад для поиска контекста",
                                "default": 24
                            },
                            "include_preferences": {
                                "type": "boolean",
                                "description": "Включить пользовательские предпочтения",
                                "default": True
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            }
        ]

    async def search_news(
            self,
            query: str,
            time_range: str = "1d",
            sectors: Optional[List[str]] = None,
            importance_threshold: float = 0.3,
            limit: int = 20
    ) -> Dict[str, Any]:
        """Поиск новостей в базе данных"""
        try:
            news_items = await self.news_service.search_news(
                query=query,
                time_range=time_range,
                sectors=sectors,
                limit=limit
            )

            # Фильтруем по важности
            filtered_news = [
                item for item in news_items
                if (item.importance_score or 0) >= importance_threshold
            ]

            result = {
                "query": query,
                "time_range": time_range,
                "total_found": len(news_items),
                "after_importance_filter": len(filtered_news),
                "news_items": [
                    {
                        "id": item.id,
                        "source": item.source_channel,
                        "text": item.original_text[:300] + "..." if len(
                            item.original_text) > 300 else item.original_text,
                        "published_at": item.published_at.isoformat(),
                        "importance_score": item.importance_score,
                        "sector": item.sector,
                        "category": item.category or item.estimated_category,
                        "views": item.views_count,
                        "tg_link": item.tg_link
                    }
                    for item in filtered_news[:limit]
                ]
            }

            logger.info(f"Search '{query}' returned {len(filtered_news)} results")
            return result

        except Exception as e:
            logger.error(f"Error in search_news: {e}")
            return {"error": str(e), "news_items": []}

    async def get_dashboard_data(
            self,
            dashboard_type: str,
            sector: Optional[str] = None,
            time_range: str = "1d",
            fresh_data: bool = False
    ) -> Dict[str, Any]:
        """Получение данных для дашбордов"""
        try:
            if dashboard_type == "daily_summary":
                data = await self._get_daily_summary_data(time_range)
            elif dashboard_type == "trending_topics":
                data = await self._get_trending_topics_data(time_range)
            elif dashboard_type == "sectoral_overview":
                data = await self._get_sectoral_overview_data(sector, time_range)
            else:
                raise ValueError(f"Unknown dashboard type: {dashboard_type}")

            return data

        except Exception as e:
            logger.error(f"Error in get_dashboard_data: {e}")
            return {"error": str(e), "data": {}}

    async def analyze_trend(
            self,
            keyword: str,
            time_range: str = "1w",
            include_sentiment: bool = True
    ) -> Dict[str, Any]:
        """Анализ трендов по ключевому слову"""
        try:
            # Определяем временные интервалы для анализа
            time_delta = {
                "1d": timedelta(days=1),
                "3d": timedelta(days=3),
                "1w": timedelta(weeks=1),
                "2w": timedelta(weeks=2),
                "1m": timedelta(days=30)
            }.get(time_range, timedelta(weeks=1))

            since_date = datetime.utcnow() - time_delta

            # Поиск новостей по ключевому слову
            news_items = await self.news_service.search_news(
                query=keyword,
                time_range=time_range,
                limit=100
            )

            if not news_items:
                return {
                    "keyword": keyword,
                    "time_range": time_range,
                    "total_mentions": 0,
                    "trend_analysis": "Недостаточно данных для анализа тренда"
                }

            # Группируем по дням
            daily_counts = {}
            sentiment_data = {"positive": 0, "negative": 0, "neutral": 0}

            for item in news_items:
                day_key = item.published_at.date().isoformat()
                daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

                # Простой анализ настроений (заглушка)
                if include_sentiment and item.sentiment:
                    sentiment_data[item.sentiment] = sentiment_data.get(item.sentiment, 0) + 1

            # Вычисляем тренд
            dates = sorted(daily_counts.keys())
            if len(dates) >= 2:
                recent_avg = sum(daily_counts[d] for d in dates[-3:]) / min(3, len(dates))
                early_avg = sum(daily_counts[d] for d in dates[:3]) / min(3, len(dates))
                trend_direction = "возрастающий" if recent_avg > early_avg else "убывающий" if recent_avg < early_avg else "стабильный"
            else:
                trend_direction = "недостаточно данных"

            result = {
                "keyword": keyword,
                "time_range": time_range,
                "total_mentions": len(news_items),
                "daily_distribution": daily_counts,
                "trend_direction": trend_direction,
                "most_active_sources": self._get_top_sources(news_items),
            }

            if include_sentiment:
                result["sentiment_distribution"] = sentiment_data

            logger.info(f"Trend analysis for '{keyword}': {len(news_items)} mentions, {trend_direction}")
            return result

        except Exception as e:
            logger.error(f"Error in analyze_trend: {e}")
            return {"error": str(e), "keyword": keyword}

    async def get_user_context(
            self,
            user_id: int,
            lookback_hours: int = 24,
            include_preferences: bool = True
    ) -> Dict[str, Any]:
        """Получение контекста пользователя на основе настроек агента"""
        try:
            from app.services.agent_settings_service import agent_settings_service
            settings = await agent_settings_service.get_settings(str(user_id))

            context = {
                "user_id": user_id,
                "agent_name": settings.agent_name,
                "focus_interests": settings.focus_interests,
                "information_style": settings.information_style.value,
                "analysis_depth": settings.analysis_depth.value,
            }

            return context

        except Exception as e:
            logger.error(f"Error in get_user_context: {e}")
            return {"error": str(e), "user_id": user_id}

    # Вспомогательные методы

    async def _get_daily_summary_data(self, time_range: str) -> Dict:
        """Данные для дневной сводки"""
        # Получаем топ новости за период
        top_news = await self.news_service.search_news(
            time_range=time_range,
            limit=5
        )

        return {
            "type": "daily_summary",
            "time_range": time_range,
            "top_stories": [
                {
                    "text": item.original_text[:200] + "...",
                    "source": item.source_channel,
                    "importance": item.importance_score,
                    "published_at": item.published_at.isoformat()
                }
                for item in top_news
            ]
        }

    async def _get_trending_topics_data(self, time_range: str) -> Dict:
        """Данные для трендовых тем"""
        # Простой анализ трендов по категориям
        news_items = await self.news_service.search_news(
            time_range=time_range,
            limit=100
        )

        category_counts = {}
        for item in news_items:
            cat = item.category or item.estimated_category or "общее"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        trending = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "type": "trending_topics",
            "time_range": time_range,
            "trending_categories": [
                {"category": cat, "mentions": count}
                for cat, count in trending
            ]
        }

    async def _get_sectoral_overview_data(self, sector: Optional[str], time_range: str) -> Dict:
        """Данные для секторального обзора"""
        sectors_to_analyze = [sector] if sector else ["currency", "commodities", "crypto", "geopolitics"]

        sectoral_data = {}

        for sec in sectors_to_analyze:
            sector_news = await self.news_service.search_news(
                time_range=time_range,
                sectors=[sec],
                limit=20
            )

            sectoral_data[sec] = {
                "news_count": len(sector_news),
                "avg_importance": sum(item.importance_score or 0 for item in sector_news) / len(
                    sector_news) if sector_news else 0,
                "top_story": {
                    "text": sector_news[0].original_text[:150] + "...",
                    "source": sector_news[0].source_channel
                } if sector_news else None
            }

        return {
            "type": "sectoral_overview",
            "time_range": time_range,
            "sectors": sectoral_data
        }

    def _get_top_sources(self, news_items: List) -> List[Dict]:
        """Получение топ источников по активности"""
        source_counts = {}
        for item in news_items:
            source = item.source_channel
            source_counts[source] = source_counts.get(source, 0) + 1

        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{"source": source, "count": count} for source, count in top_sources]



# Singleton instance
ai_tools = AITools()