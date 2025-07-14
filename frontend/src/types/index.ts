export interface Ticket {
  id: string;
  title: string;
  description: string;
  category: TicketCategory;
  priority: TicketPriority;
  status: TicketStatus;
  submittedBy: string;
  submittedAt: string;
  assignedTo?: string;
  resolvedAt?: string;
  classification?: Classification;
  tags: string[];
}

export interface Classification {
  category: string;
  confidence: number;
  suggestedActions: string[];
  estimatedResolutionTime: number;
  modelName?: string;
  processingTime?: number;
  keywordsIdentified?: string[];
  sentimentScore?: number;
  urgencyScore?: number;
}

export interface ClassificationResult {
  predicted_category: string;
  confidence_score: number;
  model_name: string;
  model_version: string;
  suggested_actions: string[];
  keywords_identified: string[];
  sentiment_score: number;
  urgency_score: number;
  estimated_resolution_time: number;
  processing_time_ms: number;
  preprocessing_applied: string[];
  features: any;
  all_predictions: any;
}

export enum TicketCategory {
  HARDWARE = 'Hardware',
  SOFTWARE = 'Software',
  NETWORK = 'Network',
  SECURITY = 'Security',
  ACCESS = 'Access',
  EMAIL = 'Email',
  OTHER = 'Other'
}

export enum TicketPriority {
  LOW = 'Low',
  MEDIUM = 'Medium',
  HIGH = 'High',
  URGENT = 'Urgent'
}

export enum TicketStatus {
  OPEN = 'Open',
  IN_PROGRESS = 'In Progress',
  PENDING = 'Pending',
  RESOLVED = 'Resolved',
  CLOSED = 'Closed'
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  department: string;
}

export enum UserRole {
  USER = 'User',
  AGENT = 'Agent',
  ADMIN = 'Admin'
}

export interface DashboardStats {
  totalTickets: number;
  openTickets: number;
  resolvedTickets: number;
  avgResolutionTime: number;
  categoryDistribution: CategoryStats[];
  priorityDistribution: PriorityStats[];
  recentActivity: Activity[];
}

export interface CategoryStats {
  category: string;
  count: number;
  percentage: number;
}

export interface PriorityStats {
  priority: string;
  count: number;
  percentage: number;
}

export interface Activity {
  id: string;
  ticketId: string;
  action: string;
  user: string;
  timestamp: string;
}

export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface FilterOptions {
  category?: TicketCategory;
  priority?: TicketPriority;
  status?: TicketStatus;
  assignedTo?: string;
  submittedBy?: string;
  dateRange?: {
    from: string;
    to: string;
  };
}

export interface CreateTicketRequest {
  title: string;
  description: string;
  category: TicketCategory;
  priority: TicketPriority;
}
