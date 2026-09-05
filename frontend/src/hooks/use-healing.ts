import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { HealingCandidate, ApproveHealingRequest } from '@/types';

const HEALING_KEY = 'healing';

export function useHealingCandidates(runId: string) {
  return useQuery({
    queryKey: [HEALING_KEY, runId],
    queryFn: () => api.get<HealingCandidate[]>(`/runs/${runId}/healing-candidates`),
    select: (response) => response.data,
    enabled: !!runId,
  });
}

export function useApproveHealing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ApproveHealingRequest) => api.post(`/healing-candidates/${data.candidate_id}/${data.approved ? 'approve' : 'reject'}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [HEALING_KEY] });
    },
  });
}

export function useProjectHealingCandidates(projectId: string) {
  return useQuery({
    queryKey: [HEALING_KEY, 'project', projectId],
    queryFn: () => api.get<HealingCandidate[]>(`/projects/${projectId}/healing-candidates`),
    select: (response) => response.data,
    enabled: !!projectId,
  });
}