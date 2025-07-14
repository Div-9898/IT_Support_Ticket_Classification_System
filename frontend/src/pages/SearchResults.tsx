import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, ArrowLeft } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner.tsx';
import { useQuery } from 'react-query';
import apiService from '../services/api.ts';
import { Ticket } from '../types/index.ts';

const SearchResults: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const query = queryParams.get('q') || '';

  const { data, isLoading, error } = useQuery(['search', query], () => apiService.searchTickets(query), {
    enabled: !!query,
  });

  useEffect(() => {
    if (!query) {
      navigate('/');
    }
  }, [query, navigate]);

  if (isLoading) return <LoadingSpinner text="Searching..." />;
  if (error) return <p className="text-red-500">An error occurred: {(error as Error).message}</p>;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-4xl mx-auto"
    >
      <div className="mb-6">
        <button
          onClick={() => navigate('/')}
          className="flex items-center text-gray-600 hover:text-gray-900 transition-colors duration-200"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back to Dashboard
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center">
            <Search className="w-6 h-6 text-blue-600 mr-3" />
            <h1 className="text-2xl font-bold text-gray-900">Search Results for "{query}"</h1>
          </div>
        </div>

        <div className="px-6 py-6 space-y-4">
          {!data || data.length === 0 ? (
            <p className="text-gray-500">No results found.</p>
          ) : (
            <ul className="space-y-4">
              {data.map((ticket: Ticket) => (
                <li key={ticket.id} className="bg-gray-50 p-4 rounded-lg shadow-sm">
                  <h2 className="text-lg font-semibold text-gray-900 mb-2">{ticket.title}</h2>
                  <p className="text-sm text-gray-700 mb-1">{ticket.description}</p>
                  <div className="text-sm text-gray-500">Submitted by: {ticket.submittedBy} | {new Date(ticket.submittedAt).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default SearchResults;
