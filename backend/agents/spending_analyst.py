"""Spending Analyst Agent — pattern detection, trends, health score, 50/30/20 rule."""
import numpy as np
import pandas as pd
from .base_agent import BaseAgent


IDEAL_RANGES = {
    'Food': (20, 35), 'Transport': (5, 15), 'Shopping': (5, 20),
    'Bills': (15, 30), 'Entertainment': (3, 10), 'Healthcare': (3, 10),
    'Education': (3, 15), 'Other': (0, 15),
}

NEEDS_CATEGORIES = {'Food', 'Bills', 'Healthcare', 'Transport', 'Education'}
WANTS_CATEGORIES = {'Shopping', 'Entertainment', 'Other'}


class SpendingAnalystAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.name = "Spending Analyst"
        self.role = "Pattern detection & trend analysis"
        self.avatar = "bar-chart-2"
        self.color = "#6c5ce7"

    def _think(self, df, ctx):
        if df.empty:
            return {"empty": True}

        now = pd.Timestamp.now()
        monthly_totals = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
        num_months = len(monthly_totals)
        avg_monthly = float(monthly_totals.mean())

        current_month_df = df[df['date'].dt.to_period('M') == now.to_period('M')]
        current_expense = float(current_month_df['amount'].sum()) if not current_month_df.empty else 0.0

        # Category breakdown
        cat_totals = df.groupby('category')['amount'].sum()
        total_spent = cat_totals.sum()
        cat_pcts = ((cat_totals / total_spent) * 100).to_dict() if total_spent > 0 else {}

        # Trend
        if num_months >= 3:
            last3 = monthly_totals.tail(3).values
            predicted = round(float(np.mean(last3)), 2)
            trend_pct = round(float((last3[-1] - last3[0]) / last3[0] * 100), 1) if last3[0] > 0 else 0
        elif num_months >= 1:
            predicted = round(float(monthly_totals.tail(1).values[0]), 2)
            trend_pct = 0
        else:
            predicted = 0
            trend_pct = 0

        # Volatility
        volatility = float(monthly_totals.std() / monthly_totals.mean()) if num_months >= 2 and monthly_totals.mean() > 0 else 0

        # Health score components
        total_income = ctx.get('total_income', 50000)
        savings_rate = ((total_income - avg_monthly) / total_income * 100) if total_income > 0 else 0
        savings_score = min(30, max(0, savings_rate * 0.6))
        consistency_score = max(0, 20 - (volatility * 20)) if num_months >= 2 else 10

        max_cat_pct = max(cat_pcts.values()) if cat_pcts else 0
        balance_score = max(0, 15 - max(0, (max_cat_pct - 30) * 0.3))

        budgets = ctx.get('budgets', [])
        if budgets and not current_month_df.empty:
            hits = sum(1 for b in budgets if current_month_df[current_month_df['category'] == b['category']]['amount'].sum() <= b['monthly_limit'])
            adherence_score = (hits / len(budgets)) * 15
        else:
            adherence_score = 7.5

        monthly_savings_amt = total_income - avg_monthly
        months_saved = (monthly_savings_amt * num_months) / avg_monthly if avg_monthly > 0 else 0
        emergency_score = min(20, months_saved * 3.3)

        health_score = round(min(100, max(0, savings_score + consistency_score + balance_score + adherence_score + emergency_score)))

        # 50/30/20 Rule Analysis
        needs_total = sum(cat_totals.get(c, 0) for c in NEEDS_CATEGORIES)
        wants_total = sum(cat_totals.get(c, 0) for c in WANTS_CATEGORIES)
        income_basis = total_income * max(num_months, 1)
        if income_basis > 0:
            needs_pct = round((needs_total / income_basis) * 100, 1)
            wants_pct = round((wants_total / income_basis) * 100, 1)
            savings_pct_rule = round(max(0, 100 - needs_pct - wants_pct), 1)
        else:
            needs_pct = wants_pct = savings_pct_rule = 0

        # Month-over-month
        mom_change = None
        last_month_val = None
        prev_month_val = None
        if num_months >= 2:
            last_month_val = float(monthly_totals.iloc[-1])
            prev_month_val = float(monthly_totals.iloc[-2])
            if prev_month_val > 0:
                mom_change = round(((last_month_val - prev_month_val) / prev_month_val) * 100, 1)

        return {
            "empty": False,
            "monthly_totals": monthly_totals,
            "num_months": num_months,
            "avg_monthly": avg_monthly,
            "current_expense": current_expense,
            "cat_pcts": cat_pcts,
            "cat_totals": cat_totals.to_dict(),
            "predicted": predicted,
            "trend_pct": trend_pct,
            "volatility": volatility,
            "savings_rate": round(savings_rate, 1),
            "health_score": health_score,
            "score_breakdown": {
                "savings": round(savings_score, 1),
                "consistency": round(consistency_score, 1),
                "balance": round(balance_score, 1),
                "budget_adherence": round(adherence_score, 1),
                "emergency_readiness": round(emergency_score, 1),
            },
            "rule_50_30_20": {
                "needs_pct": needs_pct,
                "wants_pct": wants_pct,
                "savings_pct": savings_pct_rule,
            },
            "mom_change": mom_change,
            "last_month_val": last_month_val,
            "prev_month_val": prev_month_val,
        }

    def _analyze(self, data, ctx):
        if data.get("empty"):
            return [self._create_insight(
                "No Data Yet",
                "Add some transactions so I can analyze your spending patterns.",
                "info", "spending"
            )]

        insights = []
        hs = data["health_score"]
        grade = 'Excellent' if hs >= 80 else 'Good' if hs >= 60 else 'Fair' if hs >= 40 else 'Needs Attention'

        insights.append(self._create_insight(
            f"Financial Health: {grade}",
            f"Your financial health score is {hs}/100. "
            + ("Keep up the great work!" if hs >= 70 else "There's room for improvement -- check the insights below."),
            "success" if hs >= 70 else "warning" if hs >= 40 else "critical",
            "spending",
            {"health_score": hs, "grade": grade, "breakdown": data["score_breakdown"]}
        ))

        # 50/30/20 Rule insight
        rule = data["rule_50_30_20"]
        rule_msg = (f"Your split: Needs {rule['needs_pct']}% | Wants {rule['wants_pct']}% | Savings {rule['savings_pct']}%. "
                    f"Ideal: 50% | 30% | 20%. ")
        if rule['needs_pct'] > 60:
            rule_msg += f"Your needs are high at {rule['needs_pct']}%. Look for ways to reduce fixed costs."
        elif rule['savings_pct'] < 15:
            rule_msg += f"Savings at {rule['savings_pct']}% is below 20%. Try cutting wants spending."
        else:
            rule_msg += "You're close to the ideal split!"

        insights.append(self._create_insight(
            "50/30/20 Budget Rule",
            rule_msg,
            "success" if rule['savings_pct'] >= 18 else "warning" if rule['savings_pct'] >= 10 else "critical",
            "spending", rule
        ))

        # Month-over-month comparison
        mom = data.get("mom_change")
        if mom is not None:
            direction = "increased" if mom > 0 else "decreased"
            insights.append(self._create_insight(
                f"Month-over-Month: {'+' if mom > 0 else ''}{mom}%",
                f"Spending {direction} by {abs(mom)}% vs last month "
                f"(Rs. {data['last_month_val']:,.0f} vs Rs. {data['prev_month_val']:,.0f})."
                + (" Review recent spending." if mom > 15 else " Great discipline!" if mom < -5 else ""),
                "warning" if mom > 15 else "success" if mom < -5 else "info",
                "spending",
                {"mom_change_pct": mom, "current": data['last_month_val'], "previous": data['prev_month_val']}
            ))

        # Trend insight
        tp = data["trend_pct"]
        if tp > 15:
            insights.append(self._create_insight(
                "Spending Trending Up",
                f"Your spending increased {tp}% over the last 3 months. Review recent expenses to stay on track.",
                "warning", "spending",
                {"trend_pct": tp, "predicted_next_month": data["predicted"]}
            ))
        elif tp < -10:
            insights.append(self._create_insight(
                "Spending Going Down",
                f"Great job! Spending decreased {abs(tp)}% over the last 3 months.",
                "success", "spending",
                {"trend_pct": tp, "predicted_next_month": data["predicted"]}
            ))

        # Category insights
        for cat, pct in sorted(data["cat_pcts"].items(), key=lambda x: x[1], reverse=True):
            low, high = IDEAL_RANGES.get(cat, (0, 25))
            if pct > high + 10:
                insights.append(self._create_insight(
                    f"High {cat} Spending",
                    f"{cat} is {pct:.0f}% of your total (ideal: {low}-{high}%). Consider ways to optimize.",
                    "warning", "spending",
                    {"category": cat, "percentage": round(pct, 1), "ideal_range": f"{low}-{high}%"}
                ))

        # Savings rate
        sr = data["savings_rate"]
        if sr < 10:
            insights.append(self._create_insight(
                "Low Savings Rate",
                f"Savings rate is only {sr}%. Aim for at least 20%. Start by cutting your largest discretionary category.",
                "critical", "spending", {"savings_rate": sr}
            ))
        elif sr >= 30:
            insights.append(self._create_insight(
                "Strong Savings Rate",
                f"Excellent savings rate of {sr}%! Consider investing the surplus for growth.",
                "success", "spending", {"savings_rate": sr}
            ))

        return insights
