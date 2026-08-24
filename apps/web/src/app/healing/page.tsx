'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useProjectHealingCandidates, useApproveHealing } from '@/hooks/use-healing';
import { useProjects } from '@/hooks/use-projects';
import { useToast } from '@/hooks/use-toast';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  Search,
  Filter,
  Code,
  ExternalLink,
} from 'lucide-react';
import { formatDate, getStatusColor, cn } from '@/lib/utils';
import { PaginationParams } from '@/types';
import type { HealingCandidate } from '@/types';

export default function HealingCenterPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get('projectId') || '';
  const runId = searchParams.get('runId') || '';
  const [pagination, setPagination] = useState<PaginationParams>({ page: 1, page_size: 20 });
  const [statusFilter, setStatusFilter] = useState<'pending' | 'approved' | 'rejected' | ''>('');
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<HealingCandidate | null>(null);
  const [reviewFeedback, setReviewFeedback] = useState('');

  const { data: projectsData } = useProjects({ page_size: 100 });
  const { data: healingData, isLoading, refetch } = useProjectHealingCandidates(projectId || runId || '');
  const approveHealing = useApproveHealing();
  const { toast } = useToast();

  const filteredCandidates = (healingData || []).filter((c) => !statusFilter || c.status === statusFilter);

  const handleReview = (candidate: HealingCandidate) => {
    setSelectedCandidate(candidate);
    setReviewFeedback('');
    setReviewDialogOpen(true);
  };

  const handleApprove = async (approved: boolean) => {
    if (!selectedCandidate) return;

    try {
      await approveHealing.mutateAsync({
        candidate_id: selectedCandidate.id,
        approved,
        feedback: reviewFeedback || undefined,
      });
      toast({ title: approved ? 'Healing approved' : 'Healing rejected' });
      setReviewDialogOpen(false);
      setSelectedCandidate(null);
      refetch();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to review healing', variant: 'destructive' });
    }
  };

  const getStrategyIcon = (strategy: string) => {
    const icons: Record<string, string> = {
      css: 'CSS',
      xpath: 'XPath',
      text: 'Text',
      role: 'Role',
      testId: 'TestID',
      id: 'ID',
      name: 'Name',
      placeholder: 'Placeholder',
      label: 'Label',
    };
    return icons[strategy] || strategy;
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          {[1, 2, 3].map(i => (
            <Card key={i}>
              <CardContent className="py-4">
                <div className="h-4 bg-muted rounded w-1/2 mb-2" />
                <div className="h-4 bg-muted rounded w-3/4" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Healing Center</h1>
          <p className="text-muted-foreground">Review and approve self-healing locator suggestions</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={projectId} onValueChange={(v) => window.location.search = `?projectId=${v}`}>
            <SelectTrigger className="w-[200px]"><SelectValue placeholder="Select project" /></SelectTrigger>
            <SelectContent>
              {projectsData?.items.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
            <SelectTrigger className="w-[180px]"><SelectValue placeholder="All statuses" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="">All statuses</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex-1" />
        <span className="text-sm text-muted-foreground">
          {filteredCandidates.length} candidate{filteredCandidates.length !== 1 ? 's' : ''}
        </span>
      </div>

      {filteredCandidates.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-medium">No healing candidates</h3>
            <p className="text-muted-foreground">
              {statusFilter ? 'No candidates with this status' : 'Healing candidates appear when tests fail and the system suggests alternative locators'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredCandidates.map((candidate) => (
            <Card key={candidate.id}>
              <CardContent className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge variant="secondary">{candidate.original_strategy}</Badge>
                      <Badge className={cn(getStatusColor(candidate.status))}>{candidate.status}</Badge>
                      <span className="text-sm text-muted-foreground">Confidence: {Math.round(candidate.confidence * 100)}%</span>
                      <span className="text-sm text-muted-foreground">Run: {candidate.run_id.slice(0, 8)}...</span>
                    </div>
                    <div className="grid gap-2 md:grid-cols-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">Original:</span>
                        <code className="ml-2 text-red-500 break-all">{candidate.original_locator}</code>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Suggested:</span>
                        <code className="ml-2 text-green-500 break-all">{candidate.suggested_locator}</code>
                      </div>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">{candidate.reasoning}</p>
                  </div>
                  <div className="flex items-center gap-2 ml-4 shrink-0">
                    {candidate.status === 'pending' && (
                      <>
                        <Button size="sm" onClick={() => handleReview(candidate)}>
                          Review
                        </Button>
                      </>
                    )}
                    {candidate.status !== 'pending' && (
                      <Badge variant="outline" className={candidate.status === 'approved' ? 'text-green-500 border-green-500' : 'text-red-500 border-red-500'}>
                        {candidate.status === 'approved' ? <CheckCircle className="h-3 w-3 mr-1" /> : <XCircle className="h-3 w-3 mr-1" />}
                        {candidate.status}
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

        </div>
      )}

      <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Review Healing Candidate</DialogTitle>
          </DialogHeader>
          {selectedCandidate && (
            <div className="py-4 space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium mb-1">Original Locator</label>
                  <div className="p-2 bg-red-50 border border-red-200 rounded text-sm font-mono text-red-700 break-all">
                    {selectedCandidate.original_locator}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Strategy: {getStrategyIcon(selectedCandidate.original_strategy)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Suggested Locator</label>
                  <div className="p-2 bg-green-50 border border-green-200 rounded text-sm font-mono text-green-700 break-all">
                    {selectedCandidate.suggested_locator}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Strategy: {getStrategyIcon(selectedCandidate.suggested_strategy)}</p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Reasoning</label>
                <p className="text-sm">{selectedCandidate.reasoning}</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Confidence</label>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-primary h-2 rounded-full" style={{ width: `${selectedCandidate.confidence * 100}%` }} />
                </div>
                <p className="text-xs text-muted-foreground mt-1">{Math.round(selectedCandidate.confidence * 100)}%</p>
              </div>
              <div>
                <Label htmlFor="feedback">Feedback (optional)</Label>
                <textarea
                  id="feedback"
                  className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[80px]"
                  value={reviewFeedback}
                  onChange={(e) => setReviewFeedback(e.target.value)}
                  placeholder="Add any notes about this healing decision..."
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => handleApprove(false)} disabled={approveHealing.isPending}>
              <XCircle className="mr-2 h-4 w-4" />
              Reject
            </Button>
            <Button onClick={() => handleApprove(true)} disabled={approveHealing.isPending}>
              {approveHealing.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <><CheckCircle className="mr-2 h-4 w-4" />Approve</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}