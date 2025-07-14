import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Clock, User, Tag, AlertTriangle, CheckCircle } from 'lucide-react';
import { useTickets } from '../hooks/useTickets.ts';
import { formatDate, formatTimeAgo, getPriorityColor, getStatusColor } from '../utils/index.ts';
import LoadingSpinner from '../components/LoadingSpinner.tsx';
import { TicketPriority, TicketStatus } from '../types/index.ts';

const TicketDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: tickets, isLoading } = useTickets();

  if (isLoading) return <LoadingSpinner text="Loading ticket details..." />;

  const ticket = tickets?.find(t => t.id === id);

  if (!ticket) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Ticket Not Found</h2>
        <p className="text-gray-600 mb-6">The ticket you're looking for doesn't exist or has been removed.</p>
        <button
          onClick={() => navigate('/tickets')}
          className="btn btn-primary"
        >
          Back to Tickets
        </button>
      </div>
    );
  }

  const getPriorityBadgeClass = (priority: TicketPriority) => {
    switch (priority) {
      case TicketPriority.LOW:
        return 'bg-green-100 text-green-800';
      case TicketPriority.MEDIUM:
        return 'bg-yellow-100 text-yellow-800';
      case TicketPriority.HIGH:
        return 'bg-orange-100 text-orange-800';
      case TicketPriority.URGENT:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusBadgeClass = (status: TicketStatus) => {
    switch (status) {
      case TicketStatus.OPEN:
        return 'bg-blue-100 text-blue-800';
      case TicketStatus.IN_PROGRESS:
        return 'bg-purple-100 text-purple-800';
      case TicketStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800';
      case TicketStatus.RESOLVED:
        return 'bg-green-100 text-green-800';
      case TicketStatus.CLOSED:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-4xl mx-auto"
    >
      <div className="mb-6">
        <button
          onClick={() => navigate('/tickets')}
          className="flex items-center text-gray-600 hover:text-gray-900 transition-colors duration-200"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back to Tickets
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{ticket.title}</h1>
              <p className="text-gray-600 mt-1">Ticket #{ticket.id}</p>
            </div>
            <div className="flex items-center space-x-3">
              <span className={`badge ${getPriorityBadgeClass(ticket.priority)}`}>
                {ticket.priority}
              </span>
              <span className={`badge ${getStatusBadgeClass(ticket.status)}`}>
                {ticket.status}
              </span>
            </div>
          </div>
        </div>

        <div className="px-6 py-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="space-y-4">
              <div className="flex items-center text-gray-600">
                <User className="w-5 h-5 mr-2" />
                <span>Submitted by: {ticket.submittedBy}</span>
              </div>
              <div className="flex items-center text-gray-600">
                <Clock className="w-5 h-5 mr-2" />
                <span>Created: {formatDate(ticket.submittedAt)}</span>
              </div>
              {ticket.assignedTo && (
                <div className="flex items-center text-gray-600">
                  <User className="w-5 h-5 mr-2" />
                  <span>Assigned to: {ticket.assignedTo}</span>
                </div>
              )}
            </div>
            <div className="space-y-4">
              <div className="flex items-center text-gray-600">
                <Tag className="w-5 h-5 mr-2" />
                <span>Category: {ticket.category}</span>
              </div>
              {ticket.resolvedAt && (
                <div className="flex items-center text-gray-600">
                  <CheckCircle className="w-5 h-5 mr-2" />
                  <span>Resolved: {formatDate(ticket.resolvedAt)}</span>
                </div>
              )}
            </div>
          </div>

          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Description</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-gray-700 whitespace-pre-wrap">{ticket.description}</p>
            </div>
          </div>

          {ticket.classification && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Classification</h3>
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-medium text-blue-900">Category: {ticket.classification.category}</span>
                  <span className="text-sm text-blue-700">Confidence: {(ticket.classification.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="mb-3">
                  <span className="font-medium text-blue-900">Estimated Resolution Time: </span>
                  <span className="text-blue-700">{ticket.classification.estimatedResolutionTime} hours</span>
                </div>
                {ticket.classification.suggestedActions.length > 0 && (
                  <div>
                    <span className="font-medium text-blue-900">Suggested Actions:</span>
                    <ul className="mt-2 space-y-1">
                      {ticket.classification.suggestedActions.map((action, index) => (
                        <li key={index} className="text-blue-700">• {action}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {ticket.tags && ticket.tags.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {ticket.tags.map((tag, index) => (
                  <span key={index} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default TicketDetails;
