'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useRuns, useCreateRun, useCancelRun, useRetryRun } from '@/hooks/use-runs';
import { useProjects } from '@/hooks/use-projects';
import { useTestCases } from '@/hooks/use-test-cases';
import { useToast } from '@/hooks/use-toast';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Play,
  Loader2,
  RotateCcw,
  X,
  ChevronRight,
  Filter,
} from 'lucide-react';
import { formatDate, formatDuration, getStatusColor } from '@/lib/utils';
import { PaginationParams, RunStatus } from '@/types';

export default function RunsPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get('projectId') || '';
  const [pagination, setPagination] = useState<PaginationParams>({ page: 1, page_size: 20 });
  const [statusFilter, setStatusFilter] = useState<RunStatus | ''>('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTestCase, setSelectedTestCase] = useState('');
  const [selectedEnvironment, setSelectedEnvironment] = useState('');

  const { data: runsData, isLoading, refetch } = useRuns(projectId || undefined, { ...pagination, status: statusFilter });
  const createRun = useCreateRun();
  const cancelRun = useCancelRun();
  const retryRun = useRetryRun();
  const { data: projectsData } = useProjects({ page_size: 100 });
  const { data: testCasesData } = useTestCases(projectId || '', { page_size: 100 });
  const { toast } = useToast();

  const handleCreateRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTestCase || !selectedEnvironment) return;

    try {
      await createRun.mutateAsync({
        test_case_id: selectedTestCase,
        environment_id: selectedEnvironment,
      });
      toast({ title: 'Run started', description: 'Test execution queued' });
      setDialogOpen(false);
      setSelectedTestCase('');
      setSelectedEnvironment('');
      refetch();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to start run', variant: 'destructive' });
    }
  };

  const handleCancel = async (runId: string) => {
    try {
      await cancelRun.mutateAsync(runId);
      toast({ title: 'Run cancelled' });
      refetch();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to cancel run', variant: 'destructive' });
    }
  };

  const handleRetry = async (runId: string) => {
    try {
      await retryRun.mutateAsync(runId);
      toast({ title: 'Run retried', description: 'New execution queued' });
      refetch();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to retry run', variant: 'destructive' });
    }
  };

  const statusColors: Record<RunStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    passed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
    healing: 'bg-purple-100 text-purple-800',
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Test Runs</h1>
          <p className="text-muted-foreground">Monitor and manage test executions</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Play className="mr-2 h-4 w-4" />
              New Run
            </Button>
          </DialogTrigger>
          <DialogContent>
            <form onSubmit={handleCreateRun}>
              <DialogHeader>
                <DialogTitle>Start New Test Run</DialogTitle>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Project</label>
                  <Select value={projectId} onValueChange={(v) => { setProjectId(v); setSelectedTestCase(''); setSelectedEnvironment(''); }}>
                    <SelectTrigger><SelectValue placeholder="Select project" /></SelectTrigger>
                    <SelectContent>
                      {projectsData?.items.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Test Case</label>
                  <Select value={selectedTestCase} onValueChange={setSelectedTestCase} disabled={!projectId}>
                    <SelectTrigger><SelectValue placeholder="Select test case" /></SelectTrigger>
                    <SelectContent>
                      {testCasesData?.items.map(tc => <SelectItem key={tc.id} value={tc.id}>{tc.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Environment</label>
                  <Select value={selectedEnvironment} onValueChange={setSelectedEnvironment} disabled={!projectId}>
                    <SelectTrigger><SelectValue placeholder="Select environment" /></SelectTrigger>
                    <SelectContent>
                      {/* Environments would be fetched based on project */}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={createRun.isPending || !selectedTestCase || !selectedEnvironment}>
                  {createRun.isPending ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Starting...< / > : 'Start Run'}
                </Button>
              </DialogFooter            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]"><SelectValue placeholder="All statuses" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="">All statuses</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="passed">Passed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
              <SelectItem value="healing">Healing</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map(i => (
            <Card key={i} className="animate-pulse">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="h-4 bg-muted rounded w-1/4" />
                  <div className="h-6 bg-muted rounded w-24" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : runsData?.items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Play className="mx-auto h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-medium">No test runs</h3>
            <p className="text-muted-foreground">Start a new test run to see results here</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-3">
            {runsData?.items.map(run => (
              <Card key={run.id}>
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <Link href={`/runs/${run.id}`} className="font-medium hover:underline">
                          {run.test_case_id.slice(0, 8)}...
                        </Link>
                        <Badge className={statusColors[run.status] || 'bg-gray-100 text-gray-800'}>
                          {run.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        Project: {run.project_id.slice(0, 8)}... • {run.total_steps} steps • {formatDuration(run.duration_ms || 0)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <span className="text-sm text-muted-foreground">{formatDate(run.created_at)}</span>
                      {run.status === 'running' && (
                        <Button variant="outline" size="sm" onClick={() => handleCancel(run.id)}>
                          <X className="mr-2 h-4 w-4" />
                          Cancel
                        </Button>
                      )}
                      {(run.status === 'failed' || run.status === 'cancelled') && (
                        <Button variant="outline" size="sm" onClick={() => handleRetry(run.id)}>
                          <RotateCcw className="mr-2 h-4 w-4" />
                          Retry
                        </Button>
                      )}
                      <Link href={`/runs/${run.id}`}>
                        <Button variant="ghost" size="icon">
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                  {run.failed_steps > 0 && (
                    <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
                      <span className={cn('font-medium', getStatusColor('passed'))}>Passed: {run.passed_steps}</span>
                      <span className={cn('font-medium', getStatusColor('failed'))}>Failed: {run.failed_steps}</span>
                      {run.skipped_steps > 0 && <span className={cn('font-medium', getStatusColor('skipped'))}>Skipped: {run.skipped_steps}</span>}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {runsData && runsData.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <Button variant="outline" onClick={() => setPagination(p => ({ ...p, page: p.page - 1 }))} disabled={pagination.page <= 1}>
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">Page {pagination.page} of {runsData.total_pages}</span>
              <Button variant="outline" onClick={() => setPagination(p => ({ ...p, page: p.page + 1 }))} disabled={pagination.page >= runsData.total_pages}>
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}