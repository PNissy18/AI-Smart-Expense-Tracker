import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { FiSearch, FiFilter, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import '../styles/TransactionHistory.css';

const CATEGORY_COLORS = {
  'Food': '#e17055', 'Transport': '#0984e3', 'Shopping': '#6c5ce7',
  'Bills': '#fdcb6e', 'Entertainment': '#e84393', 'Healthcare': '#00b894',
  'Education': '#00cec9', 'Other': '#636e72'
};

function TransactionHistory() {
  const [transactions, setTransactions] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [sortField, setSortField] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  useEffect(() => {
    fetchTransactions();
  }, []);

  useEffect(() => {
    filterAndSort();
  }, [transactions, searchTerm, categoryFilter, sortField, sortOrder]);

  const fetchTransactions = async () => {
    try {
      const response = await api.get('/transactions');
      setTransactions(response.data);
    } catch (err) {
      console.error('Error fetching transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSort = () => {
    let result = [...transactions];

    // Search filter
    if (searchTerm) {
      result = result.filter(t =>
        t.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.payment_mode.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Category filter
    if (categoryFilter !== 'All') {
      result = result.filter(t => t.category === categoryFilter);
    }

    // Sort
    result.sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];
      if (sortField === 'amount') { valA = parseFloat(valA); valB = parseFloat(valB); }
      if (sortField === 'date') { valA = new Date(valA); valB = new Date(valB); }
      if (sortOrder === 'asc') return valA > valB ? 1 : -1;
      return valA < valB ? 1 : -1;
    });

    setFiltered(result);
    setCurrentPage(1);
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  // Pagination
  const totalPages = Math.ceil(filtered.length / itemsPerPage);
  const startIdx = (currentPage - 1) * itemsPerPage;
  const paginatedData = filtered.slice(startIdx, startIdx + itemsPerPage);

  const categories = ['All', ...new Set(transactions.map(t => t.category))];

  // Stats
  const totalAmount = filtered.reduce((sum, t) => sum + parseFloat(t.amount), 0);
  const avgAmount = filtered.length > 0 ? totalAmount / filtered.length : 0;

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner"><div className="spinner"></div><p>Loading Transactions...</p></div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Transaction History</h1>
        <p className="subtitle">{transactions.length} total transactions recorded</p>
      </div>

      {/* Quick Stats */}
      <div className="history-stats">
        <div className="hs-item">
          <span className="hs-label">Showing</span>
          <span className="hs-value">{filtered.length} transactions</span>
        </div>
        <div className="hs-item">
          <span className="hs-label">Total</span>
          <span className="hs-value">Rs. {totalAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
        </div>
        <div className="hs-item">
          <span className="hs-label">Average</span>
          <span className="hs-value">Rs. {avgAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            type="text"
            placeholder="Search transactions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <FiFilter className="filter-icon" />
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        <table className="history-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('date')} className="sortable">
                Date {sortField === 'date' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('amount')} className="sortable">
                Amount {sortField === 'amount' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('category')} className="sortable">
                Category {sortField === 'category' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>Payment Mode</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan="5" className="empty-row">No transactions found</td>
              </tr>
            ) : (
              paginatedData.map((t, idx) => (
                <tr key={idx}>
                  <td className="date-cell">{new Date(t.date).toLocaleDateString('en-IN')}</td>
                  <td className="amount-cell">Rs. {parseFloat(t.amount).toLocaleString()}</td>
                  <td>
                    <span
                      className="category-badge"
                      style={{ backgroundColor: CATEGORY_COLORS[t.category] || '#636e72' }}
                    >
                      {t.category}
                    </span>
                  </td>
                  <td className="payment-cell">{t.payment_mode}</td>
                  <td className="desc-cell">{t.description || '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="page-btn"
          >
            <FiChevronLeft />
          </button>
          <span className="page-info">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="page-btn"
          >
            <FiChevronRight />
          </button>
        </div>
      )}
    </div>
  );
}

export default TransactionHistory;
