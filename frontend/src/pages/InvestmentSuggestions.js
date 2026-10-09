import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  FiShield, FiTrendingUp, FiLock, FiDollarSign,
  FiAward, FiAlertCircle, FiCheckCircle, FiInfo,
  FiHeart, FiChevronDown, FiChevronUp
} from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';
import '../styles/InvestmentSuggestions.css';

const ALLOC_COLORS = ['#6c5ce7', '#00b894', '#0984e3', '#fdcb6e', '#e17055'];

const ICON_MAP = {
  'shield': FiShield,
  'trending-up': FiTrendingUp,
  'lock': FiLock,
  'bank': FiDollarSign,
  'award': FiAward,
  'piggy-bank': FiDollarSign,
};

const PRIORITY_CONFIG = {
  high: { color: '#d63031', bg: '#ffeef0', label: 'High Priority' },
  medium: { color: '#e17055', bg: '#fff4e6', label: 'Medium' },
  low: { color: '#00b894', bg: '#e8f8f5', label: 'Optional' },
};

const INSURANCE_PRIORITY_CONFIG = {
  critical: { color: '#d63031', bg: '#ffeef0', label: 'Must Have' },
  recommended: { color: '#0984e3', bg: '#e8f0fe', label: 'Recommended' },
  medium: { color: '#e17055', bg: '#fff4e6', label: 'Good to Have' },
  done: { color: '#00b894', bg: '#e8f8f5', label: 'Covered' },
};

function InvestmentSuggestions() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [insuranceData, setInsuranceData] = useState(null);
  const [expandedPlan, setExpandedPlan] = useState(null);

  useEffect(() => {
    fetchSuggestions();
    fetchInsurance();
  }, []);

  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/investment-suggestions');
      setData(response.data);
      setError(null);
    } catch (err) {
      if (err.response && err.response.status === 404) {
        setError('No transactions found. Add some expenses first to get personalized investment suggestions.');
      } else {
        setError('Could not load suggestions. Make sure the backend is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchInsurance = async () => {
    try {
      const response = await api.get('/insurance-suggestions');
      setInsuranceData(response.data);
    } catch (err) { /* silently fail */ }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Analyzing your finances...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-card">
          <FiAlertCircle size={40} color="#d63031" />
          <h3>No Data Available</h3>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={fetchSuggestions}>Retry</button>
        </div>
      </div>
    );
  }

  const {
    monthly_income, additional_income = 0, total_income,
    avg_monthly_expense, monthly_savings,
    savings_rate, remaining_balance, top_spending_category,
    top_spending_percentage, trend_direction, suggestions,
    spending_tips, recommended_allocation
  } = data;

  const allocationData = Object.entries(recommended_allocation).map(([name, value]) => ({
    name, value
  }));

  const isSavingsNegative = monthly_savings < 0;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Smart Investment Suggestions</h1>
        <p className="subtitle">AI-powered recommendations based on your spending patterns</p>
      </div>

      {/* Financial Summary Cards */}
      <div className="invest-summary-grid">
        <div className="invest-summary-card">
          <span className="invest-summary-label">Total Income</span>
          <span className="invest-summary-value purple">Rs. {(total_income || monthly_income).toLocaleString()}</span>
          {additional_income > 0 && (
            <span className="invest-summary-sub">Salary: Rs. {monthly_income.toLocaleString()} + Extra: Rs. {additional_income.toLocaleString()}</span>
          )}
        </div>
        <div className="invest-summary-card">
          <span className="invest-summary-label">Avg Monthly Expense</span>
          <span className="invest-summary-value orange">Rs. {avg_monthly_expense.toLocaleString()}</span>
        </div>
        <div className="invest-summary-card">
          <span className="invest-summary-label">Monthly Savings</span>
          <span className={`invest-summary-value ${isSavingsNegative ? 'red' : 'green'}`}>
            Rs. {monthly_savings.toLocaleString()}
          </span>
        </div>
        <div className="invest-summary-card">
          <span className="invest-summary-label">Savings Rate</span>
          <span className={`invest-summary-value ${savings_rate >= 20 ? 'green' : savings_rate >= 0 ? 'orange' : 'red'}`}>
            {savings_rate}%
          </span>
        </div>
      </div>

      {/* Spending Insight Banner */}
      <div className="invest-insight-banner">
        <FiInfo size={20} />
        <div className="invest-insight-text">
          <strong>Spending Insight:</strong> Your top spending category is <strong>{top_spending_category}</strong> at{' '}
          <strong>{top_spending_percentage}%</strong> of total spending. Your spending trend is{' '}
          <strong>{trend_direction}</strong>.
        </div>
      </div>

      {/* Main Content: Suggestions + Allocation */}
      <div className="invest-main-grid">
        {/* Suggestions Column */}
        <div className="invest-suggestions-col">
          <h2 className="invest-section-title">Personalized Recommendations</h2>
          <div className="invest-suggestions-list">
            {suggestions.map((s, index) => {
              const IconComponent = ICON_MAP[s.icon] || FiDollarSign;
              const priority = PRIORITY_CONFIG[s.priority] || PRIORITY_CONFIG.medium;
              return (
                <div key={index} className="invest-suggestion-card">
                  <div className="invest-suggestion-header">
                    <div className="invest-suggestion-icon" style={{ background: priority.bg, color: priority.color }}>
                      <IconComponent size={22} />
                    </div>
                    <div className="invest-suggestion-title-group">
                      <h3 className="invest-suggestion-title">{s.title}</h3>
                      <span className="invest-priority-badge" style={{ background: priority.bg, color: priority.color }}>
                        {priority.label}
                      </span>
                    </div>
                    {s.amount > 0 && (
                      <span className="invest-suggestion-amount">Rs. {s.amount.toLocaleString()}/mo</span>
                    )}
                  </div>
                  <p className="invest-suggestion-desc">{s.description}</p>
                  <div className="invest-suggestion-action">
                    <FiCheckCircle size={14} />
                    <span>{s.action}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Allocation & Tips Column */}
        <div className="invest-sidebar-col">
          {/* Recommended Allocation Pie */}
          <div className="invest-alloc-card">
            <h2 className="invest-section-title">Recommended Allocation</h2>
            <p className="invest-alloc-subtitle">
              How to distribute Rs. {Math.max(monthly_savings, 0).toLocaleString()}/month
            </p>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={allocationData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={95}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                >
                  {allocationData.map((entry, index) => (
                    <Cell key={index} fill={ALLOC_COLORS[index % ALLOC_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `Rs. ${value.toLocaleString()}`} />
                <Legend
                  formatter={(value) => <span style={{ fontSize: '12px', color: '#636e72' }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Spending Tips */}
          <div className="invest-tips-card">
            <h2 className="invest-section-title">Spending Tips</h2>
            <ul className="invest-tips-list">
              {spending_tips.map((tip, index) => (
                <li key={index} className="invest-tip-item">
                  <FiAlertCircle size={16} className="invest-tip-icon" />
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Quick Facts */}
          <div className="invest-facts-card">
            <h2 className="invest-section-title">Quick Facts</h2>
            <div className="invest-fact-row">
              <span className="invest-fact-label">Remaining this month</span>
              <span className={`invest-fact-value ${remaining_balance >= 0 ? 'green' : 'red'}`}>
                Rs. {remaining_balance.toLocaleString()}
              </span>
            </div>
            <div className="invest-fact-row">
              <span className="invest-fact-label">Top spending category</span>
              <span className="invest-fact-value">{top_spending_category}</span>
            </div>
            <div className="invest-fact-row">
              <span className="invest-fact-label">Spending trend</span>
              <span className={`invest-fact-value ${trend_direction === 'decreasing' ? 'green' : trend_direction === 'increasing' ? 'red' : ''}`}>
                {trend_direction.charAt(0).toUpperCase() + trend_direction.slice(1)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Insurance Suggestions Section */}
      {insuranceData && (
        <div className="insurance-section">
          <div className="insurance-section-header">
            <div>
              <h2 className="invest-section-title"><FiShield size={18} style={{ verticalAlign: '-3px', color: '#d63031' }} /> Insurance Protection</h2>
              <p className="insurance-section-sub">
                {insuranceData.total_monthly_premium > 0
                  ? `Estimated total: Rs. ${insuranceData.total_monthly_premium.toLocaleString()}/mo (${insuranceData.insurance_as_income_pct}% of income)`
                  : 'Your insurance coverage status'}
              </p>
            </div>
          </div>

          {/* Term Insurance */}
          <div className="insurance-category">
            <h3 className="insurance-cat-title"><FiShield size={15} /> Term Life Insurance</h3>
            <div className="insurance-plans-list">
              {insuranceData.term_insurance.map((plan, idx) => {
                const pri = INSURANCE_PRIORITY_CONFIG[plan.priority] || INSURANCE_PRIORITY_CONFIG.medium;
                const isExpanded = expandedPlan === `term-${idx}`;
                return (
                  <div key={idx} className={`insurance-plan-card ${plan.priority === 'done' ? 'plan-done' : ''}`}>
                    <div className="insurance-plan-header" onClick={() => setExpandedPlan(isExpanded ? null : `term-${idx}`)}>
                      <div className="insurance-plan-left">
                        <span className="insurance-plan-badge" style={{ background: pri.bg, color: pri.color }}>{pri.label}</span>
                        <h4 className="insurance-plan-name">{plan.name}</h4>
                      </div>
                      <div className="insurance-plan-right">
                        {plan.est_monthly_premium && (
                          <span className="insurance-plan-premium">Rs. {plan.est_monthly_premium.toLocaleString()}/mo</span>
                        )}
                        {isExpanded ? <FiChevronUp size={16} /> : <FiChevronDown size={16} />}
                      </div>
                    </div>
                    <p className="insurance-plan-why">{plan.why}</p>
                    {isExpanded && (
                      <div className="insurance-plan-details">
                        {plan.coverage_range && (
                          <div className="insurance-detail-row">
                            <span className="insurance-detail-label">Coverage Range</span>
                            <span className="insurance-detail-value">{plan.coverage_range}</span>
                          </div>
                        )}
                        {plan.est_annual_premium && (
                          <div className="insurance-detail-row">
                            <span className="insurance-detail-label">Annual Premium (est.)</span>
                            <span className="insurance-detail-value">Rs. {plan.est_annual_premium.toLocaleString()}</span>
                          </div>
                        )}
                        <ul className="insurance-features">
                          {plan.features.map((f, i) => (
                            <li key={i}><FiCheckCircle size={13} /> {f}</li>
                          ))}
                        </ul>
                        {plan.top_providers && plan.top_providers.length > 0 && (
                          <div className="insurance-providers">
                            <strong>Top Providers:</strong> {plan.top_providers.join(', ')}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Health Insurance */}
          <div className="insurance-category">
            <h3 className="insurance-cat-title"><FiHeart size={15} /> Health Insurance</h3>
            <div className="insurance-plans-list">
              {insuranceData.health_insurance.map((plan, idx) => {
                const pri = INSURANCE_PRIORITY_CONFIG[plan.priority] || INSURANCE_PRIORITY_CONFIG.medium;
                const isExpanded = expandedPlan === `health-${idx}`;
                return (
                  <div key={idx} className={`insurance-plan-card ${plan.priority === 'done' ? 'plan-done' : ''}`}>
                    <div className="insurance-plan-header" onClick={() => setExpandedPlan(isExpanded ? null : `health-${idx}`)}>
                      <div className="insurance-plan-left">
                        <span className="insurance-plan-badge" style={{ background: pri.bg, color: pri.color }}>{pri.label}</span>
                        <h4 className="insurance-plan-name">{plan.name}</h4>
                      </div>
                      <div className="insurance-plan-right">
                        {plan.est_monthly_premium && (
                          <span className="insurance-plan-premium">Rs. {plan.est_monthly_premium.toLocaleString()}/mo</span>
                        )}
                        {isExpanded ? <FiChevronUp size={16} /> : <FiChevronDown size={16} />}
                      </div>
                    </div>
                    <p className="insurance-plan-why">{plan.why}</p>
                    {isExpanded && (
                      <div className="insurance-plan-details">
                        {plan.coverage_range && (
                          <div className="insurance-detail-row">
                            <span className="insurance-detail-label">Coverage Range</span>
                            <span className="insurance-detail-value">{plan.coverage_range}</span>
                          </div>
                        )}
                        {plan.est_annual_premium && (
                          <div className="insurance-detail-row">
                            <span className="insurance-detail-label">Annual Premium (est.)</span>
                            <span className="insurance-detail-value">Rs. {plan.est_annual_premium.toLocaleString()}</span>
                          </div>
                        )}
                        <ul className="insurance-features">
                          {plan.features.map((f, i) => (
                            <li key={i}><FiCheckCircle size={13} /> {f}</li>
                          ))}
                        </ul>
                        {plan.top_providers && plan.top_providers.length > 0 && (
                          <div className="insurance-providers">
                            <strong>Top Providers:</strong> {plan.top_providers.join(', ')}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {insuranceData.recommendation && (
            <div className="insurance-recommendation-banner">
              <FiInfo size={18} />
              <span>{insuranceData.recommendation}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default InvestmentSuggestions;
