import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import {
  FiBarChart2, FiShield, FiTarget, FiTrendingUp,
  FiAlertTriangle, FiCalendar, FiRefreshCw,
  FiAlertCircle, FiCheckCircle, FiInfo
} from 'react-icons/fi';
import { TbPigMoney } from 'react-icons/tb';
import '../styles/AgentsHub.css';

const AGENT_ICONS = {
  'bar-chart-2': FiBarChart2,
  'shield': FiShield,
  'target': FiTarget,
  'trending-up': FiTrendingUp,
  'alert-triangle': FiAlertTriangle,
  'calendar': FiCalendar,
};

const SEVERITY_CONFIG = {
  critical: { color: '#d63031', bg: '#ffeef0', label: 'Critical', icon: FiAlertCircle },
  warning: { color: '#e17055', bg: '#fff4e6', label: 'Warning', icon: FiAlertTriangle },
  success: { color: '#00b894', bg: '#e8f8f5', label: 'Good', icon: FiCheckCircle },
  info: { color: '#0984e3', bg: '#e8f0fe', label: 'Info', icon: FiInfo },
};

const STATUS_COLORS = {
  done: '#00b894',
  thinking: '#fdcb6e',
  idle: '#b2bec3',
  error: '#d63031',
};

function AgentsHub() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      const response = await api.get('/agents/insights');
      setData(response.data);
      setError(null);
    } catch (err) {
      if (err.response && err.response.status === 404) {
        setError('No transactions found. Add some expenses first to activate the AI agents.');
      } else {
        setError('Could not connect to the AI agents. Make sure the backend is running.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Activating AI Agents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-card">
          <FiAlertCircle size={40} color="#d63031" />
          <h3>Agents Unavailable</h3>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={() => fetchInsights()}>Retry</button>
        </div>
      </div>
    );
  }

  const { insights = [], agent_statuses = [], total_insights, critical_count, warning_count, success_count, generated_at } = data;

  const filteredInsights = activeFilter === 'all'
    ? insights
    : insights.filter(i => i.severity === activeFilter);

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="agents-header-row">
          <div>
            <h1><TbPigMoney className="header-icon" /> CFP Agents Hub</h1>
            <p className="subtitle">6 specialized agents analyzing your finances in real-time</p>
          </div>
          <button
            className={`btn btn-primary refresh-btn ${refreshing ? 'spinning' : ''}`}
            onClick={() => fetchInsights(true)}
            disabled={refreshing}
          >
            <FiRefreshCw size={16} />
            {refreshing ? 'Running...' : 'Re-run Agents'}
          </button>
        </div>
      </div>

      {/* Agent Cards */}
      <div className="agents-grid">
        {agent_statuses.map((agent, idx) => {
          const IconComp = AGENT_ICONS[agent.avatar] || TbPigMoney;
          const agentInsights = insights.filter(i => i.agent === agent.name);
          const topInsight = agentInsights[0];
          return (
            <div key={idx} className="agent-card" style={{ borderTopColor: agent.color }}>
              <div className="agent-card-header">
                <div className="agent-avatar" style={{ background: agent.color + '20', color: agent.color }}>
                  <IconComp size={22} />
                </div>
                <div className="agent-status-dot" style={{ background: STATUS_COLORS[agent.status] || '#b2bec3' }} title={agent.status} />
              </div>
              <h3 className="agent-name">{agent.name}</h3>
              <p className="agent-role">{agent.role}</p>
              {topInsight && (
                <div className="agent-top-recommendation" style={{ borderLeftColor: SEVERITY_CONFIG[topInsight.severity]?.color || '#0984e3' }}>
                  <span className="agent-rec-title">{topInsight.title}</span>
                  <span className="agent-rec-msg">{topInsight.message}</span>
                </div>
              )}
              <div className="agent-card-footer">
                <span className="agent-insight-count">{agentInsights.length} insight{agentInsights.length !== 1 ? 's' : ''}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Stats Bar */}
      <div className="insights-stats-bar">
        <div className="stats-left">
          <span className="stat-badge total">{total_insights} Total</span>
          {critical_count > 0 && <span className="stat-badge critical">{critical_count} Critical</span>}
          {warning_count > 0 && <span className="stat-badge warning">{warning_count} Warnings</span>}
          {success_count > 0 && <span className="stat-badge success">{success_count} Good</span>}
        </div>
        <span className="stats-time">
          Last run: {new Date(generated_at).toLocaleTimeString()}
        </span>
      </div>

      {/* Filter Tabs */}
      <div className="insight-filters">
        {['all', 'critical', 'warning', 'success', 'info'].map(filter => (
          <button
            key={filter}
            className={`filter-tab ${activeFilter === filter ? 'active' : ''}`}
            onClick={() => setActiveFilter(filter)}
          >
            {filter === 'all' ? 'All' : SEVERITY_CONFIG[filter]?.label || filter}
            {filter !== 'all' && (
              <span className="filter-count">
                {insights.filter(i => i.severity === filter).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Insights Feed */}
      <div className="insights-feed">
        {filteredInsights.length === 0 ? (
          <div className="empty-insights">
            <FiCheckCircle size={40} color="#00b894" />
            <p>No {activeFilter !== 'all' ? activeFilter : ''} insights to show.</p>
          </div>
        ) : (
          filteredInsights.map((insight, idx) => {
            const sev = SEVERITY_CONFIG[insight.severity] || SEVERITY_CONFIG.info;
            const SevIcon = sev.icon;
            const AgentIcon = AGENT_ICONS[insight.agent_avatar] || TbPigMoney;
            return (
              <div key={idx} className="insight-card" style={{ borderLeftColor: insight.agent_color }}>
                <div className="insight-header">
                  <div className="insight-agent-tag" style={{ color: insight.agent_color }}>
                    <AgentIcon size={14} />
                    <span>{insight.agent}</span>
                  </div>
                  <span className="insight-severity-badge" style={{ background: sev.bg, color: sev.color }}>
                    <SevIcon size={12} />
                    {sev.label}
                  </span>
                </div>
                <h4 className="insight-title">{insight.title}</h4>
                <p className="insight-message">{insight.message}</p>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default AgentsHub;
