import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.tsx';
import { validateEmail } from '../utils/index.ts';
import { toast } from 'react-toastify';
import './Login.css';

const CreateAccount: React.FC = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!formData.firstName.trim()) {
      setError('First name is required');
      return;
    }

    if (!formData.lastName.trim()) {
      setError('Last name is required');
      return;
    }

    if (!validateEmail(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);
    
    try {
      await register(formData.firstName, formData.lastName, formData.email, formData.password);
      toast.success('Account created successfully!');
      navigate('/dashboard');
    } catch (error: any) {
      setError(error.response?.data?.message || 'Registration failed. Please try again.');
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
        <h2>Create Account</h2>
        <form onSubmit={handleSubmit}>
          <label htmlFor="firstName">First Name</label>
          <input 
            type="text" 
            id="firstName" 
            name="firstName" 
            placeholder="Enter your first name" 
            value={formData.firstName}
            onChange={handleChange}
            required 
          />

          <label htmlFor="lastName">Last Name</label>
          <input 
            type="text" 
            id="lastName" 
            name="lastName" 
            placeholder="Enter your last name" 
            value={formData.lastName}
            onChange={handleChange}
            required 
          />

          <label htmlFor="email">Email</label>
          <input 
            type="email" 
            id="email" 
            name="email" 
            placeholder="Enter your email" 
            value={formData.email}
            onChange={handleChange}
            required 
          />

          <label htmlFor="password">Password</label>
          <input 
            type="password" 
            id="password" 
            name="password" 
            placeholder="Create a password" 
            value={formData.password}
            onChange={handleChange}
            required 
          />

          <label htmlFor="confirmPassword">Confirm Password</label>
          <input 
            type="password" 
            id="confirmPassword" 
            name="confirmPassword" 
            placeholder="Confirm your password" 
            value={formData.confirmPassword}
            onChange={handleChange}
            required 
          />

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </button>

          <div className="form-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/login'); }}>Already have an account? Sign In</a>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateAccount;
