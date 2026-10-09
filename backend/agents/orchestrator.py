"""Agent Orchestrator — coordinates all agents and prioritizes insights."""
from datetime import datetime
from .spending_analyst import SpendingAnalystAgent
from .budget_guardian import BudgetGuardianAgent
from .savings_coach import SavingsCoachAgent
from .investment_advisor import InvestmentAdvisorAgent
from .anomaly_detector import AnomalyDetectorAgent
from .bill_tracker import BillTrackerAgent


SEVERITY_PRIORITY = {"critical": 0, "warning": 1, "success": 2, "info": 3}


class AgentOrchestrator:
    """Runs all financial AI agents and returns prioritized insights."""

    def __init__(self):
        self.agents = [
            SpendingAnalystAgent(),
            BudgetGuardianAgent(),
            SavingsCoachAgent(),
            InvestmentAdvisorAgent(),
            AnomalyDetectorAgent(),
            BillTrackerAgent(),
        ]

    def run_all(self, transactions_df, user_context):
        """Execute all agents and return prioritized insights."""
        all_insights = []
        agent_statuses = []

        for agent in self.agents:
            insights = agent.run(transactions_df, user_context)
            all_insights.extend(insights)
            agent_statuses.append(agent.get_status())

        # Sort: critical first, then warning, success, info
        all_insights.sort(
            key=lambda x: (
                SEVERITY_PRIORITY.get(x["severity"], 99),
                x["timestamp"],
            )
        )

        return {
            "insights": all_insights,
            "agent_statuses": agent_statuses,
            "total_insights": len(all_insights),
            "critical_count": sum(1 for i in all_insights if i["severity"] == "critical"),
            "warning_count": sum(1 for i in all_insights if i["severity"] == "warning"),
            "success_count": sum(1 for i in all_insights if i["severity"] == "success"),
            "generated_at": datetime.now().isoformat(),
        }

    def get_agent_statuses(self):
        return [agent.get_status() for agent in self.agents]
