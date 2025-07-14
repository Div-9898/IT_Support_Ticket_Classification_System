import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Ticket, FilterOptions, CreateTicketRequest } from '../types/index.ts';
import apiService from '../services/api.ts';
import { toast } from 'react-toastify';

export const useTickets = (
  page: number = 1,
  limit: number = 10,
  filters?: FilterOptions
) => {
  return useQuery(
    ['tickets', page, limit, filters],
    () => apiService.getTickets(page, limit, filters),
    {
      keepPreviousData: true,
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );
};

export const useTicket = (id: string) => {
  return useQuery(
    ['ticket', id],
    () => apiService.getTicket(id),
    {
      enabled: !!id,
      staleTime: 2 * 60 * 1000, // 2 minutes
    }
  );
};

export const useCreateTicket = () => {
  const queryClient = useQueryClient();

  return useMutation(
    (ticket: CreateTicketRequest) => apiService.createTicket(ticket),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['tickets']);
        toast.success('Ticket created successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.message || 'Failed to create ticket');
      },
    }
  );
};

export const useUpdateTicket = () => {
  const queryClient = useQueryClient();

  return useMutation(
    ({ id, updates }: { id: string; updates: Partial<Ticket> }) =>
      apiService.updateTicket(id, updates),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['tickets']);
        queryClient.invalidateQueries(['ticket', data.id]);
        toast.success('Ticket updated successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.message || 'Failed to update ticket');
      },
    }
  );
};

export const useDeleteTicket = () => {
  const queryClient = useQueryClient();

  return useMutation(
    (id: string) => apiService.deleteTicket(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['tickets']);
        toast.success('Ticket deleted successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.message || 'Failed to delete ticket');
      },
    }
  );
};

export const useClassifyTicket = () => {
  const queryClient = useQueryClient();

  return useMutation(
    (id: string) => apiService.classifyTicket(id),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['tickets']);
        queryClient.invalidateQueries(['ticket', data.id]);
        toast.success('Ticket classified successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.message || 'Failed to classify ticket');
      },
    }
  );
};

export const useSearchTickets = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const searchTickets = async () => {
      if (!query.trim()) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const searchResults = await apiService.searchTickets(query);
        setResults(searchResults);
      } catch (error) {
        console.error('Search failed:', error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    const debounceTimer = setTimeout(searchTickets, 300);
    return () => clearTimeout(debounceTimer);
  }, [query]);

  return {
    query,
    setQuery,
    results,
    isLoading,
  };
};
