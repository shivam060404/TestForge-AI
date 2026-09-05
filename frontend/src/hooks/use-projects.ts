import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, PaginatedResponse, PaginationParams } from '@/lib/api';
import type { Project, CreateProjectRequest, UpdateProjectRequest } from '@/types';

const PROJECTS_KEY = 'projects';

export function useProjects(pagination: PaginationParams = {}) {
  return useQuery({
    queryKey: [PROJECTS_KEY, pagination],
    queryFn: () => api.get<PaginatedResponse<Project>>('/projects', pagination),
    select: (response) => response.data,
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: [PROJECTS_KEY, projectId],
    queryFn: () => api.get<Project>(`/projects/${projectId}`),
    select: (response) => response.data,
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateProjectRequest) => api.post<Project>('/projects', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROJECTS_KEY] });
    },
  });
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: UpdateProjectRequest) => api.patch<Project>(`/projects/${projectId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROJECTS_KEY] });
      queryClient.invalidateQueries({ queryKey: [PROJECTS_KEY, projectId] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (projectId: string) => api.delete(`/projects/${projectId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROJECTS_KEY] });
    },
  });
}