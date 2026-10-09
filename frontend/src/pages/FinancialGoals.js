import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { toast } from 'react-toastify';
import {
  FiTarget, FiPlus, FiX, FiTrash2, FiCheckCircle,
  FiDollarSign, FiCalendar, FiAward, FiTrendingUp,
  FiShield, FiHeart, FiStar, FiGift
} from 'react-icons/fi';
import '../styles/FinancialGoals.css';

const GOAL_ICONS = [
  { id: 'target', label: 'Target', icon: FiTarget },
  { id: 'shield', label: 'Safety', icon: FiShield },
  { id: 'trending-up', label: 'Growth', icon: FiTrendingUp },
  { id: 'award', label: 'Achievement', icon: FiAward },
  { id: 'heart', label: 'Dream', icon: FiHeart },
  { id: 'star', label: 'Premium', icon: FiStar },
  { id: 'gift', label: 'Gift', icon: FiGift },
  { id: 'dollar-sign', label: 'Money', icon: FiDollarSign },
];

const GOAL_COLORS = ['#00b894', '#6c5ce7', '#0984e3', '#e17055', '#fdcb6e', '#d63031', '#e84393', '#00cec9'];

const ICON_MAP = {
  'target': FiTarget, 'shield': FiShield, 'trending-up': FiTrendingUp,
  'award': FiAward, 'heart': FiHeart, 'star': FiStar,
  'gift': FiGift, 'dollar-sign': FiDollarSign,
};

function FinancialGoals() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [addFundGoalId, setAddFundGoalId] = useState(null);
  const [fundAmount, setFundAmount] = useState('');
  const [formData, setFormData] = useState({
    name: '', target_amount: '', deadline: '', icon: 'target', color: '#00b894'
  });

  useEffect(() => {
    fetchGoals();
  }, []);

  const fetchGoals = async () => {
    try {
      const res = await api.get('/goals');
      setGoals(res.data);
    } catch (err) {
      toast.error('Could not load goals');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.target_amount || parseFloat(formData.target_amount) <= 0) {
      toast.error('Please enter a goal name and target amount');
      return;
    }
    try {
      await api.post('/goals', {
        name: formData.name,
        target_amount: parseFloat(formData.target_amount),
        deadline: formData.deadline || null,
        icon: formData.icon,
        color: formData.color,
      });
      toast.success('Goal created!');
      setShowForm(false);
      setFormData({ name: '', target_amount: '', deadline: '', icon: 'target', color: '#00b894' });
      fetchGoals();
    } catch (err) {
      toast.error('Failed to create goal');
    }
  };

  const handleAddFunds = async (goalId) => {
    if (!fundAmount || parseFloat(fundAmount) <= 0) {
      toast.error('Enter a valid amount');
      return;
    }
    try {
      const res = await api.put(`/goals/${goalId}/add-funds`, { amount: parseFloat(fundAmount) });
      if (res.data.status === 'completed') {
        toast.success('Goal completed! Congratulations!');
      } else {
        toast.success(res.data.message);
      }
      setAddFundGoalId(null);
      setFundAmount('');
      fetchGoals();
    } catch (err) {
      toast.error('Failed to add funds');
    }
  };

  const handleDelete = async (goalId) => {
    try {
      await api.delete(`/goals/${goalId}`);
      toast.success('Goal deleted');
      fetchGoals();
    } catch (err) {
      toast.error('Failed to delete goal');
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner"></div><p>Loading Goals...</p></div>
      </div>
    );
  }

  const activeGoals = goals.filter(g => g.status === 'active');
  const completedGoals = goals.filter(g => g.status === 'completed');

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="goals-header-row">
          <div>
            <h1><FiTarget className="header-icon" style={{ color: '#00b894' }} /> Financial Goals</h1>
            <p className="subtitle">Set savings targets and track your progress</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? <><FiX size={16} /> Cancel</> : <><FiPlus size={16} /> New Goal</>}
          </button>
        </div>
      </div>

      {/* Create Goal Form */}
      {showForm && (
        <div className="goal-form-card">
          <h3>Create New Goal</h3>
          <div className="goal-form-fields">
            <div className="goal-form-field">
              <label>Goal Name</label>
              <input type="text" placeholder="e.g. Emergency Fund, Vacation, New Laptop"
                value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()} />
            </div>
            <div className="goal-form-field">
              <label>Target Amount (Rs.)</label>
              <input type="number" placeholder="e.g. 50000" min="1"
                value={formData.target_amount} onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()} />
            </div>
            <div className="goal-form-field">
              <label>Deadline (Optional)</label>
              <input type="date" value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })} />
            </div>
          </div>
          <div className="goal-form-row">
            <div className="goal-form-field">
              <label>Icon</label>
              <div className="icon-picker">
                {GOAL_ICONS.map(gi => {
                  const GI = gi.icon;
                  return (
                    <button key={gi.id}
                      className={`icon-option ${formData.icon === gi.id ? 'selected' : ''}`}
                      onClick={() => setFormData({ ...formData, icon: gi.id })}
                      title={gi.label}
                      style={formData.icon === gi.id ? { borderColor: formData.color, color: formData.color } : {}}>
                      <GI size={18} />
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="goal-form-field">
              <label>Color</label>
              <div className="color-picker">
                {GOAL_COLORS.map(c => (
                  <button key={c}
                    className={`color-option ${formData.color === c ? 'selected' : ''}`}
                    style={{ background: c }}
                    onClick={() => setFormData({ ...formData, color: c })} />
                ))}
              </div>
            </div>
          </div>
          <button className="btn btn-primary" onClick={handleCreate}>
            <FiPlus size={16} /> Create Goal
          </button>
        </div>
      )}

      {/* Active Goals */}
      {activeGoals.length === 0 && completedGoals.length === 0 && !showForm && (
        <div className="goals-empty">
          <FiTarget size={48} color="#b2bec3" />
          <h3>No Goals Yet</h3>
          <p>Create your first savings goal to start tracking progress!</p>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            <FiPlus size={16} /> Create Goal
          </button>
        </div>
      )}

      {activeGoals.length > 0 && (
        <>
          <h2 className="goals-section-title">Active Goals ({activeGoals.length})</h2>
          <div className="goals-grid">
            {activeGoals.map(goal => {
              const IconComp = ICON_MAP[goal.icon] || FiTarget;
              const pct = goal.target_amount > 0 ? Math.min(100, round((goal.current_amount / goal.target_amount) * 100, 1)) : 0;
              const remaining = Math.max(0, goal.target_amount - goal.current_amount);
              const deadlineDays = goal.deadline ? Math.ceil((new Date(goal.deadline) - new Date()) / (1000 * 60 * 60 * 24)) : null;

              return (
                <div key={goal.id} className="goal-card" style={{ borderLeftColor: goal.color }}>
                  <div className="goal-card-header">
                    <div className="goal-icon" style={{ background: goal.color + '20', color: goal.color }}>
                      <IconComp size={22} />
                    </div>
                    <button className="goal-delete-btn" onClick={() => handleDelete(goal.id)} title="Delete goal">
                      <FiTrash2 size={14} />
                    </button>
                  </div>
                  <h3 className="goal-name">{goal.name}</h3>
                  <div className="goal-progress-bar">
                    <div className="goal-progress-fill" style={{ width: `${pct}%`, background: goal.color }} />
                  </div>
                  <div className="goal-amounts">
                    <span className="goal-current" style={{ color: goal.color }}>Rs. {goal.current_amount.toLocaleString()}</span>
                    <span className="goal-target">/ Rs. {goal.target_amount.toLocaleString()}</span>
                  </div>
                  <div className="goal-meta">
                    <span className="goal-pct">{pct}%</span>
                    {deadlineDays !== null && (
                      <span className={`goal-deadline ${deadlineDays < 0 ? 'overdue' : deadlineDays < 30 ? 'soon' : ''}`}>
                        <FiCalendar size={12} />
                        {deadlineDays < 0 ? `${Math.abs(deadlineDays)}d overdue` : `${deadlineDays}d left`}
                      </span>
                    )}
                  </div>

                  {/* Add Funds */}
                  {addFundGoalId === goal.id ? (
                    <div className="add-fund-row">
                      <input type="number" placeholder="Amount" min="1" value={fundAmount}
                        onChange={(e) => setFundAmount(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddFunds(goal.id)}
                        autoFocus />
                      <button className="btn btn-primary btn-sm" onClick={() => handleAddFunds(goal.id)}>Add</button>
                      <button className="btn-cancel-sm" onClick={() => { setAddFundGoalId(null); setFundAmount(''); }}>
                        <FiX size={14} />
                      </button>
                    </div>
                  ) : (
                    <button className="add-fund-btn" style={{ color: goal.color, borderColor: goal.color + '40' }}
                      onClick={() => setAddFundGoalId(goal.id)}>
                      <FiPlus size={14} /> Add Funds
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Completed Goals */}
      {completedGoals.length > 0 && (
        <>
          <h2 className="goals-section-title completed-title">
            <FiCheckCircle size={20} color="#00b894" /> Completed ({completedGoals.length})
          </h2>
          <div className="goals-grid">
            {completedGoals.map(goal => {
              const IconComp = ICON_MAP[goal.icon] || FiTarget;
              return (
                <div key={goal.id} className="goal-card completed" style={{ borderLeftColor: '#00b894' }}>
                  <div className="goal-card-header">
                    <div className="goal-icon" style={{ background: '#00b89420', color: '#00b894' }}>
                      <IconComp size={22} />
                    </div>
                    <FiCheckCircle size={20} color="#00b894" />
                  </div>
                  <h3 className="goal-name">{goal.name}</h3>
                  <div className="goal-progress-bar">
                    <div className="goal-progress-fill" style={{ width: '100%', background: '#00b894' }} />
                  </div>
                  <span className="goal-completed-text">Rs. {goal.target_amount.toLocaleString()} achieved!</span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

function round(num, decimals) {
  return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals);
}

export default FinancialGoals;
