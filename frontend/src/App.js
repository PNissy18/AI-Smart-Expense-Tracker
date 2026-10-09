import React, { useState } from 'react';
import { Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import AddTransaction from './pages/AddTransaction';
import TransactionHistory from './pages/TransactionHistory';
import AgentsHub from './pages/AgentsHub';
import FinancialGoals from './pages/FinancialGoals';
import UploadCSV from './pages/UploadCSV';
import InvestmentSuggestions from './pages/InvestmentSuggestions';

import { FiHome, FiPlusCircle, FiList, FiZap, FiTarget, FiUpload, FiMenu, FiX, FiLogOut, FiDollarSign } from 'react-icons/fi';
import { TbPigMoney } from 'react-icons/tb';

function App() {
  const { user, loading, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#f8f9fe' }}>
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
        <ToastContainer position="bottom-right" autoClose={3000} theme="colored" />
      </>
    );
  }

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <FiHome /> },
    { path: '/add', label: 'Add', icon: <FiPlusCircle /> },
    { path: '/history', label: 'History', icon: <FiList /> },
    { path: '/agents', label: 'AI Agents', icon: <FiZap /> },
    { path: '/goals', label: 'Goals', icon: <FiTarget /> },
    { path: '/invest', label: 'Invest', icon: <FiDollarSign /> },
    { path: '/upload', label: 'Upload', icon: <FiUpload /> },
  ];

  const userInitial = user.name ? user.name.charAt(0).toUpperCase() : 'U';

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="top-navbar">
        <div className="navbar-left">
          <div className="navbar-logo-icon">
            <TbPigMoney size={22} />
          </div>
          <span className="navbar-logo-text">Smart Expense Tracker</span>
        </div>

        {/* Desktop nav links */}
        <nav className="navbar-center">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Mobile hamburger */}
        <button className="mobile-menu-btn" onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <FiX size={22} /> : <FiMenu size={22} />}
        </button>

        {/* User section */}
        <div className="navbar-right">
          <div className="user-avatar-circle">{userInitial}</div>
          <span className="navbar-user-name">{user.name}</span>
          <button className="navbar-logout-btn" onClick={logout} title="Logout">
            <FiLogOut size={16} />
          </button>
        </div>
      </header>

      {/* Mobile dropdown nav */}
      {menuOpen && (
        <nav className="mobile-nav-dropdown">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setMenuOpen(false)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
      )}

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/add" element={<AddTransaction />} />
          <Route path="/history" element={<TransactionHistory />} />
          <Route path="/agents" element={<AgentsHub />} />
          <Route path="/goals" element={<FinancialGoals />} />
          <Route path="/invest" element={<InvestmentSuggestions />} />
          <Route path="/upload" element={<UploadCSV />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>

      <ToastContainer position="bottom-right" autoClose={3000} theme="colored" />
    </div>
  );
}

export default App;
