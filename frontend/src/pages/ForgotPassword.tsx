import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { validateEmail } from '../utils/index.ts';
import { toast } from 'react-toastify';
import './Login.css';

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);
    
    try {
      // TODO: Implement forgot password API call
      // await forgotPassword(email);
      
      // Simulate API call for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast.success('Password reset link sent to your email!');
      setIsSubmitted(true);
    } catch (error: any) {
      setError(error.response?.data?.message || 'Failed to send reset link. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
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
          <h2>Check Your Email</h2>
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <p style={{ color: '#d1c4e9', fontSize: '1.1rem', marginBottom: '20px' }}>
              We've sent a password reset link to:
            </p>
            <p style={{ color: '#f5576c', fontSize: '1.2rem', fontWeight: 'bold' }}>
              {email}
            </p>
            <p style={{ color: '#d1c4e9', fontSize: '0.9rem', marginTop: '20px' }}>
              Please check your email and click the link to reset your password.
            </p>
          </div>

          <div className="form-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/login'); }}>Back to Sign In</a>
            <span className="divider">•</span>
            <a href="#" onClick={(e) => { e.preventDefault(); setIsSubmitted(false); }}>Try Different Email</a>
          </div>
        </div>
      </div>
    );
  }

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
        <h2>Reset Password</h2>
        <p style={{ color: '#d1c4e9', fontSize: '0.9rem', marginBottom: '30px', textAlign: 'center' }}>
          Enter your email address and we'll send you a link to reset your password.
        </p>
        
        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>
          <input 
            type="email" 
            id="email" 
            name="email" 
            placeholder="Enter your email address" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required 
          />

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading ? 'Sending Reset Link...' : 'Send Reset Link'}
          </button>

          <div className="form-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/login'); }}>Back to Sign In</a>
            <span className="divider">•</span>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/create-account'); }}>Create Account</a>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ForgotPassword;
