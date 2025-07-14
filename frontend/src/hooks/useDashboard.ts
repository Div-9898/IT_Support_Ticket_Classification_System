import { useQuery } from 'react-query';
import { DashboardStats } from '../types/index.ts';
import apiService from '../services/api.ts';

export const useDashboard = () => {
  return useQuery(
    ['dashboard'],
    () => apiService.getDashboardStats(),
    {
      staleTime: 2 * 60 * 1000, // 2 minutes
      refetchInterval: 5 * 60 * 1000, // 5 minutes
    }
  );
};
