"""
Flask Backend API for AI Smart Expense Tracker.
Pure AI Agent-powered financial analysis.
"""
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import re
import os
from datetime import datetime, timedelta

from database import get_db, init_db
from auth import create_token, login_required
from agents import AgentOrchestrator

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

CATEGORIES = ['Food', 'Transport', 'Shopping', 'Bills', 'Entertainment',
              'Healthcare', 'Education', 'Other']


def load_transactions_for_user(user_id):
    """Load transactions from SQLite for a specific user."""
    db = get_db()
    rows = db.execute(
        'SELECT date, amount, category, payment_mode, description FROM transactions WHERE user_id = ? ORDER BY date',
        (user_id,)
    ).fetchall()
    db.close()
    if not rows:
        return pd.DataFrame(columns=['date', 'amount', 'category', 'payment_mode', 'description'])
    df = pd.DataFrame([dict(r) for r in rows])
    df['date'] = pd.to_datetime(df['date'])
    return df


def get_user_income_data(user_id):
    """Get user's monthly income + additional income for current month."""
    db = get_db()
    user = db.execute('SELECT monthly_income FROM users WHERE id = ?', (user_id,)).fetchone()
    monthly_income = user['monthly_income'] if user else 50000

    month_prefix = datetime.now().strftime('%Y-%m')
    additional_rows = db.execute(
        "SELECT amount FROM additional_incomes WHERE user_id = ? AND date LIKE ?",
        (user_id, f'{month_prefix}%')
    ).fetchall()
    db.close()

    additional_income = sum(r['amount'] for r in additional_rows)
    return monthly_income, additional_income, monthly_income + additional_income


# =============================================
# AUTH ENDPOINTS
# =============================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Please enter a valid email address'}), 400

    db = get_db()
    existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        db.close()
        return jsonify({'error': 'An account with this email already exists'}), 409

    password_hash = generate_password_hash(password)
    cursor = db.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        (name, email, password_hash)
    )
    db.commit()
    user_id = cursor.lastrowid
    db.close()

    return jsonify({
        'message': 'Registration successful! Please login.',
        'user': {'id': user_id, 'name': name, 'email': email}
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login and get JWT token."""
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    db.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = create_token(user['id'], user['email'])
    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'monthly_income': user['monthly_income']
        }
    })


@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_me():
    """Get current user profile."""
    db = get_db()
    user = db.execute(
        'SELECT id, name, email, monthly_income, created_at FROM users WHERE id = ?',
        (g.user_id,)
    ).fetchone()
    if not user:
        db.close()
        return jsonify({'error': 'User not found'}), 404

    result = {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'monthly_income': user['monthly_income'],
        'created_at': user['created_at'],
        'age': 25, 'dependents': 0,
        'has_health_insurance': False, 'has_term_insurance': False,
    }
    try:
        extra = db.execute(
            'SELECT age, dependents, has_health_insurance, has_term_insurance FROM users WHERE id = ?',
            (g.user_id,)
        ).fetchone()
        if extra:
            result['age'] = extra['age'] or 25
            result['dependents'] = extra['dependents'] or 0
            result['has_health_insurance'] = bool(extra['has_health_insurance'])
            result['has_term_insurance'] = bool(extra['has_term_insurance'])
    except Exception:
        pass
    db.close()
    return jsonify(result)


@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'version': '3.0', 'engine': 'AI Agent-Powered'})


# =============================================
# TRANSACTION ENDPOINTS
# =============================================

@app.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    db = get_db()
    rows = db.execute(
        'SELECT id, date, amount, category, payment_mode, description FROM transactions WHERE user_id = ? ORDER BY date DESC',
        (g.user_id,)
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/transactions', methods=['POST'])
@login_required
def add_transaction():
    data = request.json
    db = get_db()
    db.execute(
        'INSERT INTO transactions (user_id, date, amount, category, payment_mode, description) VALUES (?, ?, ?, ?, ?, ?)',
        (g.user_id, data['date'], float(data['amount']), data['category'],
         data['payment_mode'], data.get('description', ''))
    )
    db.commit()
    db.close()
    return jsonify({'message': 'Transaction added successfully'}), 201


@app.route('/api/upload-csv', methods=['POST'])
@login_required
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400

    new_df = pd.read_csv(file)
    db = get_db()
    inserted = 0
    for _, row in new_df.iterrows():
        db.execute(
            'INSERT INTO transactions (user_id, date, amount, category, payment_mode, description) VALUES (?, ?, ?, ?, ?, ?)',
            (g.user_id, str(row['date']), float(row['amount']), str(row['category']),
             str(row['payment_mode']), str(row.get('description', '')))
        )
        inserted += 1
    db.commit()
    total = db.execute('SELECT COUNT(*) FROM transactions WHERE user_id = ?', (g.user_id,)).fetchone()[0]
    db.close()
    return jsonify({'message': f'Uploaded {inserted} transactions', 'total_transactions': total})


# =============================================
# INCOME ENDPOINTS
# =============================================

@app.route('/api/income', methods=['PUT'])
@login_required
def update_income():
    data = request.json
    income = data.get('monthly_income')
    if income is None or float(income) < 0:
        return jsonify({'error': 'Please provide a valid monthly income'}), 400
    db = get_db()
    db.execute('UPDATE users SET monthly_income = ? WHERE id = ?', (float(income), g.user_id))
    db.commit()
    db.close()
    return jsonify({'message': 'Income updated successfully', 'monthly_income': float(income)})


@app.route('/api/additional-income', methods=['GET'])
@login_required
def get_additional_incomes():
    month = request.args.get('month')
    db = get_db()
    if month:
        month_prefix = month
    else:
        month_prefix = datetime.now().strftime('%Y-%m')
    rows = db.execute(
        "SELECT id, date, amount, source, description FROM additional_incomes WHERE user_id = ? AND date LIKE ? ORDER BY date DESC",
        (g.user_id, f'{month_prefix}%')
    ).fetchall()
    db.close()
    items = [dict(r) for r in rows]
    total = sum(item['amount'] for item in items)
    return jsonify({'incomes': items, 'total': round(total, 2)})


@app.route('/api/additional-income', methods=['POST'])
@login_required
def add_additional_income():
    data = request.json
    date = data.get('date', '')
    amount = data.get('amount')
    source = data.get('source', 'Other').strip() or 'Other'
    description = data.get('description', '').strip()

    if not date or not amount:
        return jsonify({'error': 'Date and amount are required'}), 400
    if float(amount) <= 0:
        return jsonify({'error': 'Amount must be greater than 0'}), 400

    db = get_db()
    db.execute(
        'INSERT INTO additional_incomes (user_id, date, amount, source, description) VALUES (?, ?, ?, ?, ?)',
        (g.user_id, date, float(amount), source, description)
    )
    db.commit()
    db.close()
    return jsonify({'message': 'Additional income added successfully'}), 201


@app.route('/api/additional-income/<int:income_id>', methods=['DELETE'])
@login_required
def delete_additional_income(income_id):
    db = get_db()
    row = db.execute('SELECT id FROM additional_incomes WHERE id = ? AND user_id = ?', (income_id, g.user_id)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Income entry not found'}), 404
    db.execute('DELETE FROM additional_incomes WHERE id = ?', (income_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Income entry deleted'})


# =============================================
# USER PROFILE ENDPOINTS
# =============================================

@app.route('/api/user-profile', methods=['GET'])
@login_required
def get_user_profile():
    db = get_db()
    user = db.execute(
        'SELECT id, name, email, monthly_income, age, dependents, has_health_insurance, has_term_insurance FROM users WHERE id = ?',
        (g.user_id,)
    ).fetchone()
    db.close()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user['id'], 'name': user['name'], 'email': user['email'],
        'monthly_income': user['monthly_income'], 'age': user['age'],
        'dependents': user['dependents'],
        'has_health_insurance': bool(user['has_health_insurance']),
        'has_term_insurance': bool(user['has_term_insurance'])
    })


@app.route('/api/user-profile', methods=['PUT'])
@login_required
def update_user_profile():
    data = request.json
    db = get_db()
    fields = []
    values = []
    for field in ['name', 'age', 'dependents', 'has_health_insurance', 'has_term_insurance', 'monthly_income']:
        if field in data:
            fields.append(f'{field} = ?')
            val = data[field]
            if field in ('has_health_insurance', 'has_term_insurance'):
                val = 1 if val else 0
            values.append(val)
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    values.append(g.user_id)
    db.execute(f'UPDATE users SET {", ".join(fields)} WHERE id = ?', values)
    db.commit()
    db.close()
    return jsonify({'message': 'Profile updated successfully'})


# =============================================
# DASHBOARD
# =============================================

@app.route('/api/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    monthly_income, additional_income_total, total_income = get_user_income_data(g.user_id)
    df = load_transactions_for_user(g.user_id)

    db_u = get_db()
    user_row = db_u.execute(
        'SELECT has_health_insurance, has_term_insurance FROM users WHERE id = ?', (g.user_id,)
    ).fetchone()
    db_u.close()
    user_health_ins = bool(user_row['has_health_insurance']) if user_row else False
    user_term_ins = bool(user_row['has_term_insurance']) if user_row else False

    if df.empty:
        return jsonify({
            'total_expense': 0, 'avg_monthly_expense': 0, 'transaction_count': 0,
            'monthly_income': monthly_income, 'additional_income': additional_income_total,
            'total_income': total_income, 'current_month_expense': 0,
            'current_month_transaction_count': 0,
            'remaining_balance': total_income, 'savings_rate': 100.0,
            'category_breakdown': {}, 'monthly_trend': {}, 'payment_breakdown': {},
            'health_score': 50, 'health_score_grade': 'Fair',
            'health_score_breakdown': {'savings': 15, 'consistency': 10, 'balance': 7.5, 'budget_adherence': 7.5, 'emergency_readiness': 10},
            'rule_50_30_20': {'needs_pct': 0, 'wants_pct': 0, 'savings_pct': 100},
            'monthly_details': [], 'total_savings': 0,
            'has_health_insurance': user_health_ins, 'has_term_insurance': user_term_ins,
        })

    total_expense = float(df['amount'].sum())
    monthly_totals = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
    avg_monthly = float(monthly_totals.mean())
    num_months = len(monthly_totals)
    transaction_count = len(df)

    now = pd.Timestamp.now()
    current_month_df = df[df['date'].dt.to_period('M') == now.to_period('M')]
    current_month_expense = float(current_month_df['amount'].sum()) if not current_month_df.empty else 0.0
    current_month_transaction_count = len(current_month_df)

    remaining_balance = total_income - current_month_expense
    savings_rate = round((remaining_balance / total_income) * 100, 1) if total_income > 0 else 0
    total_savings = round((total_income * num_months) - total_expense, 2)

    category_breakdown = df.groupby('category')['amount'].sum().to_dict()
    monthly_trend = {str(k): float(v) for k, v in monthly_totals.items()}
    payment_breakdown = df.groupby('payment_mode')['amount'].sum().to_dict()

    # --- Health Score (same logic as SpendingAnalyst agent) ---
    cat_totals = df.groupby('category')['amount'].sum()
    total_spent = cat_totals.sum()

    avg_savings_rate = ((total_income - avg_monthly) / total_income * 100) if total_income > 0 else 0
    savings_score = min(30, max(0, avg_savings_rate * 0.6))

    if num_months >= 2:
        volatility = float(monthly_totals.std() / monthly_totals.mean()) if monthly_totals.mean() > 0 else 1
        consistency_score = max(0, 20 - (volatility * 20))
    else:
        consistency_score = 10

    max_cat_pct = float(cat_totals.max() / total_spent * 100) if total_spent > 0 else 0
    balance_score = max(0, 15 - max(0, (max_cat_pct - 30) * 0.3))

    db = get_db()
    budgets = db.execute('SELECT category, monthly_limit FROM budgets WHERE user_id = ?', (g.user_id,)).fetchall()
    db.close()
    if budgets and not current_month_df.empty:
        hits = sum(1 for b in budgets if current_month_df[current_month_df['category'] == b['category']]['amount'].sum() <= b['monthly_limit'])
        adherence_score = (hits / len(budgets)) * 15
    else:
        adherence_score = 7.5

    monthly_savings_amt = total_income - avg_monthly
    months_saved = (monthly_savings_amt * num_months) / avg_monthly if avg_monthly > 0 else 0
    emergency_score = min(20, months_saved * 3.3)

    health_score = round(min(100, max(0, savings_score + consistency_score + balance_score + adherence_score + emergency_score)))
    health_grade = 'Excellent' if health_score >= 80 else 'Good' if health_score >= 60 else 'Fair' if health_score >= 40 else 'Needs Attention'

    # --- 50/30/20 Rule ---
    NEEDS = {'Food', 'Bills', 'Healthcare', 'Transport', 'Education'}
    WANTS = {'Shopping', 'Entertainment', 'Other'}
    needs_total = sum(cat_totals.get(c, 0) for c in NEEDS)
    wants_total = sum(cat_totals.get(c, 0) for c in WANTS)
    income_basis = total_income * max(num_months, 1)
    if income_basis > 0:
        needs_pct = round((needs_total / income_basis) * 100, 1)
        wants_pct = round((wants_total / income_basis) * 100, 1)
        savings_pct = round(max(0, 100 - needs_pct - wants_pct), 1)
    else:
        needs_pct = wants_pct = savings_pct = 0

    # --- Monthly Details (for comparison feature) ---
    sorted_periods = sorted(monthly_totals.index)

    def fmt_period(p):
        parts = str(p).split('-')
        month_names_list = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        return month_names_list[int(parts[1]) - 1] + ' ' + parts[0][2:]

    monthly_details = []
    for period in sorted_periods:
        p_df = df[df['date'].dt.to_period('M') == period]
        p_cats = p_df.groupby('category')['amount'].sum()
        monthly_details.append({
            'key': str(period),
            'label': fmt_period(period),
            'total': round(float(monthly_totals[period]), 2),
            'txn_count': len(p_df),
            'categories': {k: round(float(v), 2) for k, v in p_cats.items()},
        })

    return jsonify({
        'total_expense': round(total_expense, 2),
        'avg_monthly_expense': round(avg_monthly, 2),
        'transaction_count': transaction_count,
        'monthly_income': monthly_income,
        'additional_income': round(additional_income_total, 2),
        'total_income': round(total_income, 2),
        'current_month_expense': round(current_month_expense, 2),
        'current_month_transaction_count': current_month_transaction_count,
        'remaining_balance': round(remaining_balance, 2),
        'savings_rate': savings_rate,
        'category_breakdown': {k: round(v, 2) for k, v in category_breakdown.items()},
        'monthly_trend': {k: round(v, 2) for k, v in monthly_trend.items()},
        'payment_breakdown': {k: round(v, 2) for k, v in payment_breakdown.items()},
        'health_score': health_score,
        'health_score_grade': health_grade,
        'health_score_breakdown': {
            'savings': round(savings_score, 1),
            'consistency': round(consistency_score, 1),
            'balance': round(balance_score, 1),
            'budget_adherence': round(adherence_score, 1),
            'emergency_readiness': round(emergency_score, 1),
        },
        'rule_50_30_20': {
            'needs_pct': needs_pct,
            'wants_pct': wants_pct,
            'savings_pct': savings_pct,
        },
        'monthly_details': monthly_details,
        'total_savings': total_savings,
        'has_health_insurance': user_health_ins,
        'has_term_insurance': user_term_ins,
    })


# =============================================
# AI INSIGHTS (Replaces ML Predictions)
# =============================================

@app.route('/api/ai-insights', methods=['GET'])
@login_required
def get_ai_insights():
    """AI-powered financial insights using statistical analysis."""
    monthly_income, additional_income, total_income = get_user_income_data(g.user_id)
    df = load_transactions_for_user(g.user_id)

    if df.empty:
        return jsonify({'error': 'No transactions found. Add expenses first.'}), 404

    now = pd.Timestamp.now()
    monthly_totals = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
    num_months = len(monthly_totals)
    avg_monthly_expense = float(monthly_totals.mean())

    # --- 1. Financial Health Score (0-100) ---
    current_month_df = df[df['date'].dt.to_period('M') == now.to_period('M')]
    current_month_expense = float(current_month_df['amount'].sum()) if not current_month_df.empty else 0.0

    # Savings Rate Score (30 points)
    savings_rate = ((total_income - avg_monthly_expense) / total_income * 100) if total_income > 0 else 0
    savings_score = min(30, max(0, savings_rate * 0.6))

    # Spending Consistency Score (20 points) — lower volatility is better
    if num_months >= 2:
        volatility = float(monthly_totals.std() / monthly_totals.mean()) if monthly_totals.mean() > 0 else 1
        consistency_score = max(0, 20 - (volatility * 20))
    else:
        consistency_score = 10

    # Category Balance Score (15 points) — no single category > 50%
    category_totals = df.groupby('category')['amount'].sum()
    total_spent = category_totals.sum()
    if total_spent > 0:
        max_category_pct = float(category_totals.max() / total_spent * 100)
        balance_score = max(0, 15 - max(0, (max_category_pct - 30) * 0.3))
    else:
        balance_score = 7.5

    # Budget Adherence Score (15 points)
    db = get_db()
    budgets = db.execute('SELECT category, monthly_limit FROM budgets WHERE user_id = ?', (g.user_id,)).fetchall()
    db.close()
    if budgets:
        budget_hits = 0
        for b in budgets:
            cat_month = current_month_df[current_month_df['category'] == b['category']]['amount'].sum() if not current_month_df.empty else 0
            if cat_month <= b['monthly_limit']:
                budget_hits += 1
        adherence_score = (budget_hits / len(budgets)) * 15
    else:
        adherence_score = 7.5  # neutral if no budgets set

    # Emergency Fund Readiness (20 points)
    monthly_savings_amt = total_income - avg_monthly_expense
    months_of_savings = (monthly_savings_amt * num_months) / avg_monthly_expense if avg_monthly_expense > 0 else 0
    emergency_score = min(20, months_of_savings * 3.3)

    health_score = round(min(100, max(0, savings_score + consistency_score + balance_score + adherence_score + emergency_score)))
    health_grade = 'Excellent' if health_score >= 80 else 'Good' if health_score >= 60 else 'Fair' if health_score >= 40 else 'Needs Attention'

    # --- 2. Spending Forecast (3-month moving average) ---
    if num_months >= 3:
        last_3 = monthly_totals.tail(3).values
        predicted_next_month = round(float(np.mean(last_3)), 2)
        trend_pct = round(float((last_3[-1] - last_3[0]) / last_3[0] * 100), 1) if last_3[0] > 0 else 0
    elif num_months >= 1:
        predicted_next_month = round(float(monthly_totals.tail(1).values[0]), 2)
        trend_pct = 0
    else:
        predicted_next_month = 0
        trend_pct = 0

    # --- 3. Spending Anomalies ---
    anomalies = []
    if num_months >= 3:
        mean_spending = float(monthly_totals.mean())
        std_spending = float(monthly_totals.std())
        threshold = mean_spending + (1.5 * std_spending)
        for period, amount in monthly_totals.items():
            if float(amount) > threshold:
                anomalies.append({
                    'month': str(period),
                    'amount': round(float(amount), 2),
                    'average': round(mean_spending, 2),
                    'excess': round(float(amount) - mean_spending, 2)
                })

    # --- 4. Category Insights ---
    category_insights = []
    category_percentages = ((category_totals / total_spent) * 100).to_dict() if total_spent > 0 else {}

    ideal_ranges = {
        'Food': (20, 35), 'Transport': (5, 15), 'Shopping': (5, 20),
        'Bills': (15, 30), 'Entertainment': (3, 10), 'Healthcare': (3, 10),
        'Education': (3, 15), 'Other': (0, 15)
    }

    for cat, pct in category_percentages.items():
        low, high = ideal_ranges.get(cat, (0, 25))
        status = 'optimal' if low <= pct <= high else ('high' if pct > high else 'low')
        category_insights.append({
            'category': cat,
            'percentage': round(pct, 1),
            'amount': round(float(category_totals.get(cat, 0)), 2),
            'ideal_range': f'{low}-{high}%',
            'status': status
        })

    category_insights.sort(key=lambda x: x['percentage'], reverse=True)

    # --- 5. Monthly Comparison ---
    monthly_comparison = []
    monthly_list = [(str(k), float(v)) for k, v in monthly_totals.items()]
    for i, (month, amount) in enumerate(monthly_list):
        change = round(amount - monthly_list[i - 1][1], 2) if i > 0 else 0
        change_pct = round((change / monthly_list[i - 1][1]) * 100, 1) if i > 0 and monthly_list[i - 1][1] > 0 else 0
        monthly_comparison.append({
            'month': month, 'amount': round(amount, 2),
            'change': change, 'change_pct': change_pct
        })

    # --- 6. Smart Tips ---
    tips = []
    if savings_rate < 10:
        tips.append({'type': 'warning', 'message': f'Your savings rate is only {savings_rate:.0f}%. Aim for at least 20% to build financial security.'})
    elif savings_rate >= 30:
        tips.append({'type': 'success', 'message': f'Great savings rate of {savings_rate:.0f}%! Consider increasing your investments.'})

    if trend_pct > 15:
        tips.append({'type': 'warning', 'message': f'Spending is trending up {trend_pct}% over the last 3 months. Review recent expenses.'})
    elif trend_pct < -10:
        tips.append({'type': 'success', 'message': f'Spending decreased by {abs(trend_pct)}%. Your cost-cutting efforts are working!'})

    for ci in category_insights[:3]:
        if ci['status'] == 'high':
            tips.append({'type': 'info', 'message': f'{ci["category"]} spending is {ci["percentage"]:.0f}% (ideal: {ci["ideal_range"]}). Look for ways to optimize.'})

    if not budgets:
        tips.append({'type': 'info', 'message': 'Set category budgets to get better financial control and tracking.'})

    if len(anomalies) > 0:
        tips.append({'type': 'warning', 'message': f'Found {len(anomalies)} unusual spending month(s). Review them in the anomalies section.'})

    # --- 7. Risk Level ---
    if savings_rate >= 30 and health_score >= 70:
        risk_level = 'Low'
    elif savings_rate >= 10 and health_score >= 40:
        risk_level = 'Medium'
    else:
        risk_level = 'High'

    return jsonify({
        'health_score': health_score,
        'health_grade': health_grade,
        'score_breakdown': {
            'savings': round(savings_score, 1),
            'consistency': round(consistency_score, 1),
            'balance': round(balance_score, 1),
            'budget_adherence': round(adherence_score, 1),
            'emergency_readiness': round(emergency_score, 1)
        },
        'risk_level': risk_level,
        'predicted_next_month': predicted_next_month,
        'spending_trend_pct': trend_pct,
        'anomalies': anomalies,
        'category_insights': category_insights,
        'monthly_comparison': monthly_comparison[-12:],
        'tips': tips,
        'total_income': round(total_income, 2),
        'avg_monthly_expense': round(avg_monthly_expense, 2),
        'savings_rate': round(savings_rate, 1)
    })


# =============================================
# BUDGET MANAGER
# =============================================

@app.route('/api/budgets', methods=['GET'])
@login_required
def get_budgets():
    """Get all budgets with current month progress."""
    db = get_db()
    budgets = db.execute('SELECT id, category, monthly_limit FROM budgets WHERE user_id = ?', (g.user_id,)).fetchall()
    db.close()

    df = load_transactions_for_user(g.user_id)
    now = pd.Timestamp.now()
    current_month_df = df[df['date'].dt.to_period('M') == now.to_period('M')] if not df.empty else pd.DataFrame()

    result = []
    for b in budgets:
        spent = float(current_month_df[current_month_df['category'] == b['category']]['amount'].sum()) if not current_month_df.empty else 0
        limit = b['monthly_limit']
        pct = round((spent / limit) * 100, 1) if limit > 0 else 0
        result.append({
            'id': b['id'], 'category': b['category'],
            'monthly_limit': limit, 'spent': round(spent, 2),
            'remaining': round(limit - spent, 2),
            'percentage': pct,
            'status': 'over' if pct > 100 else ('warning' if pct > 80 else 'good')
        })

    return jsonify(result)


@app.route('/api/budgets', methods=['POST'])
@login_required
def add_budget():
    data = request.json
    category = data.get('category', '').strip()
    monthly_limit = data.get('monthly_limit')

    if not category or not monthly_limit:
        return jsonify({'error': 'Category and monthly limit are required'}), 400
    if float(monthly_limit) <= 0:
        return jsonify({'error': 'Budget limit must be positive'}), 400

    db = get_db()
    existing = db.execute('SELECT id FROM budgets WHERE user_id = ? AND category = ?', (g.user_id, category)).fetchone()
    if existing:
        db.execute('UPDATE budgets SET monthly_limit = ? WHERE id = ?', (float(monthly_limit), existing['id']))
    else:
        db.execute('INSERT INTO budgets (user_id, category, monthly_limit) VALUES (?, ?, ?)',
                   (g.user_id, category, float(monthly_limit)))
    db.commit()
    db.close()
    return jsonify({'message': f'Budget for {category} saved'}), 201


@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    db = get_db()
    row = db.execute('SELECT id FROM budgets WHERE id = ? AND user_id = ?', (budget_id, g.user_id)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Budget not found'}), 404
    db.execute('DELETE FROM budgets WHERE id = ?', (budget_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Budget deleted'})


# =============================================
# INSURANCE PLANNER
# =============================================

@app.route('/api/insurance-suggestions', methods=['GET'])
@login_required
def get_insurance_suggestions():
    """Generate personalized health and term insurance suggestions."""
    db = get_db()
    user = db.execute(
        'SELECT monthly_income, age, dependents, has_health_insurance, has_term_insurance FROM users WHERE id = ?',
        (g.user_id,)
    ).fetchone()
    db.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    age = user['age'] or 25
    dependents = user['dependents'] or 0
    monthly_income = user['monthly_income'] or 50000
    annual_income = monthly_income * 12
    has_health = bool(user['has_health_insurance'])
    has_term = bool(user['has_term_insurance'])
    family_size = 1 + dependents

    # --- TERM INSURANCE ---
    term_plans = []
    if not has_term:
        # Coverage: 10-15x annual income
        coverage_low = annual_income * 10
        coverage_high = annual_income * 15
        recommended_coverage = annual_income * 12

        # Premium estimate based on age (per lakh per year)
        if age < 25:
            rate_per_lakh = 8
        elif age < 30:
            rate_per_lakh = 10
        elif age < 35:
            rate_per_lakh = 14
        elif age < 40:
            rate_per_lakh = 20
        elif age < 45:
            rate_per_lakh = 30
        elif age < 50:
            rate_per_lakh = 45
        else:
            rate_per_lakh = 70

        est_annual_premium = (recommended_coverage / 100000) * rate_per_lakh
        est_monthly_premium = round(est_annual_premium / 12)

        term_plans.append({
            'name': 'Pure Term Life Insurance',
            'priority': 'critical',
            'coverage_recommended': recommended_coverage,
            'coverage_range': f'Rs. {coverage_low / 100000:.0f} Lakhs - Rs. {coverage_high / 100000:.0f} Lakhs',
            'est_monthly_premium': est_monthly_premium,
            'est_annual_premium': round(est_annual_premium),
            'why': f'At age {age} with {dependents} dependent(s), you need at least 10-15x your annual income as life cover to protect your family.',
            'features': [
                'Covers death due to any cause',
                'Payout as lump sum or monthly income to nominee',
                f'Tax benefit under Section 80C up to Rs. 1.5 Lakhs/year',
                'Lock in lower premiums at younger age',
                f'Recommended tenure: till age 60-65 ({max(60 - age, 15)} years)'
            ],
            'top_providers': ['LIC e-Term', 'HDFC Click 2 Protect', 'ICICI iProtect Smart', 'Max Life Smart Secure Plus', 'Tata AIA Sampoorna Raksha']
        })

        if dependents > 0:
            term_plans.append({
                'name': 'Term Plan with Return of Premium',
                'priority': 'medium',
                'coverage_recommended': recommended_coverage,
                'est_monthly_premium': round(est_monthly_premium * 1.8),
                'est_annual_premium': round(est_annual_premium * 1.8),
                'why': 'If you survive the policy term, you get all premiums back. Good for those who want insurance + savings.',
                'features': [
                    'All premiums returned if you survive the term',
                    'Same death benefit as pure term plan',
                    'Higher premium than pure term but money is not "lost"',
                    'Good option if you are risk-averse'
                ],
                'top_providers': ['HDFC Click 2 Protect 3D Plus', 'ICICI Pru iProtect Return of Premium', 'SBI Life eShield Next']
            })
    else:
        term_plans.append({
            'name': 'You already have Term Insurance',
            'priority': 'done',
            'why': f'Great! Make sure your coverage is at least Rs. {annual_income * 10 / 100000:.0f} Lakhs (10x your annual income). Review your plan annually as your income grows.',
            'features': [
                'Review coverage adequacy every 2-3 years',
                'Increase cover if income or dependents increase',
                'Consider adding critical illness rider',
                'Ensure nominee details are up to date'
            ],
            'top_providers': []
        })

    # --- HEALTH INSURANCE ---
    health_plans = []
    if not has_health:
        if family_size == 1:
            cover_low = 500000
            cover_high = 1000000
            recommended_cover = 500000
        elif family_size <= 3:
            cover_low = 500000
            cover_high = 1500000
            recommended_cover = 1000000
        else:
            cover_low = 1000000
            cover_high = 2500000
            recommended_cover = 1500000

        # Premium estimate based on age and family size
        base_premium = 5000 if age < 30 else 8000 if age < 40 else 12000 if age < 50 else 18000
        family_multiplier = 1.0 if family_size == 1 else 1.7 if family_size <= 3 else 2.3
        cover_multiplier = recommended_cover / 500000
        est_annual_premium = round(base_premium * family_multiplier * cover_multiplier)
        est_monthly_premium = round(est_annual_premium / 12)

        health_plans.append({
            'name': 'Comprehensive Health Insurance',
            'priority': 'critical',
            'coverage_recommended': recommended_cover,
            'coverage_range': f'Rs. {cover_low / 100000:.0f} Lakhs - Rs. {cover_high / 100000:.0f} Lakhs',
            'est_monthly_premium': est_monthly_premium,
            'est_annual_premium': est_annual_premium,
            'family_size': family_size,
            'why': f'Medical emergencies can cost lakhs. With {family_size} family member(s), a health cover of Rs. {recommended_cover / 100000:.0f} Lakhs protects against financial ruin.',
            'features': [
                'Cashless treatment at 5000+ network hospitals',
                'Pre and post-hospitalization expenses covered',
                'Day-care procedures covered',
                f'Tax benefit under Section 80D up to Rs. {25000 if age < 60 else 50000}/year',
                'No-claim bonus increases cover each year',
                f'Covers {family_size} family member(s)'
            ],
            'top_providers': ['Star Health', 'Niva Bupa (formerly Max Bupa)', 'HDFC ERGO Optima Secure', 'Care Health', 'ICICI Lombard']
        })

        # Super Top-up
        if monthly_income >= 40000:
            health_plans.append({
                'name': 'Super Top-Up Plan',
                'priority': 'recommended',
                'coverage_recommended': recommended_cover * 3,
                'est_monthly_premium': round(est_monthly_premium * 0.3),
                'est_annual_premium': round(est_annual_premium * 0.3),
                'why': 'A Super Top-Up adds extra coverage at a fraction of the cost. Activates when your base policy limit is exhausted.',
                'features': [
                    f'Additional cover of Rs. {recommended_cover * 3 / 100000:.0f} Lakhs',
                    'Very affordable premium — 70% cheaper than base plans',
                    'Ideal safety net for major surgeries or critical illness',
                    'Works on top of your employer or base health insurance'
                ],
                'top_providers': ['HDFC ERGO', 'ICICI Lombard', 'Star Health', 'Care Health']
            })

        # Critical Illness
        if age >= 30:
            health_plans.append({
                'name': 'Critical Illness Cover',
                'priority': 'medium',
                'coverage_recommended': 1000000,
                'est_monthly_premium': round(800 if age < 40 else 1500),
                'est_annual_premium': round(9600 if age < 40 else 18000),
                'why': 'Pays a lump sum on diagnosis of critical illnesses like cancer, heart attack, stroke. This money covers lost income during recovery.',
                'features': [
                    'Lump-sum payout on diagnosis',
                    'Covers 30+ critical illnesses',
                    'No bills needed — amount paid on diagnosis',
                    'Covers lost income during treatment and recovery'
                ],
                'top_providers': ['HDFC Life Critical Illness', 'Max Life Critical Illness', 'ICICI Pru Heart/Cancer Protect']
            })
    else:
        health_plans.append({
            'name': 'You already have Health Insurance',
            'priority': 'done',
            'why': 'Ensure your cover is adequate for your family size. Consider a Super Top-Up for additional protection.',
            'features': [
                f'Recommended minimum: Rs. {(500000 * max(1, family_size * 0.5)) / 100000:.0f} Lakhs for {family_size} member(s)',
                'Review and port your policy if premiums increase too much',
                'Add Super Top-Up for extra protection at low cost',
                'Check if critical illness rider is included'
            ],
            'top_providers': []
        })

    # Total insurance budget recommendation
    total_insurance_monthly = sum(p.get('est_monthly_premium', 0) for p in term_plans + health_plans if p.get('priority') != 'done')
    insurance_as_pct = round((total_insurance_monthly / monthly_income) * 100, 1) if monthly_income > 0 else 0

    return jsonify({
        'user_profile': {
            'age': age, 'dependents': dependents, 'family_size': family_size,
            'monthly_income': monthly_income, 'annual_income': annual_income,
            'has_health_insurance': has_health, 'has_term_insurance': has_term
        },
        'term_insurance': term_plans,
        'health_insurance': health_plans,
        'total_monthly_premium': total_insurance_monthly,
        'insurance_as_income_pct': insurance_as_pct,
        'recommendation': f'Spend about {min(insurance_as_pct + 1, 5)}% of your income on insurance premiums for comprehensive protection.'
    })


# =============================================
# INVESTMENT SUGGESTIONS
# =============================================

@app.route('/api/investment-suggestions', methods=['GET'])
@login_required
def get_investment_suggestions():
    monthly_income, additional_income_total, total_income = get_user_income_data(g.user_id)
    df = load_transactions_for_user(g.user_id)

    if df.empty:
        return jsonify({'error': 'No transactions found. Add expenses first.'}), 404

    now = pd.Timestamp.now()
    current_month_df = df[df['date'].dt.to_period('M') == now.to_period('M')]
    current_month_expense = float(current_month_df['amount'].sum()) if not current_month_df.empty else 0.0

    avg_monthly_expense = float(df.groupby(df['date'].dt.to_period('M'))['amount'].sum().mean())
    monthly_savings = total_income - avg_monthly_expense
    savings_rate = (monthly_savings / total_income * 100) if total_income > 0 else 0
    remaining_balance = total_income - current_month_expense

    category_totals = df.groupby('category')['amount'].sum()
    total_spent = category_totals.sum()
    category_percentages = ((category_totals / total_spent) * 100).to_dict() if total_spent > 0 else {}

    top_category = category_totals.idxmax() if not category_totals.empty else 'Unknown'
    top_category_pct = round(category_percentages.get(top_category, 0), 1)

    monthly_totals = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
    if len(monthly_totals) >= 2:
        recent_trend = float(monthly_totals.iloc[-1]) - float(monthly_totals.iloc[-2])
        trend_direction = 'increasing' if recent_trend > 0 else 'decreasing'
    else:
        recent_trend = 0
        trend_direction = 'stable'

    suggestions = []

    emergency_target = avg_monthly_expense * 6
    suggestions.append({
        'title': 'Emergency Fund', 'icon': 'shield', 'priority': 'high',
        'description': f'Build an emergency fund of Rs. {emergency_target:,.0f} (6 months of expenses). Keep in a high-interest savings account or liquid mutual fund.',
        'action': f'Save Rs. {min(monthly_savings * 0.3, emergency_target / 12):,.0f}/month towards this goal.',
        'amount': round(min(monthly_savings * 0.3, emergency_target / 12), 0)
    })

    if savings_rate >= 30:
        suggestions.append({
            'title': 'Equity Mutual Funds (SIP)', 'icon': 'trending-up', 'priority': 'high',
            'description': f'Savings rate is {savings_rate:.0f}% — excellent! Invest in index funds like Nifty 50 for long-term wealth.',
            'action': f'Start a SIP of Rs. {monthly_savings * 0.4:,.0f}/month.',
            'amount': round(monthly_savings * 0.4, 0)
        })
        suggestions.append({
            'title': 'Public Provident Fund (PPF)', 'icon': 'lock', 'priority': 'medium',
            'description': 'PPF offers ~7.1% tax-free returns with government backing. Max Rs. 1,50,000/year under Section 80C.',
            'action': f'Invest Rs. {min(monthly_savings * 0.15, 12500):,.0f}/month.',
            'amount': round(min(monthly_savings * 0.15, 12500), 0)
        })
    elif savings_rate >= 15:
        suggestions.append({
            'title': 'Balanced Mutual Funds', 'icon': 'trending-up', 'priority': 'high',
            'description': f'{savings_rate:.0f}% savings rate — start with balanced funds mixing equity and debt.',
            'action': f'SIP of Rs. {monthly_savings * 0.35:,.0f}/month.',
            'amount': round(monthly_savings * 0.35, 0)
        })
    else:
        suggestions.append({
            'title': 'Recurring Deposit', 'icon': 'piggy-bank', 'priority': 'high',
            'description': f'Savings rate is {savings_rate:.0f}%. Start with a safe RD to build the saving habit.',
            'action': f'Open an RD of Rs. {max(monthly_savings * 0.3, 500):,.0f}/month.',
            'amount': round(max(monthly_savings * 0.3, 500), 0)
        })

    if remaining_balance > monthly_income * 0.2:
        suggestions.append({
            'title': 'Fixed Deposit', 'icon': 'bank', 'priority': 'medium',
            'description': 'Park excess funds in an FD earning 7-8% interest.',
            'action': f'Deposit Rs. {remaining_balance * 0.3:,.0f} in an FD.',
            'amount': round(remaining_balance * 0.3, 0)
        })

    if monthly_savings > 5000:
        suggestions.append({
            'title': 'Digital Gold / Gold ETF', 'icon': 'award', 'priority': 'low',
            'description': 'Allocate 5-10% to gold as an inflation hedge.',
            'action': f'Invest Rs. {monthly_savings * 0.05:,.0f}/month in Gold ETF.',
            'amount': round(monthly_savings * 0.05, 0)
        })

    spending_tips = []
    if category_percentages.get('Food', 0) > 35:
        spending_tips.append(f'Food is {category_percentages["Food"]:.0f}% of spending. Try meal planning.')
    if category_percentages.get('Entertainment', 0) > 15:
        spending_tips.append(f'Entertainment is {category_percentages["Entertainment"]:.0f}%. Review subscriptions.')
    if category_percentages.get('Shopping', 0) > 25:
        spending_tips.append(f'Shopping is {category_percentages["Shopping"]:.0f}%. Use the 24-hour rule.')
    if trend_direction == 'increasing':
        spending_tips.append(f'Spending rose by Rs. {abs(recent_trend):,.0f} last month.')
    if not spending_tips:
        spending_tips.append('Spending is well balanced. Keep it up!')

    total_investable = max(monthly_savings, 0)
    allocation = {
        'Emergency Fund': round(total_investable * 0.20),
        'Equity/Mutual Funds': round(total_investable * 0.40),
        'Fixed Income (PPF/FD)': round(total_investable * 0.25),
        'Gold': round(total_investable * 0.05),
        'Flexible Savings': round(total_investable * 0.10)
    }

    return jsonify({
        'monthly_income': monthly_income, 'additional_income': round(additional_income_total, 2),
        'total_income': round(total_income, 2), 'avg_monthly_expense': round(avg_monthly_expense, 2),
        'monthly_savings': round(monthly_savings, 2), 'savings_rate': round(savings_rate, 1),
        'remaining_balance': round(remaining_balance, 2), 'top_spending_category': top_category,
        'top_spending_percentage': top_category_pct, 'trend_direction': trend_direction,
        'suggestions': suggestions, 'spending_tips': spending_tips,
        'recommended_allocation': allocation
    })


# =============================================
# AI AGENT ENDPOINTS
# =============================================

def _build_user_context(user_id):
    """Build context dict consumed by all agents."""
    monthly_income, additional_income, total_income = get_user_income_data(user_id)
    db = get_db()
    budgets = [dict(r) for r in db.execute(
        'SELECT category, monthly_limit FROM budgets WHERE user_id = ?', (user_id,)
    ).fetchall()]
    goals = [dict(r) for r in db.execute(
        'SELECT * FROM financial_goals WHERE user_id = ? AND status = ?', (user_id, 'active')
    ).fetchall()]
    # Try to read CFP profile columns (may not exist in older schemas)
    try:
        user = db.execute(
            'SELECT age, dependents, has_health_insurance, has_term_insurance FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        age = user['age'] if user else 25
        dependents = user['dependents'] if user else 0
        has_health = bool(user['has_health_insurance']) if user else False
        has_term = bool(user['has_term_insurance']) if user else False
    except Exception:
        age, dependents, has_health, has_term = 25, 0, False, False
    db.close()
    return {
        'user_id': user_id,
        'monthly_income': monthly_income,
        'additional_income': additional_income,
        'total_income': total_income,
        'budgets': budgets,
        'goals': goals,
        'age': age,
        'dependents': dependents,
        'has_health_insurance': has_health,
        'has_term_insurance': has_term,
    }


@app.route('/api/agents/insights', methods=['GET'])
@login_required
def get_agent_insights():
    """Run all AI agents and return prioritized insights."""
    df = load_transactions_for_user(g.user_id)
    ctx = _build_user_context(g.user_id)
    orchestrator = AgentOrchestrator()
    result = orchestrator.run_all(df, ctx)
    return jsonify(result)


@app.route('/api/agents/status', methods=['GET'])
@login_required
def get_agent_statuses():
    """Get the status of all AI agents."""
    orchestrator = AgentOrchestrator()
    return jsonify(orchestrator.get_agent_statuses())


# =============================================
# FINANCIAL GOALS
# =============================================

@app.route('/api/goals', methods=['GET'])
@login_required
def get_goals():
    db = get_db()
    rows = db.execute(
        'SELECT * FROM financial_goals WHERE user_id = ? ORDER BY status ASC, created_at DESC',
        (g.user_id,)
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/goals', methods=['POST'])
@login_required
def create_goal():
    data = request.json
    name = data.get('name', '').strip()
    target = data.get('target_amount')

    if not name or not target or float(target) <= 0:
        return jsonify({'error': 'Name and a positive target amount are required'}), 400

    db = get_db()
    db.execute(
        'INSERT INTO financial_goals (user_id, name, target_amount, deadline, icon, color) VALUES (?, ?, ?, ?, ?, ?)',
        (g.user_id, name, float(target),
         data.get('deadline', ''), data.get('icon', 'target'), data.get('color', '#00b894'))
    )
    db.commit()
    db.close()
    return jsonify({'message': f'Goal "{name}" created!'}), 201


@app.route('/api/goals/<int:goal_id>', methods=['PUT'])
@login_required
def update_goal(goal_id):
    db = get_db()
    row = db.execute('SELECT id FROM financial_goals WHERE id = ? AND user_id = ?', (goal_id, g.user_id)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Goal not found'}), 404

    data = request.json
    fields, values = [], []
    for f in ['name', 'target_amount', 'current_amount', 'deadline', 'icon', 'color', 'status']:
        if f in data:
            fields.append(f'{f} = ?')
            values.append(data[f])
    if not fields:
        db.close()
        return jsonify({'error': 'No fields to update'}), 400

    fields.append('updated_at = ?')
    values.append(datetime.now().isoformat())
    values.append(goal_id)
    db.execute(f'UPDATE financial_goals SET {", ".join(fields)} WHERE id = ?', values)
    db.commit()
    db.close()
    return jsonify({'message': 'Goal updated'})


@app.route('/api/goals/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    db = get_db()
    row = db.execute('SELECT id FROM financial_goals WHERE id = ? AND user_id = ?', (goal_id, g.user_id)).fetchone()
    if not row:
        db.close()
        return jsonify({'error': 'Goal not found'}), 404
    db.execute('DELETE FROM financial_goals WHERE id = ?', (goal_id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Goal deleted'})


@app.route('/api/goals/<int:goal_id>/add-funds', methods=['PUT'])
@login_required
def add_funds_to_goal(goal_id):
    db = get_db()
    goal = db.execute('SELECT * FROM financial_goals WHERE id = ? AND user_id = ?', (goal_id, g.user_id)).fetchone()
    if not goal:
        db.close()
        return jsonify({'error': 'Goal not found'}), 404

    amount = request.json.get('amount', 0)
    if float(amount) <= 0:
        db.close()
        return jsonify({'error': 'Amount must be positive'}), 400

    new_current = goal['current_amount'] + float(amount)
    new_status = 'completed' if new_current >= goal['target_amount'] else 'active'
    db.execute(
        'UPDATE financial_goals SET current_amount = ?, status = ?, updated_at = ? WHERE id = ?',
        (new_current, new_status, datetime.now().isoformat(), goal_id)
    )
    db.commit()
    db.close()
    return jsonify({
        'message': f'Added Rs. {float(amount):,.0f} to goal',
        'current_amount': round(new_current, 2),
        'status': new_status
    })


# =============================================
# RECURRING BILLS
# =============================================

@app.route('/api/recurring-bills', methods=['GET'])
@login_required
def get_recurring_bills():
    db = get_db()
    rows = db.execute(
        'SELECT * FROM recurring_bills WHERE user_id = ? AND is_active = 1 ORDER BY expected_day ASC',
        (g.user_id,)
    ).fetchall()
    db.close()

    now = datetime.now()
    bills = []
    for r in rows:
        bill = dict(r)
        exp_day = bill.get('expected_day') or 1
        days_until = exp_day - now.day
        if days_until < 0:
            days_until += 30  # next month
        bill['days_until'] = days_until
        bills.append(bill)

    return jsonify(bills)


# =============================================
# SMART PARSE (Natural Language Transaction)
# =============================================

CATEGORY_KEYWORDS = {
    'Food': ['food', 'grocery', 'groceries', 'lunch', 'dinner', 'breakfast', 'snack',
             'restaurant', 'cafe', 'coffee', 'tea', 'meal', 'biryani', 'pizza', 'burger',
             'swiggy', 'zomato', 'eat', 'cook'],
    'Transport': ['transport', 'uber', 'ola', 'cab', 'taxi', 'metro', 'bus', 'fuel',
                  'petrol', 'diesel', 'parking', 'toll', 'train', 'flight', 'travel', 'ride'],
    'Shopping': ['shopping', 'amazon', 'flipkart', 'myntra', 'clothes', 'shoes', 'dress',
                 'shirt', 'electronics', 'gadget', 'buy', 'purchase', 'order', 'mall'],
    'Bills': ['bill', 'electricity', 'water', 'gas', 'internet', 'wifi', 'phone',
              'recharge', 'rent', 'emi', 'loan', 'insurance', 'maintenance'],
    'Entertainment': ['movie', 'netflix', 'spotify', 'game', 'concert', 'show',
                      'subscription', 'youtube', 'prime', 'hotstar', 'party', 'fun'],
    'Healthcare': ['doctor', 'hospital', 'medicine', 'pharmacy', 'medical', 'health',
                   'dentist', 'lab', 'test', 'checkup', 'clinic'],
    'Education': ['course', 'book', 'tuition', 'class', 'study', 'exam', 'school',
                  'college', 'university', 'udemy', 'coursera', 'learning'],
}

PAYMENT_KEYWORDS = {
    'UPI': ['upi', 'gpay', 'phonepe', 'paytm', 'google pay', 'bhim'],
    'Credit Card': ['credit card', 'credit', 'cc'],
    'Debit Card': ['debit card', 'debit', 'dc', 'card'],
    'Net Banking': ['net banking', 'netbanking', 'bank transfer', 'neft', 'imps'],
    'Cash': ['cash'],
}


def parse_transaction_text(text):
    """Parse natural language text into a transaction dict."""
    text_lower = text.lower().strip()

    # Extract amount
    amount = None
    amount_patterns = [
        r'rs\.?\s*([\d,]+(?:\.\d+)?)',
        r'inr\s*([\d,]+(?:\.\d+)?)',
        r'([\d,]+(?:\.\d+)?)\s*(?:rs|rupees|inr)',
        r'(?:spent|paid|cost|for)\s*([\d,]+(?:\.\d+)?)',
        r'^\s*([\d,]+(?:\.\d+)?)\s',
        r'\s([\d,]+(?:\.\d+)?)\s',
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, text_lower)
        if match:
            amount = float(match.group(1).replace(',', ''))
            break

    # Extract date
    today = datetime.now()
    date = today.strftime('%Y-%m-%d')
    if 'yesterday' in text_lower:
        date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'day before' in text_lower:
        date = (today - timedelta(days=2)).strftime('%Y-%m-%d')
    elif 'last week' in text_lower:
        date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    else:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if date_match:
            date = date_match.group(1)
        else:
            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', text)
            if date_match:
                d, m, y = date_match.groups()
                if len(y) == 2:
                    y = '20' + y
                date = f'{y}-{m.zfill(2)}-{d.zfill(2)}'

    # Extract category
    category = 'Other'
    best_match_count = 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > best_match_count:
            best_match_count = matches
            category = cat

    # Extract payment mode
    payment_mode = 'UPI'  # default
    for mode, keywords in PAYMENT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            payment_mode = mode
            break

    # Extract description (clean up the text)
    description = text.strip()

    return {
        'amount': amount,
        'date': date,
        'category': category,
        'payment_mode': payment_mode,
        'description': description,
        'parsed': amount is not None,
    }


@app.route('/api/smart-parse', methods=['POST'])
@login_required
def smart_parse():
    """Parse natural language into a transaction."""
    text = request.json.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    return jsonify(parse_transaction_text(text))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
