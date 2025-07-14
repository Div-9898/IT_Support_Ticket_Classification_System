import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  Ticket, 
  CreateTicketRequest, 
  DashboardStats, 
  ApiResponse, 
  PaginatedResponse, 
  FilterOptions,
  User 
} from '../types/index.ts';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Tickets
  async getTickets(
    page: number = 1,
    limit: number = 10,
    filters?: FilterOptions
  ): Promise<PaginatedResponse<Ticket>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters,
    });

    const response = await this.api.get<PaginatedResponse<Ticket>>(`/tickets?${params}`);
    return response.data;
  }

  async getTicket(id: string): Promise<Ticket> {
    const response = await this.api.get<ApiResponse<Ticket>>(`/tickets/${id}`);
    return response.data.data;
  }

  async createTicket(ticket: CreateTicketRequest): Promise<Ticket> {
    const response = await this.api.post<ApiResponse<Ticket>>('/tickets', ticket);
    return response.data.data;
  }

  async updateTicket(id: string, updates: Partial<Ticket>): Promise<Ticket> {
    const response = await this.api.put<ApiResponse<Ticket>>(`/tickets/${id}`, updates);
    return response.data.data;
  }

  async deleteTicket(id: string): Promise<void> {
    await this.api.delete(`/tickets/${id}`);
  }

  async classifyTicket(id: string): Promise<Ticket> {
    const response = await this.api.post<ApiResponse<Ticket>>(`/tickets/${id}/classify`);
    return response.data.data;
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.api.get<ApiResponse<DashboardStats>>('/dashboard/stats');
    return response.data.data;
  }

  // Users
  async getUsers(): Promise<User[]> {
    const response = await this.api.get<ApiResponse<User[]>>('/users');
    return response.data.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<User>('/auth/me');
    return response.data;
  }

  // Authentication
  async login(email: string, password: string): Promise<{ token: string; user: User }> {
    const response = await this.api.post<{ token: string; user: User; token_type: string }>(
      '/auth/login',
      { email, password }
    );
    return response.data;
  }

  async register(userData: {
    email: string;
    name: string;
    password: string;
    role?: string;
    department?: string;
    phone?: string;
    bio?: string;
  }): Promise<User> {
    const response = await this.api.post<User>('/auth/register', userData);
    return response.data;
  }

  async logout(): Promise<void> {
    await this.api.post('/auth/logout');
    localStorage.removeItem('authToken');
  }

  // Search
  async searchTickets(query: string): Promise<Ticket[]> {
    const response = await this.api.get<ApiResponse<Ticket[]>>(`/search/tickets?q=${encodeURIComponent(query)}`);
    return response.data.data;
  }

  // File upload
  async uploadFile(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await this.api.post<ApiResponse<{ url: string }>>(
      '/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data.url;
  }

  // NLP Classification
  async classifyText(title: string, description: string): Promise<any> {
    const response = await this.api.post('/tickets/classify-text', {
      title,
      description
    });
    return response.data;
  }

  // Admin - Get all tickets for management
  async getAllTicketsForAdmin(): Promise<Ticket[]> {
    const response = await this.api.get<Ticket[]>('/tickets/admin/all');
    return response.data;
  }

  // Update ticket status
  async updateTicketStatus(id: string, status: string, assignedTo?: string): Promise<Ticket> {
    const response = await this.api.put<Ticket>(`/tickets/${id}/status`, {
      status,
      assignedTo
    });
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;
