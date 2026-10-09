"""Savings Coach Agent — goal tracking, milestones, encouragement."""
import pandas as pd
from .base_agent import BaseAgent


MILESTONES = [1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 1000000]


class SavingsCoachAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.name = "Savings Coach"
        self.role = "Goal tracking & savings motivation"
        self.avatar = "target"
        self.color = "#00b894"

    def _think(self, df, ctx):
        total_income = ctx.get('total_income', 50000)
        goals = ctx.get('goals', [])

        if df.empty:
            return {"empty": True, "goals": goals}

        monthly_totals = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
        avg_expense = float(monthly_totals.mean())
        monthly_savings = total_income - avg_expense
        num_months = len(monthly_totals)
        total_saved_estimate = max(0, monthly_savings * num_months)

        # Current month
        now = pd.Timestamp.now()
        current_month_df = df[df['date'].dt.to_period('M') == now.to_period('M')]
        current_expense = float(current_month_df['amount'].sum()) if not current_month_df.empty else 0
        current_month_savings = total_income - current_expense

        # Best / worst month
        best_month_expense = float(monthly_totals.min())
        best_month_savings = total_income - best_month_expense
        worst_month_expense = float(monthly_totals.max())

        # Savings velocity
        savings_velocity = "faster" if current_month_savings > monthly_savings * 1.1 else "slower" if current_month_savings < monthly_savings * 0.9 else "on_track"

        # Goal analysis
        goal_analysis = []
        for g in goals:
            if g.get('status') != 'active':
                continue
            target = g['target_amount']
            current = g.get('current_amount', 0)
            pct = round((current / target) * 100, 1) if target > 0 else 0
            remaining = max(0, target - current)

            months_to_goal = round(remaining / monthly_savings, 1) if monthly_savings > 0 else float('inf')

            # Monthly needed to hit deadline
            monthly_needed = None
            if g.get('deadline') and remaining > 0:
                try:
                    deadline_date = pd.Timestamp(g['deadline'])
                    months_left = max(1, (deadline_date.year - now.year) * 12 + (deadline_date.month - now.month))
                    monthly_needed = round(remaining / months_left, 2)
                except Exception:
                    pass

            goal_analysis.append({
                "name": g['name'],
                "target": target,
                "current": current,
                "percentage": pct,
                "remaining": remaining,
                "months_to_goal": months_to_goal,
                "deadline": g.get('deadline'),
                "monthly_needed": monthly_needed,
            })

        # Milestone check
        next_milestone = None
        for m in MILESTONES:
            if total_saved_estimate < m:
                next_milestone = m
                break

        return {
            "empty": False,
            "monthly_savings": round(monthly_savings, 2),
            "current_month_savings": round(current_month_savings, 2),
            "total_saved_estimate": round(total_saved_estimate, 2),
            "best_month_savings": round(best_month_savings, 2),
            "avg_expense": round(avg_expense, 2),
            "goal_analysis": goal_analysis,
            "next_milestone": next_milestone,
            "num_months": num_months,
            "savings_velocity": savings_velocity,
        }

    def _analyze(self, data, ctx):
        if data.get("empty"):
            return [self._create_insight(
                "Start Tracking to Save",
                "Once you add transactions, I'll help you track savings and hit your goals!",
                "info", "savings"
            )]

        insights = []
        ms = data["monthly_savings"]
        cms = data["current_month_savings"]

        # Current month performance
        if cms > ms * 1.2:
            insights.append(self._create_insight(
                "Amazing Month So Far!",
                f"You're saving Rs. {cms:,.0f} this month -- that's better than your average of Rs. {ms:,.0f}!",
                "success", "savings",
                {"current_month_savings": cms, "avg_monthly_savings": ms}
            ))
        elif cms < 0:
            insights.append(self._create_insight(
                "Overspending This Month",
                f"You're Rs. {abs(cms):,.0f} over budget this month. Try to cut non-essential spending for the rest of the month.",
                "critical", "savings",
                {"current_month_savings": cms}
            ))

        # Goal insights
        for ga in data["goal_analysis"]:
            if ga["percentage"] >= 100:
                insights.append(self._create_insight(
                    f"Goal Complete: {ga['name']}!",
                    f"Congratulations! You've reached your Rs. {ga['target']:,.0f} goal!",
                    "success", "savings",
                    ga
                ))
            elif ga["percentage"] >= 75:
                insights.append(self._create_insight(
                    f"Almost There: {ga['name']}",
                    f"You're {ga['percentage']}% of the way to {ga['name']}! Just Rs. {ga['remaining']:,.0f} to go.",
                    "success", "savings",
                    ga
                ))
            elif ga["months_to_goal"] != float('inf'):
                eta_text = f"~{ga['months_to_goal']:.0f} months" if ga['months_to_goal'] > 1 else "less than a month"
                insights.append(self._create_insight(
                    f"Goal Progress: {ga['name']}",
                    f"{ga['name']} is {ga['percentage']}% complete (Rs. {ga['current']:,.0f} / Rs. {ga['target']:,.0f}). "
                    f"At your current pace, you'll reach it in {eta_text}.",
                    "info", "savings",
                    ga
                ))

        # Goal deadline warnings
        for ga in data["goal_analysis"]:
            if ga.get('monthly_needed') and ga['monthly_needed'] > ms and ga['percentage'] < 100:
                shortfall = ga['monthly_needed'] - ms
                insights.append(self._create_insight(
                    f"Goal at Risk: {ga['name']}",
                    f"To hit {ga['name']} by {ga['deadline']}, you need Rs. {ga['monthly_needed']:,.0f}/month, "
                    f"but you average Rs. {ms:,.0f}. Increase savings by Rs. {shortfall:,.0f}/month or extend deadline.",
                    "warning", "savings", ga
                ))

        if not data["goal_analysis"] and not ctx.get('goals'):
            insights.append(self._create_insight(
                "Set a Savings Goal",
                f"You're saving ~Rs. {ms:,.0f}/month. Set a goal to stay motivated! Try the Goals page to get started.",
                "info", "savings",
                {"monthly_savings": ms}
            ))

        # Savings velocity
        vel = data.get("savings_velocity")
        if vel == "faster" and ms > 0:
            insights.append(self._create_insight(
                "Savings Accelerating",
                f"Saving Rs. {cms:,.0f} this month vs avg Rs. {ms:,.0f}. Great momentum!",
                "success", "savings"
            ))
        elif vel == "slower" and ms > 0 and cms < ms:
            insights.append(self._create_insight(
                "Savings Slowing Down",
                f"This month's savings (Rs. {cms:,.0f}) is below your avg of Rs. {ms:,.0f}. "
                f"Try cutting Rs. {abs(ms - cms):,.0f} in discretionary spending.",
                "warning", "savings"
            ))

        # Auto-savings suggestion
        recommended_auto = round(ms * 0.5, -2) if ms > 0 else 0
        if recommended_auto >= 1000:
            insights.append(self._create_insight(
                "Automate Your Savings",
                f"Set up an auto-transfer of Rs. {recommended_auto:,.0f}/month on salary day. "
                f"This builds wealth on autopilot.",
                "info", "savings",
                {"auto_savings_amount": recommended_auto}
            ))

        # Milestone
        nm = data.get("next_milestone")
        tse = data["total_saved_estimate"]
        if nm and tse > 0:
            pct_to_milestone = round((tse / nm) * 100, 1)
            if pct_to_milestone >= 80:
                insights.append(self._create_insight(
                    f"Approaching Rs. {nm:,.0f} Milestone",
                    f"You're {pct_to_milestone}% of the way to saving Rs. {nm:,.0f} total. Keep pushing!",
                    "success", "savings"
                ))

        return insights
