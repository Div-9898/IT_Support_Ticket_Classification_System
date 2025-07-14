import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext.tsx';
import apiService from '../services/api.ts';
import LoadingSpinner from '../components/LoadingSpinner.tsx';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';
import { 
  Brain, 
  Zap, 
  Target, 
  Clock, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  Settings,
  Users,
  MessageSquare
} from 'lucide-react';
import { ClassificationResult, UserRole } from '../types/index.ts';

const COLORS = ['#3b82f6', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6', '#6366f1', '#f97316'];

// Sample tickets for demonstration
const SAMPLE_TICKETS = [
  {
    title: "Cannot connect to office WiFi",
    description: "I am unable to connect to the office WiFi network. It keeps asking for password but shows authentication failed.",
    expectedCategory: "Network"
  },
  {
    title: "Laptop screen is black",
    description: "My laptop turns on but the screen remains black. I can hear the fan running but nothing displays.",
    expectedCategory: "Hardware"
  },
  {
    title: "Email not syncing",
    description: "My Outlook emails are not syncing properly. I'm not receiving new emails since yesterday.",
    expectedCategory: "Email"
  },
  {
    title: "Software installation failed",
    description: "I cannot install the new accounting software. It shows error code 1603 during installation.",
    expectedCategory: "Software"
  },
  {
    title: "Password reset request",
    description: "I forgot my Active Directory password and need to reset it to access company resources.",
    expectedCategory: "Security"
  },
  {
    title: "Cannot access shared folder",
    description: "I don't have permission to access the shared folder on the network drive. Getting access denied error.",
    expectedCategory: "Access"
  }
];

interface ModelPerformance {
  modelName: string;
  accuracy: number;
  predictions: number;
  avgConfidence: number;
  avgProcessingTime: number;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [inputText, setInputText] = useState('');
  const [inputTitle, setInputTitle] = useState('');
  const [classificationResult, setClassificationResult] = useState<ClassificationResult | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [selectedSample, setSelectedSample] = useState('');
  const [classificationHistory, setClassificationHistory] = useState<any[]>([]);
  const [modelPerformance, setModelPerformance] = useState<ModelPerformance[]>([]);
  const [showModelDetails, setShowModelDetails] = useState(false);

  // Mock model performance data
  useEffect(() => {
    setModelPerformance([
      { modelName: 'Naive Bayes', accuracy: 85.2, predictions: 1247, avgConfidence: 0.78, avgProcessingTime: 45 },
      { modelName: 'Random Forest', accuracy: 89.1, predictions: 1247, avgConfidence: 0.82, avgProcessingTime: 67 },
      { modelName: 'SVM', accuracy: 87.6, predictions: 1247, avgConfidence: 0.80, avgProcessingTime: 89 },
      { modelName: 'DistilBERT', accuracy: 92.4, predictions: 1247, avgConfidence: 0.88, avgProcessingTime: 156 }
    ]);
  }, []);

  const handleClassifyText = async () => {
    if (!inputTitle.trim() && !inputText.trim()) return;
    
    setIsClassifying(true);
    try {
      const result = await apiService.classifyText(inputTitle, inputText);
      setClassificationResult(result);
      
      // Add to history
      setClassificationHistory(prev => [{
        id: Date.now(),
        title: inputTitle,
        description: inputText,
        result: result,
        timestamp: new Date().toISOString()
      }, ...prev.slice(0, 9)]); // Keep last 10 results
      
    } catch (error) {
      console.error('Classification failed:', error);
    } finally {
      setIsClassifying(false);
    }
  };

  const handleSampleSelect = (sample: any) => {
    setInputTitle(sample.title);
    setInputText(sample.description);
    setSelectedSample(sample.expectedCategory);
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Hardware': '#ef4444',
      'Software': '#3b82f6', 
      'Network': '#f59e0b',
      'Security': '#8b5cf6',
      'Access': '#10b981',
      'Email': '#f97316',
      'Other': '#6b7280'
    };
    return colors[category] || '#6b7280';
  };

  const categoryDistribution = classificationHistory.reduce((acc, item) => {
    const category = item.result?.predicted_category || 'Other';
    acc[category] = (acc[category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const chartData = Object.entries(categoryDistribution).map(([category, count]) => ({
    category,
    count,
    percentage: ((count / classificationHistory.length) * 100).toFixed(1)
  }));

  if (user?.role === UserRole.ADMIN) {
    return <AdminDashboard />;
  }

  return (
    <motion.div 
      className="flex flex-col gap-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg shadow-sm p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">IT Support Ticket Classification System</h1>
            <p className="text-blue-100">
              Powered by Advanced NLP & Machine Learning Models
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <Brain className="w-12 h-12 text-blue-200" />
            <div className="text-right">
              <div className="text-2xl font-bold">AI-Powered</div>
              <div className="text-sm text-blue-200">Classification</div>
            </div>
          </div>
        </div>
      </div>

      {/* Classification Input Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div 
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <MessageSquare className="w-5 h-5 mr-2 text-blue-500" />
            Ticket Classification Demo
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ticket Title
              </label>
              <input
                type="text"
                value={inputTitle}
                onChange={(e) => setInputTitle(e.target.value)}
                placeholder="Enter ticket title..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ticket Description
              </label>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Describe the IT issue..."
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <button
              onClick={handleClassifyText}
              disabled={isClassifying || (!inputTitle.trim() && !inputText.trim())}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isClassifying ? (
                <LoadingSpinner text="Classifying..." />
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  Classify Ticket
                </>
              )}
            </button>
          </div>
          
          {/* Sample Tickets */}
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Sample Tickets (Click to try):</h4>
            <div className="space-y-2">
              {SAMPLE_TICKETS.map((sample, index) => (
                <button
                  key={index}
                  onClick={() => handleSampleSelect(sample)}
                  className="w-full text-left p-3 bg-gray-50 hover:bg-blue-50 rounded-md transition-colors border border-gray-200 hover:border-blue-300"
                >
                  <div className="font-medium text-sm text-gray-900">{sample.title}</div>
                  <div className="text-xs text-gray-600 mt-1 truncate">{sample.description}</div>
                  <div className="text-xs text-blue-600 mt-1">Expected: {sample.expectedCategory}</div>
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Classification Results */}
        <motion.div 
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Target className="w-5 h-5 mr-2 text-green-500" />
            Classification Results
          </h3>
          
          {classificationResult ? (
            <div className="space-y-4">
              <div className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-lg border border-green-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-lg font-bold text-gray-900">
                    {classificationResult.predicted_category}
                  </div>
                  <div 
                    className="px-3 py-1 rounded-full text-white text-sm font-medium"
                    style={{ backgroundColor: getCategoryColor(classificationResult.predicted_category) }}
                  >
                    {(classificationResult.confidence_score * 100).toFixed(1)}% Confidence
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  Model: {classificationResult.model_name} v{classificationResult.model_version}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm text-gray-600">Processing Time</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {classificationResult.processing_time_ms}ms
                  </div>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm text-gray-600">Urgency Score</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {classificationResult.urgency_score}/10
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Suggested Actions:</h4>
                <ul className="space-y-1">
                  {classificationResult.suggested_actions.map((action, index) => (
                    <li key={index} className="text-sm text-gray-700 flex items-start">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      {action}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Keywords Identified:</h4>
                <div className="flex flex-wrap gap-2">
                  {classificationResult.keywords_identified.map((keyword, index) => (
                    <span 
                      key={index}
                      className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Model Architecture:</h4>
                <div className="text-sm text-gray-700 space-y-1">
                  <div>• Preprocessing: {classificationResult.preprocessing_applied.join(', ')}</div>
                  <div>• Sentiment Score: {classificationResult.sentiment_score.toFixed(2)}</div>
                  <div>• Estimated Resolution: {classificationResult.estimated_resolution_time} minutes</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Target className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Enter a ticket description and click "Classify Ticket" to see AI-powered classification results</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Model Performance & Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div 
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-purple-500" />
            Model Performance
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={modelPerformance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="modelName" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="accuracy" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div 
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-orange-500" />
            Processing Speed
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={modelPerformance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="modelName" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="avgProcessingTime" 
                stroke="#f59e0b" 
                strokeWidth={3}
                dot={{ fill: '#f59e0b', strokeWidth: 2, r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div 
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertCircle className="w-5 h-5 mr-2 text-red-500" />
            Category Distribution
          </h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="count"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  label={({ category, percentage }) => `${category}: ${percentage}%`}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getCategoryColor(entry.category)} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No classifications yet</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Classification History */}
      {classificationHistory.length > 0 && (
        <motion.div 
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.7 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Classifications</h3>
          <div className="space-y-4">
            {classificationHistory.map((item, index) => (
              <div key={item.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <div className="font-medium text-gray-900">{item.title}</div>
                  <div 
                    className="px-2 py-1 rounded-full text-white text-xs font-medium"
                    style={{ backgroundColor: getCategoryColor(item.result?.predicted_category) }}
                  >
                    {item.result?.predicted_category}
                  </div>
                </div>
                <div className="text-sm text-gray-600 mb-2">{item.description}</div>
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span>Confidence: {(item.result?.confidence_score * 100).toFixed(1)}%</span>
                  <span>Processing: {item.result?.processing_time_ms}ms</span>
                  <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

// Admin Dashboard Component
const AdminDashboard: React.FC = () => {
  const [tickets, setTickets] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    // Mock ticket data for admin
    setTickets([
      {
        id: '1',
        title: 'WiFi Connection Issues',
        description: 'Unable to connect to office network',
        category: 'Network',
        priority: 'High',
        status: 'Open',
        submittedBy: 'john.doe@company.com',
        submittedAt: new Date().toISOString(),
        classification: {
          confidence: 0.89,
          suggestedActions: ['Check network configuration', 'Reset router'],
          processingTime: 156
        }
      },
      {
        id: '2',
        title: 'Software Installation Problem',
        description: 'Cannot install new accounting software',
        category: 'Software',
        priority: 'Medium',
        status: 'In Progress',
        submittedBy: 'jane.smith@company.com',
        submittedAt: new Date().toISOString(),
        assignedTo: 'Tech Support',
        classification: {
          confidence: 0.94,
          suggestedActions: ['Check system requirements', 'Run as administrator'],
          processingTime: 134
        }
      }
    ]);
    setIsLoading(false);
  }, []);

  const filteredTickets = tickets.filter(ticket => 
    filter === 'all' || ticket.status.toLowerCase() === filter
  );

  const updateTicketStatus = (ticketId: string, newStatus: string) => {
    setTickets(prev => prev.map(ticket => 
      ticket.id === ticketId ? { ...ticket, status: newStatus } : ticket
    ));
  };

  if (isLoading) return <LoadingSpinner text="Loading Admin Dashboard..." />;

  return (
    <motion.div 
      className="flex flex-col gap-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg shadow-sm p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">Admin Dashboard</h1>
            <p className="text-purple-100">Manage and resolve IT support tickets</p>
          </div>
          <Settings className="w-12 h-12 text-purple-200" />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Total Tickets', value: tickets.length, icon: MessageSquare, color: 'blue' },
          { label: 'Open Tickets', value: tickets.filter(t => t.status === 'Open').length, icon: AlertCircle, color: 'red' },
          { label: 'In Progress', value: tickets.filter(t => t.status === 'In Progress').length, icon: Clock, color: 'yellow' },
          { label: 'Resolved', value: tickets.filter(t => t.status === 'Resolved').length, icon: CheckCircle, color: 'green' }
        ].map((stat, index) => (
          <motion.div
            key={index}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <stat.icon className={`w-8 h-8 text-${stat.color}-500`} />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Filter Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex space-x-4 mb-6">
          {['all', 'open', 'in progress', 'resolved'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        {/* Tickets Table */}
        <div className="space-y-4">
          {filteredTickets.map((ticket) => (
            <div key={ticket.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900">{ticket.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{ticket.description}</p>
                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                    <span>By: {ticket.submittedBy}</span>
                    <span>Category: {ticket.category}</span>
                    <span>Priority: {ticket.priority}</span>
                    {ticket.classification && (
                      <span>AI Confidence: {(ticket.classification.confidence * 100).toFixed(1)}%</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span 
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      ticket.status === 'Open' ? 'bg-red-100 text-red-800' :
                      ticket.status === 'In Progress' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}
                  >
                    {ticket.status}
                  </span>
                  <select
                    value={ticket.status}
                    onChange={(e) => updateTicketStatus(ticket.id, e.target.value)}
                    className="text-xs border border-gray-300 rounded px-2 py-1"
                  >
                    <option value="Open">Open</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Resolved">Resolved</option>
                    <option value="Closed">Closed</option>
                  </select>
                </div>
              </div>
              
              {ticket.classification && (
                <div className="bg-gray-50 rounded-lg p-3 mt-3">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">AI-Generated Suggestions:</h4>
                  <ul className="text-sm text-gray-700 space-y-1">
                    {ticket.classification.suggestedActions.map((action: string, index: number) => (
                      <li key={index} className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default Dashboard;