"""Base Agent class — all financial agents inherit from this."""
from abc import ABC, abstractmethod
from datetime import datetime


class BaseAgent(ABC):
    """Abstract base class for AI financial agents."""

    def __init__(self):
        self.name = ""
        self.role = ""
        self.avatar = ""
        self.color = ""
        self.last_run = None
        self.status = "idle"

    def run(self, transactions_df, user_context):
        """Execute the full think -> analyze pipeline."""
        self.status = "thinking"
        self.last_run = datetime.now().isoformat()
        try:
            thought_data = self._think(transactions_df, user_context)
            insights = self._analyze(thought_data, user_context)
            self.status = "done"
            return insights
        except Exception as e:
            self.status = "error"
            return [self._create_insight(
                "Agent Error",
                f"{self.name} encountered an issue: {str(e)}",
                "info", "system"
            )]

    @abstractmethod
    def _think(self, df, ctx):
        """Pre-process data. Return a dict of computed metrics."""

    @abstractmethod
    def _analyze(self, data, ctx):
        """Generate insights from thought data. Return list of insight dicts."""

    def get_status(self):
        return {
            "name": self.name,
            "role": self.role,
            "avatar": self.avatar,
            "color": self.color,
            "status": self.status,
            "last_run": self.last_run,
        }

    def _create_insight(self, title, message, severity, category, data=None):
        return {
            "agent": self.name,
            "agent_avatar": self.avatar,
            "agent_color": self.color,
            "title": title,
            "message": message,
            "severity": severity,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
        }
