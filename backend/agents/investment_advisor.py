"""Investment Advisor Agent — investment suggestions based on spending patterns."""
import pandas as pd
from .base_agent import BaseAgent


class InvestmentAdvisorAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.name = "Investment Advisor"
        self.role = "Personalized investment recommendations"
        self.avatar = "trending-up"
        self.color = "#0984e3"

    def _think(self, df, ctx):
        if df.empty:
            return {"empty": True}

        total_income = ctx.get('total_income', 50000)
        monthly_totals = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
        avg_expense = float(monthly_totals.mean())
        monthly_savings = total_income - avg_expense
        savings_rate = (monthly_savings / total_income * 100) if total_income > 0 else 0

        emergency_target = avg_expense * 6
        num_months = len(monthly_totals)

        # CFP data
        age = ctx.get('age', 25)
        dependents = ctx.get('dependents', 0)
        has_health = ctx.get('has_health_insurance', False)
        has_term = ctx.get('has_term_insurance', False)

        # Emergency fund months covered
        estimated_emergency_months = (monthly_savings * num_months) / avg_expense if avg_expense > 0 else 0

        # DTI ratio (bills as % of income)
        bills_df = df[df['category'] == 'Bills']
        if not bills_df.empty:
            bills_monthly = float(bills_df.groupby(bills_df['date'].dt.to_period('M'))['amount'].sum().mean())
        else:
            bills_monthly = 0
        dti_ratio = round((bills_monthly / total_income) * 100, 1) if total_income > 0 else 0

        # Age-based allocation
        equity_allocation = max(20, min(80, 100 - age))
        debt_allocation = 100 - equity_allocation

        return {
            "empty": False,
            "total_income": total_income,
            "avg_expense": round(avg_expense, 2),
            "monthly_savings": round(monthly_savings, 2),
            "savings_rate": round(savings_rate, 1),
            "emergency_target": round(emergency_target, 2),
            "num_months": num_months,
            "age": age,
            "dependents": dependents,
            "has_health_insurance": has_health,
            "has_term_insurance": has_term,
            "emergency_months_covered": round(estimated_emergency_months, 1),
            "dti_ratio": dti_ratio,
            "bills_monthly": round(bills_monthly, 2),
            "equity_allocation": equity_allocation,
            "debt_allocation": debt_allocation,
        }

    def _analyze(self, data, ctx):
        if data.get("empty"):
            return []

        insights = []
        ms = data["monthly_savings"]
        sr = data["savings_rate"]

        if ms <= 0:
            insights.append(self._create_insight(
                "Build Savings First",
                "Your expenses currently exceed your income. Focus on reducing spending before investing.",
                "warning", "investment"
            ))
            return insights

        # Emergency fund
        insights.append(self._create_insight(
            "Emergency Fund Priority",
            f"Target Rs. {data['emergency_target']:,.0f} (6 months of expenses) in a liquid fund or high-interest savings account. "
            f"Allocate ~Rs. {min(ms * 0.3, data['emergency_target'] / 12):,.0f}/month.",
            "info", "investment",
            {"target": data["emergency_target"], "monthly_allocation": round(min(ms * 0.3, data['emergency_target'] / 12))}
        ))

        # Investment suggestions based on savings rate
        if sr >= 30:
            insights.append(self._create_insight(
                "Equity SIP Recommended",
                f"With a {sr}% savings rate, invest Rs. {ms * 0.4:,.0f}/month in Nifty 50 index funds via SIP for long-term wealth building.",
                "success", "investment",
                {"type": "equity", "amount": round(ms * 0.4)}
            ))
            insights.append(self._create_insight(
                "Tax-Saving with PPF",
                f"Invest Rs. {min(ms * 0.15, 12500):,.0f}/month in PPF for ~7.1% tax-free returns under Section 80C.",
                "info", "investment",
                {"type": "ppf", "amount": round(min(ms * 0.15, 12500))}
            ))
        elif sr >= 15:
            insights.append(self._create_insight(
                "Balanced Funds",
                f"A {sr}% savings rate is solid. Start with Rs. {ms * 0.35:,.0f}/month in balanced mutual funds mixing equity and debt.",
                "info", "investment",
                {"type": "balanced", "amount": round(ms * 0.35)}
            ))
        else:
            insights.append(self._create_insight(
                "Start with Recurring Deposit",
                f"At {sr}% savings, build the habit first. Open an RD of Rs. {max(ms * 0.3, 500):,.0f}/month.",
                "info", "investment",
                {"type": "rd", "amount": round(max(ms * 0.3, 500))}
            ))

        # Gold allocation
        if ms > 5000:
            insights.append(self._create_insight(
                "Gold as Hedge",
                f"Allocate 5% (Rs. {ms * 0.05:,.0f}/month) to Digital Gold or Gold ETF as an inflation hedge.",
                "info", "investment",
                {"type": "gold", "amount": round(ms * 0.05)}
            ))

        # Emergency fund status
        em = data.get('emergency_months_covered', 0)
        if em < 3:
            insights.append(self._create_insight(
                f"Emergency Fund: {em:.1f} Months",
                f"You have ~{em:.1f} months of expenses covered. Target 6 months "
                f"(Rs. {data['emergency_target']:,.0f}). This should be your top priority.",
                "critical" if em < 1 else "warning", "investment",
                {"months_covered": em}
            ))
        elif em >= 6:
            insights.append(self._create_insight(
                "Emergency Fund: Healthy",
                f"~{em:.0f} months of expenses covered. Focus on growth investments.",
                "success", "investment"
            ))

        # DTI ratio
        dti = data.get('dti_ratio', 0)
        if dti > 40:
            insights.append(self._create_insight(
                f"High Fixed Obligations: {dti}%",
                f"Bills/EMIs take {dti}% of income. Ideal is below 30%. Consider restructuring.",
                "warning", "investment"
            ))

        # Tax-saving suggestions
        if ms > 0:
            monthly_80c = round(min(150000 / 12, ms * 0.2), -2)
            if monthly_80c >= 500:
                insights.append(self._create_insight(
                    "Tax-Saving: Section 80C",
                    f"Invest Rs. {monthly_80c:,.0f}/month in ELSS, PPF, or NPS to save up to Rs. 46,800/year in taxes. "
                    f"ELSS has shortest lock-in (3 years).",
                    "info", "investment",
                    {"type": "80C", "monthly": monthly_80c}
                ))

        # Insurance checks
        if not data.get('has_health_insurance') and data.get('dependents', 0) > 0:
            insights.append(self._create_insight(
                "Health Insurance Missing",
                f"With {data['dependents']} dependent(s), health insurance is critical. "
                f"A Rs. 5-10 lakh family floater costs ~Rs. 800-1500/month with 80D tax benefits.",
                "critical", "investment"
            ))

        if not data.get('has_term_insurance') and data.get('dependents', 0) > 0:
            insights.append(self._create_insight(
                "Term Insurance Recommended",
                f"With dependents, get term cover of 10-15x annual income "
                f"(Rs. {data['total_income'] * 12 * 10:,.0f}). Costs ~Rs. 500-1000/month.",
                "warning", "investment"
            ))

        # Age-appropriate allocation
        insights.append(self._create_insight(
            f"Asset Allocation: {data['equity_allocation']}% Equity / {data['debt_allocation']}% Debt",
            f"At age {data.get('age', 25)}, a {data['equity_allocation']}:{data['debt_allocation']} equity-to-debt split "
            f"balances growth and safety. Rebalance annually.",
            "info", "investment",
            {"equity": data['equity_allocation'], "debt": data['debt_allocation']}
        ))

        return insights
