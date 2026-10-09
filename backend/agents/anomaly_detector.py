"""Anomaly Detector Agent — unusual spending detection."""
import numpy as np
import pandas as pd
from .base_agent import BaseAgent


class AnomalyDetectorAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.name = "Anomaly Detector"
        self.role = "Unusual spending & spike detection"
        self.avatar = "alert-triangle"
        self.color = "#e17055"

    def _think(self, df, ctx):
        if df.empty or len(df) < 5:
            return {"empty": True}

        now = pd.Timestamp.now()
        monthly_totals = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
        num_months = len(monthly_totals)

        # Monthly anomalies (z-score > 1.5)
        monthly_anomalies = []
        if num_months >= 3:
            mean_s = float(monthly_totals.mean())
            std_s = float(monthly_totals.std())
            threshold = mean_s + (1.5 * std_s)
            for period, amount in monthly_totals.items():
                if float(amount) > threshold:
                    monthly_anomalies.append({
                        "month": str(period),
                        "amount": round(float(amount), 2),
                        "average": round(mean_s, 2),
                        "excess": round(float(amount) - mean_s, 2),
                    })

        # Large single transactions
        large_transactions = []
        if len(df) >= 10:
            mean_txn = float(df['amount'].mean())
            std_txn = float(df['amount'].std())
            large_threshold = mean_txn + (2 * std_txn)
            recent_df = df[df['date'] >= (now - pd.Timedelta(days=30))]
            for _, row in recent_df.iterrows():
                if row['amount'] > large_threshold:
                    large_transactions.append({
                        "date": str(row['date'].date()),
                        "amount": round(float(row['amount']), 2),
                        "category": row['category'],
                        "description": row.get('description', ''),
                        "avg_transaction": round(mean_txn, 2),
                        "multiplier": round(float(row['amount'] / mean_txn), 1),
                    })

        # Category spikes (current month vs average)
        category_spikes = []
        if num_months >= 2:
            cat_monthly = df.groupby([df['date'].dt.to_period('M'), 'category'])['amount'].sum().unstack(fill_value=0)
            current_period = now.to_period('M')
            if current_period in cat_monthly.index and len(cat_monthly) >= 2:
                current_cats = cat_monthly.loc[current_period]
                avg_cats = cat_monthly.drop(current_period, errors='ignore').mean()
                for cat in current_cats.index:
                    curr = float(current_cats[cat])
                    avg = float(avg_cats.get(cat, 0))
                    if avg > 0 and curr > avg * 1.5:
                        category_spikes.append({
                            "category": cat,
                            "current_amount": round(curr, 2),
                            "average_amount": round(avg, 2),
                            "increase_pct": round(((curr - avg) / avg) * 100, 1),
                        })

        # Weekend vs weekday spending
        df_copy = df.copy()
        df_copy['is_weekend'] = df_copy['date'].dt.dayofweek >= 5
        weekend_avg = float(df_copy[df_copy['is_weekend']]['amount'].mean()) if df_copy['is_weekend'].any() else 0
        weekday_avg = float(df_copy[~df_copy['is_weekend']]['amount'].mean()) if (~df_copy['is_weekend']).any() else 0

        # Week-over-week comparison
        today = now.normalize()
        week_start = today - pd.Timedelta(days=today.dayofweek)
        last_week_start = week_start - pd.Timedelta(days=7)

        this_week_df = df[(df['date'] >= week_start) & (df['date'] < week_start + pd.Timedelta(days=7))]
        last_week_df = df[(df['date'] >= last_week_start) & (df['date'] < week_start)]

        this_week_total = float(this_week_df['amount'].sum())
        last_week_total = float(last_week_df['amount'].sum())
        week_change_pct = round(((this_week_total - last_week_total) / last_week_total) * 100, 1) if last_week_total > 0 else 0

        return {
            "empty": False,
            "monthly_anomalies": monthly_anomalies,
            "large_transactions": large_transactions[:5],
            "category_spikes": category_spikes,
            "weekend_avg": round(weekend_avg, 2),
            "weekday_avg": round(weekday_avg, 2),
            "this_week_total": round(this_week_total, 2),
            "last_week_total": round(last_week_total, 2),
            "week_change_pct": week_change_pct,
        }

    def _analyze(self, data, ctx):
        if data.get("empty"):
            return []

        insights = []

        # Monthly anomalies
        for a in data["monthly_anomalies"]:
            insights.append(self._create_insight(
                f"Unusual Month: {a['month']}",
                f"Spending of Rs. {a['amount']:,.0f} in {a['month']} was Rs. {a['excess']:,.0f} above your average of Rs. {a['average']:,.0f}.",
                "warning", "anomaly",
                a
            ))

        # Large transactions
        for lt in data["large_transactions"]:
            insights.append(self._create_insight(
                f"Large Transaction: Rs. {lt['amount']:,.0f}",
                f"Rs. {lt['amount']:,.0f} on {lt['category']} ({lt['date']}) is {lt['multiplier']}x your average transaction."
                + (f" ({lt['description']})" if lt['description'] else ""),
                "warning", "anomaly",
                lt
            ))

        # Category spikes
        for cs in data["category_spikes"]:
            excess = cs['current_amount'] - cs['average_amount']
            insights.append(self._create_insight(
                f"{cs['category']} Spike: +{cs['increase_pct']:.0f}%",
                f"Your {cs['category']} spending jumped {cs['increase_pct']:.0f}% this month "
                f"(Rs. {cs['current_amount']:,.0f} vs avg Rs. {cs['average_amount']:,.0f}). "
                f"That's Rs. {excess:,.0f} extra. Check if this is a one-time expense or a new pattern.",
                "warning", "anomaly",
                cs
            ))

        # Weekly spike
        wc = data.get("week_change_pct", 0)
        if wc > 40 and data.get("last_week_total", 0) > 0:
            insights.append(self._create_insight(
                f"Weekly Spending Spike: +{wc}%",
                f"This week: Rs. {data['this_week_total']:,.0f} vs last week: Rs. {data['last_week_total']:,.0f}. "
                f"That's a {wc}% increase. Review your recent transactions.",
                "warning", "anomaly",
                {"this_week": data['this_week_total'], "last_week": data['last_week_total'], "change_pct": wc}
            ))

        # Weekend pattern
        wa = data["weekend_avg"]
        wda = data["weekday_avg"]
        if wa > 0 and wda > 0 and wa > wda * 1.5:
            insights.append(self._create_insight(
                "High Weekend Spending",
                f"Weekend transactions average Rs. {wa:,.0f} vs Rs. {wda:,.0f} on weekdays. "
                f"Consider setting a weekend spending limit.",
                "info", "anomaly",
                {"weekend_avg": wa, "weekday_avg": wda}
            ))

        if not insights:
            insights.append(self._create_insight(
                "No Anomalies Detected",
                "Your spending patterns look normal. No unusual activity found.",
                "success", "anomaly"
            ))

        return insights
