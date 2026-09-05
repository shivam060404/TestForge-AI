import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, PaginatedResponse, PaginationParams } from '@/lib/api';
import type { Environment, CreateEnvironmentRequest, UpdateEnvironmentRequest } from '@/types';

const ENVIRONMENTS_KEY = 'environments';

export function useEnvironments(projectId: string, pagination: PaginationParams = {}) {
  return useQuery({
    queryKey: [ENVIRONMENTS_KEY, projectId, pagination],
    queryFn: () => api.get<PaginatedResponse<Environment>>(`/projects/${projectId}/environments`, pagination),
    select: (response) => response.data,
    enabled: !!projectId,
  });
}

export function useEnvironment(environmentId: string) {
  return useQuery({
    queryKey: [ENVIRONMENTS_KEY, environmentId],
    queryFn: () => api.get<Environment>(`/environments/${environmentId}`),
    select: (response) => response.data,
    enabled: !!environmentId,
  });
}

export function useCreateEnvironment(projectId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateEnvironmentRequest) => api.post<Environment>(`/projects/${projectId}/environments`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ENVIRONMENTS_KEY, projectId] });
    },
  });
}

export function useUpdateEnvironment(environmentId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: UpdateEnvironmentRequest) => api.patch<Environment>(`/environments/${environmentId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ENVIRONMENTS_KEY] });
      queryClient.invalidateQueries({ queryKey: [ENVIRONMENTS_KEY, environmentId] });
    },
  });
}

export function useDeleteEnvironment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (environmentId: string) => api.delete(`/environments/${environmentId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ENVIRONMENTS_KEY] });
    },
  });
}