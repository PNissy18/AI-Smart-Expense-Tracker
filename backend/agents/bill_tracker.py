"""Bill Tracker Agent — recurring bill detection, upcoming alerts, income impact."""
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from .base_agent import BaseAgent


class BillTrackerAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.name = "Bill Tracker"
        self.role = "Recurring bill detection & reminders"
        self.avatar = "calendar"
        self.color = "#fdcb6e"

    def _think(self, df, ctx):
        if df.empty or len(df) < 10:
            return {"empty": True}

        now = pd.Timestamp.now()
        total_income = ctx.get('total_income', 50000)

        # Group transactions by (category, rounded_amount, description_key)
        # to detect recurring patterns
        df_copy = df.copy()
        df_copy['month'] = df_copy['date'].dt.to_period('M')
        df_copy['desc_key'] = df_copy['description'].str.lower().str.strip()
        df_copy['amount_bucket'] = (df_copy['amount'] / 50).round() * 50  # bucket to nearest 50

        # Find recurring patterns: same category + similar amount appearing in 2+ months
        recurring = []
        groups = df_copy.groupby(['category', 'amount_bucket'])

        for (cat, amt_bucket), group in groups:
            months = group['month'].unique()
            if len(months) >= 2:
                avg_amount = round(float(group['amount'].mean()), 2)
                # Find typical day of month
                days = group['date'].dt.day
                typical_day = int(days.median())

                # Most common description
                desc_counts = group['desc_key'].value_counts()
                best_desc = desc_counts.index[0] if len(desc_counts) > 0 else ''
                display_name = best_desc.title() if best_desc else f"{cat} (~Rs. {avg_amount:,.0f})"

                # Check if it appeared in the current month
                current_period = now.to_period('M')
                appeared_this_month = current_period in months

                # Last occurrence
                last_date = group['date'].max()

                # Detect newly recurring (only 2 months)
                is_new = len(months) == 2

                recurring.append({
                    "name": display_name,
                    "category": cat,
                    "estimated_amount": avg_amount,
                    "typical_day": typical_day,
                    "months_detected": len(months),
                    "appeared_this_month": appeared_this_month,
                    "last_date": str(last_date.date()),
                    "frequency": "monthly",
                    "is_new": is_new,
                })

        # Sort by amount (highest first) and deduplicate
        recurring.sort(key=lambda x: x['estimated_amount'], reverse=True)

        # Deduplicate by name similarity
        seen_names = set()
        unique_recurring = []
        for r in recurring:
            key = r['name'][:15].lower()
            if key not in seen_names:
                seen_names.add(key)
                unique_recurring.append(r)

        # Calculate totals
        total_recurring = sum(r['estimated_amount'] for r in unique_recurring)
        bills_pct_of_income = round((total_recurring / total_income) * 100, 1) if total_income > 0 else 0

        # Upcoming bills (not yet appeared this month, expected day hasn't passed)
        upcoming = [r for r in unique_recurring if not r['appeared_this_month'] and r['typical_day'] >= now.day]

        # New recurring (appeared in exactly 2 months)
        new_recurring = [r for r in unique_recurring if r['is_new']]

        return {
            "empty": False,
            "recurring_bills": unique_recurring[:10],
            "upcoming_bills": upcoming[:5],
            "new_recurring": new_recurring[:3],
            "total_recurring": round(total_recurring, 2),
            "bills_pct_of_income": bills_pct_of_income,
            "total_income": total_income,
            "count": len(unique_recurring),
            "current_day": now.day,
        }

    def _analyze(self, data, ctx):
        if data.get("empty"):
            return [self._create_insight(
                "Need More Data",
                "Add more transactions over time so I can detect your recurring bills and subscriptions.",
                "info", "bills"
            )]

        insights = []

        count = data["count"]
        total = data["total_recurring"]
        pct = data["bills_pct_of_income"]

        if count > 0:
            severity = "warning" if pct > 40 else "info"
            insights.append(self._create_insight(
                f"{count} Recurring Expense(s): Rs. {total:,.0f}/mo",
                f"Your {count} recurring bills total ~Rs. {total:,.0f}/month, which is {pct}% of your income. "
                + ("This is high -- review subscriptions you can cancel." if pct > 40
                   else "This is within a healthy range." if pct <= 30
                   else "Getting close to the 40% comfort limit."),
                severity, "bills",
                {"count": count, "total": total, "pct_of_income": pct, "bills": data["recurring_bills"]}
            ))

        # Upcoming bills
        for bill in data["upcoming_bills"]:
            days_until = bill['typical_day'] - data['current_day']
            insights.append(self._create_insight(
                f"Upcoming: {bill['name']}",
                f"{bill['name']} (~Rs. {bill['estimated_amount']:,.0f}) is expected around day {bill['typical_day']} "
                f"-- about {days_until} day(s) away. Ensure sufficient balance.",
                "warning" if days_until <= 3 else "info",
                "bills",
                bill
            ))

        # Newly recurring expenses (appeared 2 months only)
        for nr in data.get("new_recurring", []):
            insights.append(self._create_insight(
                f"New Recurring: {nr['name']}",
                f"{nr['name']} (~Rs. {nr['estimated_amount']:,.0f}) has appeared for 2 months. "
                f"If this is a new subscription, make sure it's intentional.",
                "info", "bills",
                nr
            ))

        # Bills that should have appeared but didn't
        missed = [r for r in data["recurring_bills"]
                  if not r['appeared_this_month'] and r['typical_day'] < data['current_day'] and not r.get('is_new')]
        for bill in missed[:3]:
            insights.append(self._create_insight(
                f"Missed? {bill['name']}",
                f"{bill['name']} (~Rs. {bill['estimated_amount']:,.0f}) usually appears by day {bill['typical_day']} "
                f"but hasn't shown up this month. Cancelled, delayed, or auto-debited elsewhere?",
                "info", "bills",
                bill
            ))

        return insights
