import React, { useState } from 'react';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FiPlusCircle, FiCalendar, FiDollarSign, FiTag, FiCreditCard, FiFileText, FiZap } from 'react-icons/fi';
import '../styles/AddTransaction.css';

const CATEGORIES = [
  'Food', 'Transport', 'Shopping', 'Bills',
  'Entertainment', 'Healthcare', 'Education', 'Other'
];

const PAYMENT_MODES = [
  'Cash', 'UPI', 'Credit Card', 'Debit Card', 'Net Banking'
];

function AddTransaction() {
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    amount: '',
    category: 'Food',
    payment_mode: 'UPI',
    description: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [smartText, setSmartText] = useState('');
  const [parsing, setParsing] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSmartParse = async () => {
    if (!smartText.trim()) return;
    try {
      setParsing(true);
      const res = await api.post('/smart-parse', { text: smartText });
      const parsed = res.data;
      if (parsed.parsed && parsed.amount) {
        setFormData({
          date: parsed.date || formData.date,
          amount: String(parsed.amount),
          category: parsed.category || 'Other',
          payment_mode: parsed.payment_mode || 'UPI',
          description: parsed.description || smartText,
        });
        toast.success('Parsed! Review the details below and submit.');
        setSmartText('');
      } else {
        toast.warning('Could not parse amount. Try: "Spent 450 on groceries via UPI"');
      }
    } catch (err) {
      toast.error('Smart parse failed. Enter manually.');
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    try {
      setSubmitting(true);
      await api.post('/transactions', formData);
      toast.success('Transaction added successfully!');

      // Add to recent list
      setRecentTransactions(prev => [{
        ...formData,
        id: Date.now()
      }, ...prev].slice(0, 5));

      // Reset form
      setFormData({
        date: new Date().toISOString().split('T')[0],
        amount: '',
        category: 'Food',
        payment_mode: 'UPI',
        description: ''
      });
    } catch (err) {
      toast.error('Failed to add transaction. Is the backend running?');
    } finally {
      setSubmitting(false);
    }
  };

  const getCategoryEmoji = (cat) => {
    const emojis = {
      'Food': '🍔', 'Transport': '🚗', 'Shopping': '🛍️', 'Bills': '📄',
      'Entertainment': '🎬', 'Healthcare': '🏥', 'Education': '📚', 'Other': '📦'
    };
    return emojis[cat] || '📦';
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Add Transaction</h1>
        <p className="subtitle">Record your expenses and income</p>
      </div>

      {/* Smart Parse */}
      <div className="smart-parse-section">
        <div className="smart-parse-label">
          <FiZap size={16} className="smart-icon" />
          <span>Quick Add</span>
        </div>
        <div className="smart-parse-row">
          <input
            type="text"
            className="smart-parse-input"
            placeholder='Try: "Spent 450 on groceries yesterday via UPI"'
            value={smartText}
            onChange={(e) => setSmartText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSmartParse()}
          />
          <button className="btn btn-primary smart-parse-btn" onClick={handleSmartParse} disabled={parsing || !smartText.trim()}>
            <FiZap size={14} />
            {parsing ? 'Parsing...' : 'Parse'}
          </button>
        </div>
        <p className="smart-parse-hint">
          Describe your expense in natural language and we'll fill the form for you.
        </p>
      </div>

      <div className="add-transaction-layout">
        {/* Form Card */}
        <div className="form-card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>
                <FiCalendar className="field-icon" />
                Date
              </label>
              <input
                type="date"
                name="date"
                value={formData.date}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>
                <FiDollarSign className="field-icon" />
                Amount (Rs.)
              </label>
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleChange}
                placeholder="Enter amount"
                min="1"
                step="0.01"
                required
              />
            </div>

            <div className="form-group">
              <label>
                <FiTag className="field-icon" />
                Category
              </label>
              <div className="category-grid">
                {CATEGORIES.map(cat => (
                  <button
                    key={cat}
                    type="button"
                    className={`category-chip ${formData.category === cat ? 'active' : ''}`}
                    onClick={() => setFormData({ ...formData, category: cat })}
                  >
                    <span className="chip-emoji">{getCategoryEmoji(cat)}</span>
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>
                <FiCreditCard className="field-icon" />
                Payment Mode
              </label>
              <select
                name="payment_mode"
                value={formData.payment_mode}
                onChange={handleChange}
              >
                {PAYMENT_MODES.map(mode => (
                  <option key={mode} value={mode}>{mode}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>
                <FiFileText className="field-icon" />
                Description (Optional)
              </label>
              <input
                type="text"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="What was this expense for?"
              />
            </div>

            <button type="submit" className="btn btn-primary btn-submit" disabled={submitting}>
              <FiPlusCircle />
              {submitting ? 'Adding...' : 'Add Transaction'}
            </button>
          </form>
        </div>

        {/* Recent Transactions */}
        <div className="recent-card">
          <h3>Recently Added</h3>
          {recentTransactions.length === 0 ? (
            <div className="empty-state">
              <p>No transactions added yet in this session.</p>
              <small>Your recently added transactions will appear here.</small>
            </div>
          ) : (
            <div className="recent-list">
              {recentTransactions.map((t) => (
                <div key={t.id} className="recent-item">
                  <span className="recent-emoji">{getCategoryEmoji(t.category)}</span>
                  <div className="recent-info">
                    <span className="recent-category">{t.category}</span>
                    <span className="recent-date">{t.date} | {t.payment_mode}</span>
                  </div>
                  <span className="recent-amount">Rs. {parseFloat(t.amount).toLocaleString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AddTransaction;
