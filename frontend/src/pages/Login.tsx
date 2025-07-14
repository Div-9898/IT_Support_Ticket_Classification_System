import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.tsx';
import { validateEmail } from '../utils/index.ts';
import { toast } from 'react-toastify';
import './Login.css';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);
    
    try {
      await login(email, password);
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error: any) {
      setError(error.response?.data?.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container" style={{backgroundImage: `url(${process.env.PUBLIC_URL}/images/login-illustration.jpg)`}}>
      {/* Glowing Stars */}
      <div className="stars">
        <div className="star large"></div>
        <div className="star medium"></div>
        <div className="star small"></div>
        <div className="star medium"></div>
        <div className="star large"></div>
        <div className="star small"></div>
        <div className="star medium"></div>
        <div className="star small"></div>
        <div className="star large"></div>
        <div className="star medium"></div>
      </div>

      <div className="form-section">
        <h2>Welcome Back</h2>
        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>
          <input 
            type="email" 
            id="email" 
            name="email" 
            placeholder="Enter your email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required 
          />

          <label htmlFor="password">Password</label>
          <input 
            type="password" 
            id="password" 
            name="password" 
            placeholder="Enter your password" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required 
          />

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Log In'}
          </button>

          <div className="form-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/forgot-password'); }}>Forgot Password?</a>
            <span className="divider">•</span>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/create-account'); }}>Create Account</a>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
