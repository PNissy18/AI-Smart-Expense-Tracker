import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LabelList
} from 'recharts';
import {
  FiDollarSign, FiTrendingUp, FiActivity, FiPocket,
  FiEdit3, FiCheck, FiPlus, FiTrash2, FiX, FiZap,
  FiChevronRight, FiAlertCircle, FiAlertTriangle, FiCheckCircle, FiInfo,
  FiUser, FiHeart, FiShield
} from 'react-icons/fi';
import { TbPigMoney } from 'react-icons/tb';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';
import '../styles/Dashboard.css';

const COLORS = ['#6c5ce7', '#00b894', '#fdcb6e', '#e17055', '#0984e3', '#d63031', '#e84393', '#636e72'];
const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const INCOME_SOURCES = ['Freelance', 'Bonus', 'Part-time Job', 'Gift', 'Rental', 'Interest', 'Refund', 'Other'];

function Dashboard() {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingIncome, setEditingIncome] = useState(false);
  const [incomeInput, setIncomeInput] = useState('');
  const [agentInsights, setAgentInsights] = useState([]);
  const [additionalIncomes, setAdditionalIncomes] = useState([]);
  const [showAddIncome, setShowAddIncome] = useState(false);
  const [newIncome, setNewIncome] = useState({
    date: new Date().toISOString().split('T')[0],
    amount: '',
    source: 'Freelance',
    description: ''
  });
  const [profile, setProfile] = useState(null);
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [profileForm, setProfileForm] = useState({ age: '', dependents: '', has_health_insurance: false, has_term_insurance: false });
  const [savingProfile, setSavingProfile] = useState(false);
  const [compareMonth1, setCompareMonth1] = useState(null);
  const [compareMonth2, setCompareMonth2] = useState(null);

  useEffect(() => {
    fetchDashboard();
    fetchAdditionalIncomes();
    fetchAgentInsights();
    fetchProfile();
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const response = await api.get('/dashboard');
      setDashboardData(response.data);
      setIncomeInput(response.data.monthly_income);
      setError(null);
    } catch (err) {
      setError('Could not load dashboard. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAdditionalIncomes = async () => {
    try {
      const response = await api.get('/additional-income');
      setAdditionalIncomes(response.data.incomes);
    } catch (err) { /* silently fail */ }
  };

  const fetchAgentInsights = async () => {
    try {
      const response = await api.get('/agents/insights');
      setAgentInsights(response.data.insights || []);
    } catch (err) { /* silently fail */ }
  };

  const fetchProfile = async () => {
    try {
      const response = await api.get('/user-profile');
      setProfile(response.data);
      setProfileForm({
        age: response.data.age || '',
        dependents: response.data.dependents || 0,
        has_health_insurance: response.data.has_health_insurance || false,
        has_term_insurance: response.data.has_term_insurance || false,
      });
    } catch (err) { /* silently fail */ }
  };

  const handleSaveProfile = async () => {
    if (!profileForm.age || parseInt(profileForm.age) < 18 || parseInt(profileForm.age) > 100) {
      toast.error('Please enter a valid age (18-100)');
      return;
    }
    try {
      setSavingProfile(true);
      await api.put('/user-profile', {
        age: parseInt(profileForm.age),
        dependents: parseInt(profileForm.dependents) || 0,
        has_health_insurance: profileForm.has_health_insurance,
        has_term_insurance: profileForm.has_term_insurance,
      });
      toast.success('Profile updated! Insurance suggestions will now be personalized.');
      setShowProfileForm(false);
      fetchProfile();
    } catch (err) {
      toast.error('Failed to update profile');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleUpdateIncome = async () => {
    try {
      await api.put('/income', { monthly_income: parseFloat(incomeInput) });
      toast.success('Monthly income updated!');
      setEditingIncome(false);
      fetchDashboard();
    } catch (err) {
      toast.error('Failed to update income');
    }
  };

  const handleAddAdditionalIncome = async () => {
    if (!newIncome.amount || parseFloat(newIncome.amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    try {
      await api.post('/additional-income', {
        date: newIncome.date,
        amount: parseFloat(newIncome.amount),
        source: newIncome.source,
        description: newIncome.description
      });
      toast.success('Additional income added!');
      setShowAddIncome(false);
      setNewIncome({ date: new Date().toISOString().split('T')[0], amount: '', source: 'Freelance', description: '' });
      fetchDashboard();
      fetchAdditionalIncomes();
    } catch (err) {
      toast.error('Failed to add income');
    }
  };

  const handleDeleteAdditionalIncome = async (id) => {
    try {
      await api.delete(`/additional-income/${id}`);
      toast.success('Income entry removed');
      fetchDashboard();
      fetchAdditionalIncomes();
    } catch (err) {
      toast.error('Failed to delete');
    }
  };

  if (loading) {
    return (<div className="page-container"><div className="loading-spinner"><div className="spinner"></div><p>Loading Dashboard...</p></div></div>);
  }
  if (error) {
    return (<div className="page-container"><div className="error-card"><h3>Connection Error</h3><p>{error}</p><button className="btn btn-primary" onClick={fetchDashboard}>Retry</button></div></div>);
  }

  const {
    total_expense, avg_monthly_expense, transaction_count,
    monthly_income, additional_income = 0, total_income,
    current_month_expense, current_month_transaction_count = 0,
    remaining_balance, savings_rate,
    category_breakdown = {}, monthly_trend = {}, payment_breakdown = {},
    health_score = 0, health_score_breakdown = {}, health_score_grade = '',
    rule_50_30_20 = null, monthly_details = [],
    total_savings = 0,
    has_health_insurance = false, has_term_insurance = false
  } = dashboardData;

  const isBalanceNegative = remaining_balance < 0;

  // Format month labels: "Jan 25" instead of "2025-01"
  const monthlyChartData = Object.entries(monthly_trend).map(([month, amount]) => {
    const parts = month.substring(0, 7).split('-');
    const short = MONTH_NAMES[parseInt(parts[1]) - 1] + ' ' + parts[0].slice(2);
    return { month: short, amount: Math.round(amount) };
  });

  // Compute date range for "all-time" charts
  const dataRange = monthly_details.length > 0
    ? `${monthly_details[0].label} – ${monthly_details[monthly_details.length - 1].label}`
    : '';

  const categoryTotal = Object.values(category_breakdown).reduce((a, b) => a + b, 0);
  const categoryChartData = Object.entries(category_breakdown).map(([name, value]) => ({
    name, value: Math.round(value), pct: categoryTotal > 0 ? ((value / categoryTotal) * 100).toFixed(1) : 0
  }));
  const paymentTotal = Object.values(payment_breakdown).reduce((a, b) => a + b, 0);
  const paymentChartData = Object.entries(payment_breakdown).map(([name, value]) => ({
    name, value: Math.round(value), pct: paymentTotal > 0 ? ((value / paymentTotal) * 100).toFixed(1) : 0
  }));

  const renderPieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, pct, name, index }) => {
    if (pct < 12) return null;
    const RADIAN = Math.PI / 180;
    const mid = (innerRadius + outerRadius) / 2;
    const x = cx + mid * Math.cos(-midAngle * RADIAN);
    const y = cy + mid * Math.sin(-midAngle * RADIAN);
    return (
      <text x={x} y={y} fill="#fff" textAnchor="middle"
        dominantBaseline="central" fontSize={11} fontWeight={700}>
        {pct}%
      </text>
    );
  };

  const healthColor = health_score >= 70 ? '#00b894' : health_score >= 40 ? '#fdcb6e' : '#d63031';

  const HEALTH_COMPONENT_INFO = {
    savings: { max: 30, icon: <FiDollarSign size={13} />, label: 'Savings', desc: 'Based on your savings rate. Save 20%+ of income to max this out.' },
    consistency: { max: 20, icon: <FiActivity size={13} />, label: 'Consistency', desc: 'How stable your spending is month-to-month. Less fluctuation = higher score.' },
    balance: { max: 15, icon: <FiPocket size={13} />, label: 'Balance', desc: 'How well you spread spending across categories. No single category should exceed 30%.' },
    budget_adherence: { max: 15, icon: <FiCheck size={13} />, label: 'Budget Adherence', desc: 'Percentage of budgets you stayed within this month. Set budgets to improve this.' },
    emergency_readiness: { max: 20, icon: <FiShield size={13} />, label: 'Emergency Fund', desc: 'Months of expenses saved for emergencies. Target: 6 months of expenses.' },
  };

  // Find weakest areas for tips
  const sortedBreakdown = Object.entries(health_score_breakdown)
    .map(([key, val]) => ({ key, val, max: HEALTH_COMPONENT_INFO[key]?.max || 20, pct: (val / (HEALTH_COMPONENT_INFO[key]?.max || 20)) * 100 }))
    .sort((a, b) => a.pct - b.pct);
  const weakestAreas = sortedBreakdown.filter(a => a.pct < 50).slice(0, 2);

  const getHealthTip = (key) => {
    const tips = {
      savings: 'Try the 50/30/20 rule: allocate 20% of income to savings each month.',
      consistency: 'Plan monthly budgets and avoid large impulse purchases to stabilize spending.',
      balance: 'Diversify spending - if one category dominates, look for ways to reduce it.',
      budget_adherence: 'Set realistic budgets for your top 3-4 spending categories.',
      emergency_readiness: 'Automate a small monthly transfer to a separate emergency fund.',
    };
    return tips[key] || '';
  };

  // Monthly comparison logic
  const last12 = monthly_details.slice(-12);
  const compM1 = compareMonth1 !== null ? compareMonth1 : (monthly_details.length >= 2 ? monthly_details.length - 2 : null);
  const compM2 = compareMonth2 !== null ? compareMonth2 : (monthly_details.length >= 1 ? monthly_details.length - 1 : null);
  const selectedPrev = compM1 !== null ? monthly_details[compM1] : null;
  const selectedCurr = compM2 !== null ? monthly_details[compM2] : null;

  let comparisonData = null;
  if (selectedPrev && selectedCurr && compM1 !== compM2) {
    const pTotal = selectedPrev.total;
    const cTotal = selectedCurr.total;
    const changePct = pTotal > 0 ? Math.round(((cTotal - pTotal) / pTotal) * 1000) / 10 : 0;
    const allCats = [...new Set([...Object.keys(selectedPrev.categories || {}), ...Object.keys(selectedCurr.categories || {})])];
    const catChanges = allCats.map(cat => {
      const p = (selectedPrev.categories || {})[cat] || 0;
      const c = (selectedCurr.categories || {})[cat] || 0;
      const pct = p > 0 ? Math.round(((c - p) / p) * 1000) / 10 : (c > 0 ? 100 : 0);
      return { category: cat, previous: p, current: c, change_pct: pct };
    }).sort((a, b) => Math.abs(b.change_pct) - Math.abs(a.change_pct));

    const insights = [];
    if (changePct > 10) insights.push(`Your spending increased by ${changePct}% from ${selectedPrev.label} to ${selectedCurr.label}. Review discretionary expenses.`);
    else if (changePct < -10) insights.push(`Great job! Spending decreased by ${Math.abs(changePct)}% from ${selectedPrev.label} to ${selectedCurr.label}.`);
    else insights.push(`Spending is stable (${changePct > 0 ? '+' : ''}${changePct}%) between ${selectedPrev.label} and ${selectedCurr.label}.`);

    catChanges.filter(c => c.change_pct > 15 && c.previous > 0).slice(0, 2).forEach(c =>
      insights.push(`${c.category} spending rose ${c.change_pct}% (Rs. ${c.previous.toLocaleString()} → Rs. ${c.current.toLocaleString()}).`)
    );
    catChanges.filter(c => c.change_pct < -15 && c.previous > 0).slice(0, 2).forEach(c =>
      insights.push(`${c.category} spending dropped ${Math.abs(c.change_pct)}% (Rs. ${c.previous.toLocaleString()} → Rs. ${c.current.toLocaleString()}).`)
    );

    comparisonData = {
      prev: selectedPrev, curr: selectedCurr,
      change_pct: changePct, category_changes: catChanges.slice(0, 8), insights,
    };
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Welcome, {user.name}!</h1>
        <p className="subtitle">Your financial overview at a glance</p>
      </div>

      {/* Income & Balance Banner */}
      <div className="income-banner">
        <div className="income-left">
          <span className="income-label">Monthly Salary</span>
          {editingIncome ? (
            <div className="income-edit-row">
              <span className="income-rs">Rs.</span>
              <input type="number" className="income-input" value={incomeInput}
                onChange={(e) => setIncomeInput(e.target.value)} autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleUpdateIncome()} />
              <button className="income-save-btn" onClick={handleUpdateIncome}><FiCheck size={16} /></button>
            </div>
          ) : (
            <div className="income-display-row">
              <span className="income-value">Rs. {monthly_income.toLocaleString()}</span>
              <button className="income-edit-btn" onClick={() => setEditingIncome(true)}><FiEdit3 size={14} /></button>
            </div>
          )}
          {additional_income > 0 && (
            <span className="income-extra-tag">+ Rs. {additional_income.toLocaleString()} extra</span>
          )}
        </div>
        <div className="income-right">
          <div className="balance-block">
            <span className="balance-label">Total Income</span>
            <span className="balance-spent">Rs. {(total_income || monthly_income).toLocaleString()}</span>
          </div>
          <div className="balance-divider"></div>
          <div className="balance-block">
            <span className="balance-label">This Month Spent</span>
            <span className="balance-spent">Rs. {current_month_expense.toLocaleString()}</span>
          </div>
          <div className="balance-divider"></div>
          <div className="balance-block">
            <span className="balance-label">Remaining Balance</span>
            <span className={`balance-value ${isBalanceNegative ? 'negative' : 'positive'}`}>
              Rs. {remaining_balance.toLocaleString()}
            </span>
          </div>
          <div className="balance-divider"></div>
          <div className="balance-block">
            <span className="balance-label">Savings Rate</span>
            <span className={`balance-rate ${savings_rate >= 20 ? 'good' : savings_rate >= 0 ? 'warning' : 'bad'}`}>
              {savings_rate}%
            </span>
          </div>
        </div>
      </div>

      {/* Additional Income Section */}
      <div className="additional-income-section">
        <div className="additional-income-header">
          <h3 className="additional-income-title">
            <FiDollarSign size={18} />
            Additional Income This Month
          </h3>
          <button className="btn-add-income" onClick={() => setShowAddIncome(!showAddIncome)}>
            {showAddIncome ? <FiX size={16} /> : <FiPlus size={16} />}
            {showAddIncome ? 'Cancel' : 'Add Income'}
          </button>
        </div>

        {showAddIncome && (
          <div className="add-income-form">
            <div className="add-income-fields">
              <div className="add-income-field">
                <label>Date</label>
                <input type="date" value={newIncome.date}
                  onChange={(e) => setNewIncome({ ...newIncome, date: e.target.value })} />
              </div>
              <div className="add-income-field">
                <label>Amount (Rs.)</label>
                <input type="number" placeholder="e.g. 5000" value={newIncome.amount}
                  onChange={(e) => setNewIncome({ ...newIncome, amount: e.target.value })}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddAdditionalIncome()} />
              </div>
              <div className="add-income-field">
                <label>Source</label>
                <select value={newIncome.source}
                  onChange={(e) => setNewIncome({ ...newIncome, source: e.target.value })}>
                  {INCOME_SOURCES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="add-income-field">
                <label>Description (optional)</label>
                <input type="text" placeholder="e.g. Logo design project" value={newIncome.description}
                  onChange={(e) => setNewIncome({ ...newIncome, description: e.target.value })}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddAdditionalIncome()} />
              </div>
              <button className="btn btn-primary add-income-submit" onClick={handleAddAdditionalIncome}>
                <FiPlus size={16} /> Add
              </button>
            </div>
          </div>
        )}

        {additionalIncomes.length > 0 ? (
          <div className="additional-income-list">
            {additionalIncomes.map((inc) => (
              <div key={inc.id} className="additional-income-item">
                <div className="ai-item-icon"><FiDollarSign size={16} /></div>
                <div className="ai-item-info">
                  <span className="ai-item-source">{inc.source}</span>
                  <span className="ai-item-desc">{inc.description || inc.date}</span>
                </div>
                <span className="ai-item-date">{inc.date}</span>
                <span className="ai-item-amount">+ Rs. {parseFloat(inc.amount).toLocaleString()}</span>
                <button className="ai-item-delete" onClick={() => handleDeleteAdditionalIncome(inc.id)}>
                  <FiTrash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="additional-income-empty">
            No additional income this month. Click "Add Income" to log freelance work, bonuses, or any extra earnings.
          </p>
        )}
      </div>

      {/* CFP Section: Health Score + 50/30/20 Rule */}
      {(health_score > 0 || rule_50_30_20) && (
        <div className="cfp-section">
          {health_score > 0 && (
            <div className="health-score-card">
              <div className="hs-top-section">
                <div className="health-score-circle" style={{
                  background: `conic-gradient(${healthColor} ${health_score * 3.6}deg, #e9ecef ${health_score * 3.6}deg)`
                }}>
                  <div className="health-score-inner">
                    <span className="health-score-number" style={{ color: healthColor }}>{health_score}</span>
                    <span className="health-score-label">{health_score_grade || (health_score >= 70 ? 'Good' : health_score >= 40 ? 'Fair' : 'Needs Work')}</span>
                  </div>
                </div>
                <div className="hs-summary">
                  <h3 className="health-title">Financial Health</h3>
                  <span className="hs-grade-badge" style={{ background: `${healthColor}18`, color: healthColor }}>
                    {health_score}/100
                  </span>
                  <p className="hs-desc">
                    {health_score >= 80 ? 'Excellent! Your finances are well-managed. Keep maintaining these healthy habits.' :
                     health_score >= 60 ? 'Good progress! A few improvements can push your score higher.' :
                     health_score >= 40 ? 'Fair - there\'s room for improvement. Focus on the weak areas below.' :
                     'Needs attention. Follow the tips below to strengthen your financial position.'}
                  </p>
                </div>
              </div>

              {Object.keys(health_score_breakdown).length > 0 && (
                <div className="score-breakdown">
                  <h4 className="sbd-heading">Score Breakdown</h4>
                  {Object.entries(health_score_breakdown).map(([key, val]) => {
                    const info = HEALTH_COMPONENT_INFO[key] || { max: 20, label: key.replace(/_/g, ' '), desc: '' };
                    const pct = (val / info.max) * 100;
                    const barColor = pct >= 70 ? '#00b894' : pct >= 40 ? '#fdcb6e' : '#d63031';
                    return (
                      <div key={key} className="score-breakdown-row">
                        <div className="sbd-icon" style={{ color: barColor }}>{info.icon}</div>
                        <div className="sbd-content">
                          <div className="sbd-top">
                            <span className="sbd-label">{info.label}</span>
                            <span className="sbd-val">{val} <span className="sbd-max">/ {info.max}</span></span>
                          </div>
                          <div className="score-bar">
                            <div className="score-bar-fill" style={{ width: `${Math.min(pct, 100)}%`, background: barColor }} />
                          </div>
                          <p className="sbd-desc">{info.desc}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {weakestAreas.length > 0 && (
                <div className="hs-tips">
                  <h4 className="hs-tips-title"><FiAlertTriangle size={14} /> Areas to Improve</h4>
                  {weakestAreas.map(area => (
                    <div key={area.key} className="hs-tip-item">
                      <span className="hs-tip-badge" style={{ background: '#d6303118', color: '#d63031' }}>
                        {HEALTH_COMPONENT_INFO[area.key]?.label || area.key}
                      </span>
                      <p className="hs-tip-text">{getHealthTip(area.key)}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="cfp-right-col">
            {rule_50_30_20 && (
              <div className="rule-card">
                <h3 className="rule-title">50/30/20 Budget Rule</h3>
                <p className="rule-subtitle">How your spending compares to the ideal split</p>
                <div className="stacked-bar">
                  {rule_50_30_20.needs_pct > 0 && (
                    <div className="bar-segment bar-needs" style={{ width: `${Math.max(rule_50_30_20.needs_pct, 5)}%` }}>
                      {rule_50_30_20.needs_pct >= 10 && `${rule_50_30_20.needs_pct}%`}
                    </div>
                  )}
                  {rule_50_30_20.wants_pct > 0 && (
                    <div className="bar-segment bar-wants" style={{ width: `${Math.max(rule_50_30_20.wants_pct, 5)}%` }}>
                      {rule_50_30_20.wants_pct >= 10 && `${rule_50_30_20.wants_pct}%`}
                    </div>
                  )}
                  {rule_50_30_20.savings_pct > 0 && (
                    <div className="bar-segment bar-savings" style={{ width: `${Math.max(rule_50_30_20.savings_pct, 5)}%` }}>
                      {rule_50_30_20.savings_pct >= 10 && `${rule_50_30_20.savings_pct}%`}
                    </div>
                  )}
                </div>
                <div className="rule-legend">
                  <span className="rule-leg-item"><span className="leg-dot" style={{ background: '#0984e3' }}></span> Needs {rule_50_30_20.needs_pct}%</span>
                  <span className="rule-leg-item"><span className="leg-dot" style={{ background: '#fdcb6e' }}></span> Wants {rule_50_30_20.wants_pct}%</span>
                  <span className="rule-leg-item"><span className="leg-dot" style={{ background: '#00b894' }}></span> Savings {rule_50_30_20.savings_pct}%</span>
                </div>
                <div className="ideal-bar-label">Ideal: 50% Needs | 30% Wants | 20% Savings</div>
              </div>
            )}

            {/* CFP Insights — inside right column */}
            {agentInsights.length > 0 && (
              <div className="cfp-insights-inline">
                <div className="quick-insights-header">
                  <h3><TbPigMoney size={18} className="qi-header-icon" /> CFP Insights</h3>
                  <NavLink to="/agents" className="view-all-link">
                    View All <FiChevronRight size={14} />
                  </NavLink>
                </div>
                <div className="cfp-insights-inline-list">
                  {agentInsights.slice(0, 3).map((insight, idx) => {
                    const sevColors = { critical: '#d63031', warning: '#e17055', success: '#00b894', info: '#0984e3' };
                    const sevBgs = { critical: '#ffeef0', warning: '#fff4e6', success: '#e8f8f5', info: '#e8f0fe' };
                    const SevIcon = insight.severity === 'critical' ? FiAlertCircle
                      : insight.severity === 'warning' ? FiAlertTriangle
                      : insight.severity === 'success' ? FiCheckCircle
                      : FiInfo;
                    return (
                      <div key={idx} className="cfp-inline-card" style={{ borderLeftColor: insight.agent_color }}>
                        <div className="qi-top">
                          <span className="qi-agent" style={{ color: insight.agent_color }}>{insight.agent}</span>
                          <span className="qi-severity" style={{ background: sevBgs[insight.severity], color: sevColors[insight.severity] }}>
                            <SevIcon size={11} /> {insight.severity}
                          </span>
                        </div>
                        <span className="qi-title">{insight.title}</span>
                        <span className="qi-message">{insight.message}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stat Cards — Current Month */}
      <div className="stats-grid">
        <div className="stat-card stat-purple">
          <div className="stat-icon"><FiDollarSign /></div>
          <div className="stat-info">
            <span className="stat-label">This Month's Expenses</span>
            <span className="stat-value">Rs. {current_month_expense.toLocaleString()}</span>
          </div>
        </div>
        <div className="stat-card stat-green">
          <div className="stat-icon"><FiTrendingUp /></div>
          <div className="stat-info">
            <span className="stat-label">Monthly Average</span>
            <span className="stat-value">Rs. {avg_monthly_expense.toLocaleString()}</span>
          </div>
        </div>
        <div className="stat-card stat-orange">
          <div className="stat-icon"><FiActivity /></div>
          <div className="stat-info">
            <span className="stat-label">This Month's Transactions</span>
            <span className="stat-value">{current_month_transaction_count.toLocaleString()}</span>
          </div>
        </div>
        <div className="stat-card stat-blue">
          <div className="stat-icon"><FiPocket /></div>
          <div className="stat-info">
            <span className="stat-label">Remaining Balance</span>
            <span className="stat-value" style={{ color: isBalanceNegative ? '#d63031' : '#00b894' }}>
              Rs. {remaining_balance.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Savings & Coverage Cards */}
      <div className="coverage-grid">
        <div className="coverage-card savings-card">
          <div className="coverage-icon" style={{ background: '#00b89415', color: '#00b894' }}>
            <FiPocket size={20} />
          </div>
          <div className="coverage-info">
            <span className="coverage-label">Total Savings Till Date</span>
            <span className="coverage-value" style={{ color: total_savings >= 0 ? '#00b894' : '#d63031' }}>
              Rs. {total_savings.toLocaleString()}
            </span>
            <span className="coverage-sub">
              {monthly_details.length > 0 ? `Across ${monthly_details.length} months` : 'Start tracking to see savings'}
            </span>
          </div>
        </div>
        <div className={`coverage-card ${has_health_insurance ? 'covered' : 'not-covered'}`}>
          <div className="coverage-icon" style={{ background: has_health_insurance ? '#00b89415' : '#d6303115', color: has_health_insurance ? '#00b894' : '#d63031' }}>
            <FiHeart size={20} />
          </div>
          <div className="coverage-info">
            <span className="coverage-label">Health Insurance</span>
            <span className="coverage-status">
              {has_health_insurance
                ? <><FiCheckCircle size={14} style={{ color: '#00b894' }} /> Covered</>
                : <><FiAlertCircle size={14} style={{ color: '#d63031' }} /> Not Covered</>}
            </span>
            <span className="coverage-sub">
              {has_health_insurance ? 'You have active health coverage' : 'Recommended for medical emergencies'}
            </span>
          </div>
        </div>
        <div className={`coverage-card ${has_term_insurance ? 'covered' : 'not-covered'}`}>
          <div className="coverage-icon" style={{ background: has_term_insurance ? '#00b89415' : '#d6303115', color: has_term_insurance ? '#00b894' : '#d63031' }}>
            <FiShield size={20} />
          </div>
          <div className="coverage-info">
            <span className="coverage-label">Term Insurance</span>
            <span className="coverage-status">
              {has_term_insurance
                ? <><FiCheckCircle size={14} style={{ color: '#00b894' }} /> Covered</>
                : <><FiAlertCircle size={14} style={{ color: '#d63031' }} /> Not Covered</>}
            </span>
            <span className="coverage-sub">
              {has_term_insurance ? 'You have active term life coverage' : 'Essential for family protection'}
            </span>
          </div>
        </div>
      </div>

      {/* Profile Completion Card */}
      {profile && (!profile.age || profile.age === 25) && !profile.has_health_insurance && !profile.has_term_insurance && (
        <div className="profile-prompt-card">
          <div className="profile-prompt-header">
            <div className="profile-prompt-title">
              <FiUser size={18} />
              <div>
                <h3>Complete Your Profile</h3>
                <p>Add your age, dependents, and insurance info to get personalized CFP suggestions</p>
              </div>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setShowProfileForm(!showProfileForm)}>
              {showProfileForm ? 'Cancel' : 'Update Profile'}
            </button>
          </div>
          {showProfileForm && (
            <div className="profile-form">
              <div className="profile-form-fields">
                <div className="profile-field">
                  <label>Age</label>
                  <input type="number" min="18" max="100" placeholder="e.g. 30"
                    value={profileForm.age} onChange={(e) => setProfileForm({ ...profileForm, age: e.target.value })} />
                </div>
                <div className="profile-field">
                  <label>Dependents</label>
                  <input type="number" min="0" max="10" placeholder="e.g. 2"
                    value={profileForm.dependents} onChange={(e) => setProfileForm({ ...profileForm, dependents: e.target.value })} />
                </div>
                <div className="profile-field profile-check-field">
                  <label>
                    <input type="checkbox" checked={profileForm.has_health_insurance}
                      onChange={(e) => setProfileForm({ ...profileForm, has_health_insurance: e.target.checked })} />
                    <FiHeart size={14} /> I have Health Insurance
                  </label>
                </div>
                <div className="profile-field profile-check-field">
                  <label>
                    <input type="checkbox" checked={profileForm.has_term_insurance}
                      onChange={(e) => setProfileForm({ ...profileForm, has_term_insurance: e.target.checked })} />
                    <FiShield size={14} /> I have Term Insurance
                  </label>
                </div>
              </div>
              <button className="btn btn-primary" onClick={handleSaveProfile} disabled={savingProfile}>
                <FiCheck size={14} />
                {savingProfile ? 'Saving...' : 'Save Profile'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* CFP Insights moved into cfp-section right column above */}

      {/* Charts Row 1 */}
      <div className="charts-grid">
        <div className="chart-card chart-wide">
          <h3 className="chart-title">Monthly Expense Trend {dataRange && <span className="chart-date-range">({dataRange})</span>}</h3>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={monthlyChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
              <Tooltip formatter={(value) => [`Rs. ${value.toLocaleString()}`, 'Expense']} />
              <Line type="monotone" dataKey="amount" stroke="#6c5ce7" strokeWidth={3}
                dot={{ fill: '#6c5ce7', r: 4 }} activeDot={{ r: 6 }} name="Monthly Expense" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-card">
          <h3 className="chart-title">Category Breakdown {dataRange && <span className="chart-date-range">({dataRange})</span>}</h3>
          <ResponsiveContainer width="100%" height={340}>
            <PieChart>
              <Pie data={categoryChartData} cx="50%" cy="42%" innerRadius={55} outerRadius={90}
                paddingAngle={3} dataKey="value" label={renderPieLabel}>
                {categoryChartData.map((entry, index) => (<Cell key={index} fill={COLORS[index % COLORS.length]} />))}
              </Pie>
              <Tooltip formatter={(value, name, props) => [`Rs. ${value.toLocaleString()} (${props.payload.pct}%)`, name]} />
              <Legend layout="horizontal" verticalAlign="bottom" align="center"
                formatter={(value, entry) => <span style={{ fontSize: '11px' }}>{value} ({entry.payload.pct}%)</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="charts-grid">
        <div className="chart-card chart-wide">
          <h3 className="chart-title">Spending by Category {dataRange && <span className="chart-date-range">({dataRange})</span>}</h3>
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={categoryChartData} margin={{ top: 20, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0}
                tickFormatter={(value) => value.length > 10 ? value.slice(0, 10) + '..' : value} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
              <Tooltip formatter={(value, name, props) => [`Rs. ${value.toLocaleString()} (${props.payload.pct}%)`, 'Amount']} />
              <Bar dataKey="value" name="Amount" radius={[6, 6, 0, 0]}>
                {categoryChartData.map((entry, index) => (<Cell key={index} fill={COLORS[index % COLORS.length]} />))}
                <LabelList dataKey="value" position="top" fontSize={10} fontWeight={600}
                  formatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-card">
          <h3 className="chart-title">Payment Methods {dataRange && <span className="chart-date-range">({dataRange})</span>}</h3>
          <ResponsiveContainer width="100%" height={340}>
            <PieChart>
              <Pie data={paymentChartData} cx="50%" cy="42%" innerRadius={55} outerRadius={90} paddingAngle={3} dataKey="value" label={renderPieLabel}>
                {paymentChartData.map((entry, index) => (<Cell key={index} fill={COLORS[(index + 3) % COLORS.length]} />))}
              </Pie>
              <Tooltip formatter={(value, name, props) => [`Rs. ${value.toLocaleString()} (${props.payload.pct}%)`, name]} />
              <Legend layout="horizontal" verticalAlign="bottom" align="center"
                formatter={(value, entry) => <span style={{ fontSize: '11px' }}>{value} ({entry.payload.pct}%)</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly Comparison */}
      {monthly_details.length >= 2 && (
        <div className="month-comparison-section">
          <div className="mc-header-row">
            <h3 className="chart-title">Monthly Comparison</h3>
            <div className="mc-selectors">
              <select className="mc-select" value={compM1 ?? ''} onChange={(e) => setCompareMonth1(Number(e.target.value))}>
                {monthly_details.map((m, idx) => (
                  <option key={idx} value={idx}>{m.label}</option>
                ))}
              </select>
              <span className="mc-select-vs">vs</span>
              <select className="mc-select" value={compM2 ?? ''} onChange={(e) => setCompareMonth2(Number(e.target.value))}>
                {monthly_details.map((m, idx) => (
                  <option key={idx} value={idx}>{m.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 12-Month Overview Bar Chart */}
          <div className="mc-overview">
            <h4 className="mc-sub-title">Last {last12.length} Months Overview</h4>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={last12} margin={{ top: 15, right: 10, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={0} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
                <Tooltip formatter={(value) => `Rs. ${value.toLocaleString()}`} />
                <Bar dataKey="total" name="Spending" radius={[4, 4, 0, 0]}>
                  {last12.map((entry, index) => {
                    const isSelected = entry.key === selectedPrev?.key || entry.key === selectedCurr?.key;
                    return <Cell key={index} fill={isSelected ? '#6c5ce7' : '#b2bec3'} />;
                  })}
                  <LabelList dataKey="total" position="top" fontSize={9} fontWeight={600}
                    formatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Selected Month Comparison */}
          {comparisonData && (
            <>
              <div className="mc-summary-row">
                <div className="mc-summary-card">
                  <span className="mc-month-label">{comparisonData.prev.label}</span>
                  <span className="mc-month-amount">Rs. {comparisonData.prev.total.toLocaleString()}</span>
                  <span className="mc-month-txns">{comparisonData.prev.txn_count} transactions</span>
                </div>
                <div className="mc-vs">
                  <span className={`mc-change ${comparisonData.change_pct > 0 ? 'mc-up' : comparisonData.change_pct < 0 ? 'mc-down' : ''}`}>
                    {comparisonData.change_pct > 0 ? '+' : ''}{comparisonData.change_pct}%
                  </span>
                  <span className="mc-vs-label">change</span>
                </div>
                <div className="mc-summary-card">
                  <span className="mc-month-label">{comparisonData.curr.label}</span>
                  <span className="mc-month-amount">Rs. {comparisonData.curr.total.toLocaleString()}</span>
                  <span className="mc-month-txns">{comparisonData.curr.txn_count} transactions</span>
                </div>
              </div>

              {/* Category Changes */}
              <div className="mc-categories">
                <h4 className="mc-sub-title">Category-wise Changes</h4>
                <div className="mc-cat-grid">
                  {comparisonData.category_changes.map((cat, idx) => (
                    <div key={idx} className="mc-cat-item">
                      <span className="mc-cat-name">{cat.category}</span>
                      <div className="mc-cat-values">
                        <span className="mc-cat-prev">Rs. {cat.previous.toLocaleString()}</span>
                        <span className="mc-cat-arrow">→</span>
                        <span className="mc-cat-curr">Rs. {cat.current.toLocaleString()}</span>
                      </div>
                      <span className={`mc-cat-change ${cat.change_pct > 0 ? 'mc-up' : cat.change_pct < 0 ? 'mc-down' : ''}`}>
                        {cat.change_pct > 0 ? '+' : ''}{cat.change_pct}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Comparison Insights */}
              {comparisonData.insights.length > 0 && (
                <div className="mc-insights">
                  <h4 className="mc-sub-title">Insights</h4>
                  {comparisonData.insights.map((insight, idx) => (
                    <div key={idx} className="mc-insight-item">
                      <FiInfo size={14} />
                      <span>{insight}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
