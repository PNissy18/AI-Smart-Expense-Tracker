"""Budget Guardian Agent — budget monitoring, overspend alerts, projections."""
import pandas as pd
from datetime import datetime
from .base_agent import BaseAgent


class BudgetGuardianAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.name = "Budget Guardian"
        self.role = "Budget monitoring & overspend alerts"
        self.avatar = "shield"
        self.color = "#d63031"

    def _think(self, df, ctx):
        budgets = ctx.get('budgets', [])
        if not budgets:
            return {"no_budgets": True, "empty": df.empty}

        now = pd.Timestamp.now()
        day_of_month = now.day
        days_in_month = now.days_in_month
        days_remaining = days_in_month - day_of_month
        month_progress = day_of_month / days_in_month

        current_month_df = df[df['date'].dt.to_period('M') == now.to_period('M')] if not df.empty else pd.DataFrame()

        budget_status = []
        for b in budgets:
            cat = b['category']
            limit = b['monthly_limit']
            spent = float(current_month_df[current_month_df['category'] == cat]['amount'].sum()) if not current_month_df.empty else 0
            pct = round((spent / limit) * 100, 1) if limit > 0 else 0
            projected = round(spent / month_progress, 2) if month_progress > 0 else spent

            daily_rate = spent / max(day_of_month, 1)
            days_until_exhausted = round((limit - spent) / daily_rate) if daily_rate > 0 and spent < limit else 0
            safe_daily_budget = round((limit - spent) / max(days_remaining, 1), 2) if days_remaining > 0 else 0

            budget_status.append({
                "category": cat,
                "limit": limit,
                "spent": round(spent, 2),
                "remaining": round(limit - spent, 2),
                "percentage": pct,
                "projected_eom": projected,
                "will_exceed": projected > limit,
                "status": "over" if pct > 100 else "warning" if pct > 80 else "good",
                "daily_rate": round(daily_rate, 2),
                "days_until_exhausted": days_until_exhausted,
                "safe_daily_budget": safe_daily_budget,
            })

        # Categories without budgets
        if not df.empty:
            all_cats = set(df['category'].unique())
            budgeted_cats = {b['category'] for b in budgets}
            unbudgeted = all_cats - budgeted_cats
            unbudgeted_spending = {}
            for cat in unbudgeted:
                amt = float(current_month_df[current_month_df['category'] == cat]['amount'].sum()) if not current_month_df.empty else 0
                if amt > 0:
                    unbudgeted_spending[cat] = round(amt, 2)
        else:
            unbudgeted_spending = {}

        return {
            "no_budgets": False,
            "empty": df.empty,
            "budget_status": budget_status,
            "days_remaining": days_remaining,
            "month_progress": round(month_progress * 100, 1),
            "unbudgeted_spending": unbudgeted_spending,
        }

    def _analyze(self, data, ctx):
        if data.get("empty"):
            return []

        if data.get("no_budgets"):
            return [self._create_insight(
                "No Budgets Set",
                "Set category budgets to get spending alerts and stay in control. Head to the Dashboard to create budgets.",
                "info", "budget"
            )]

        insights = []

        for bs in data["budget_status"]:
            if bs["status"] == "over":
                excess = abs(bs['remaining'])
                daily_cut = round(excess / max(data['days_remaining'], 1), 2)
                insights.append(self._create_insight(
                    f"{bs['category']} Budget Exceeded",
                    f"Over by Rs. {excess:,.0f} ({bs['percentage']}% of Rs. {bs['limit']:,.0f}). "
                    f"Reduce other spending by Rs. {daily_cut:,.0f}/day for {data['days_remaining']} days to recover.",
                    "critical", "budget",
                    bs
                ))
            elif bs["status"] == "warning":
                insights.append(self._create_insight(
                    f"{bs['category']} Budget Alert",
                    f"{bs['category']} is at {bs['percentage']}% with {data['days_remaining']} days left. "
                    f"Keep daily {bs['category']} spending under Rs. {bs['safe_daily_budget']:,.0f} to stay on track.",
                    "warning", "budget",
                    bs
                ))
            elif bs["will_exceed"]:
                insights.append(self._create_insight(
                    f"{bs['category']} Projected to Exceed",
                    f"At your current pace, {bs['category']} spending will reach Rs. {bs['projected_eom']:,.0f} "
                    f"(budget: Rs. {bs['limit']:,.0f}). Slow down to stay on track.",
                    "warning", "budget",
                    bs
                ))

        # Good budgets
        good_count = sum(1 for bs in data["budget_status"] if bs["status"] == "good" and not bs["will_exceed"])
        if good_count > 0:
            insights.append(self._create_insight(
                f"{good_count} Budget(s) On Track",
                f"You're within limits on {good_count} category budget(s). Keep it up!",
                "success", "budget"
            ))

        # Unbudgeted categories
        for cat, amt in data.get("unbudgeted_spending", {}).items():
            if amt > 1000:
                insights.append(self._create_insight(
                    f"Unbudgeted: {cat}",
                    f"You've spent Rs. {amt:,.0f} on {cat} this month with no budget set. Consider adding one.",
                    "info", "budget",
                    {"category": cat, "amount": amt}
                ))

        return insights
