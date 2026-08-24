'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useRun } from '@/hooks/use-runs';
import { useToast } from '@/hooks/use-toast';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Play,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Image,
  Code,
  Terminal,
  Download,
  Image as ImageIcon,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  X,
} from 'lucide-react';
import { formatDate, formatDuration, getStatusColor, cn } from '@/lib/utils';
import { StepExecution, StepStatus, RunStatus } from '@/types';

export default function RunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params.id as string;
  const eventSourceRef = useRef<EventSource | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'console' | 'report' | 'healing'>('console');
  const { data: run, isLoading, refetch } = useRun(runId);
  const { toast } = useToast();

  useEffect(() => {
    if (!run) return;

    const es = new EventSource(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/runs/${runId}/events`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleSSEEvent(data);
      } catch (e) {
        console.error('Failed to parse SSE event', e);
      }
    };

    es.onerror = () => {
      console.error('SSE connection error');
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [runId, run]);

  const handleSSEEvent = (event: any) => {
    switch (event.type) {
      case 'run_started':
        refetch();
        break;
      case 'step_started':
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] START: ${event.data.action} - ${event.data.description || ''}`]);
        break;
      case 'step_completed':
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ✓ ${event.data.status.toUpperCase()} (${event.data.duration_ms}ms)`]);
        refetch();
        break;
      case 'step_failed':
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ✗ FAILED: ${event.data.error}`]);
        if (event.data.healing_candidate) {
          setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] 🔧 Healing candidate generated`]);
        }
        refetch();
        break;
      case 'healing_candidate':
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] 🔧 HEALING: ${event.data.candidate.reasoning}`]);
        refetch();
        break;
      case 'run_completed':
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] RUN ${event.data.status.toUpperCase()} (${event.data.duration_ms}ms)`]);
        refetch();
        break;
      case 'run_cancelled':
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] RUN CANCELLED`]);
        refetch();
        break;
      case 'log':
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] [${event.data.level.toUpperCase()}] ${event.data.message}`]);
        break;
    }
  };

  const toggleStep = (stepId: string) => {
    setExpandedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepId)) next.delete(stepId);
      else next.add(stepId);
      return next;
    });
  };

  const handleRetry = async () => {
    if (!run) return;
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/runs/${runId}/retry`, {
        method: 'POST',
      });
      if (response.ok) {
        toast({ title: 'Run retried', description: 'New execution queued' });
        router.refresh();
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to retry run', variant: 'destructive' });
    }
  };

  const handleCancel = async () => {
    if (!run) return;
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/runs/${runId}/cancel`, {
        method: 'POST',
      });
      if (response.ok) {
        toast({ title: 'Run cancelled' });
        refetch();
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to cancel run', variant: 'destructive' });
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

  const stepStatusIcons: Record<StepStatus, React.ReactNode> = {
    pending: <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />,
    running: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
    passed: <CheckCircle className="h-4 w-4 text-green-500" />,
    failed: <XCircle className="h-4 w-4 text-red-500" />,
    skipped: <AlertCircle className="h-4 w-4 text-gray-500" />,
    healing: <RotateCcw className="h-4 w-4 animate-spin text-purple-500" />,
    healed: <CheckCircle className="h-4 w-4 text-green-500" />,
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="h-64 bg-muted rounded" />
        </div>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="container mx-auto py-8 px-4 text-center">
        <h1 className="text-2xl font-bold">Run not found</h1>
        <Link href="/runs">
          <Button className="mt-4">Back to Runs</Button>
        </Link>
      </div>
    );
  }

  const sortedSteps = [...(run.step_executions || [])].sort((a, b) => a.order - b.order);

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link href="/runs" className="text-sm text-muted-foreground hover:underline">
            ← All Runs
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Run Details</h1>
            <p className="text-muted-foreground">Test Case: {run.test_case_id.slice(0, 8)}... • Environment: {run.environment_id.slice(0, 8)}...</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Badge className={cn('text-lg', statusColors[run.status] || 'bg-gray-100 text-gray-800')}>
            {run.status}
          </Badge>
          <div className="flex gap-2">
            {run.status === 'running' && (
              <Button variant="outline" onClick={handleCancel}>
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            )}
            {(run.status === 'failed' || run.status === 'cancelled') && (
              <Button onClick={handleRetry}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Retry
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card>
          <CardContent className="py-4 text-center">
            <div className="text-2xl font-bold">{run.passed_steps}</div>
            <div className="text-sm text-muted-foreground">Passed</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4 text-center">
            <div className="text-2xl font-bold text-red-500">{run.failed_steps}</div>
            <div className="text-sm text-muted-foreground">Failed</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4 text-center">
            <div className="text-2xl font-bold">{run.skipped_steps}</div>
            <div className="text-sm text-muted-foreground">Skipped</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4 text-center">
            <div className="text-2xl font-bold">{formatDuration(run.duration_ms || 0)}</div>
            <div className="text-sm text-muted-foreground">Duration</div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
        <TabsList>
          <TabsTrigger value="console">Console</TabsTrigger>
          <TabsTrigger value="report">Report</TabsTrigger>
          <TabsTrigger value="healing">Healing</TabsTrigger>
        </TabsList>

        <TabsContent value="console" className="mt-4">
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>Step Execution</CardTitle>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    {run.status === 'running' && (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Running...
                      </>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-[600px] overflow-y-auto">
                    {sortedSteps.map(step => {
                      const expanded = expandedSteps.has(step.id);
                      return (
                        <div key={step.id} className="border rounded-lg overflow-hidden">
                          <button
                            onClick={() => toggleStep(step.id)}
                            className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              {stepStatusIcons[step.status]}
                              <span className="font-mono text-sm text-muted-foreground">{step.order + 1}</span>
                              <Badge variant="secondary">{(step as any).action}</Badge>
                              <span className="flex-1 truncate">{((step as any).description || (step as any).action)}</span>
                              <Badge className={cn(getStatusColor(step.status))}>{step.status}</Badge>
                              {step.duration_ms && <span className="text-sm text-muted-foreground">{formatDuration(step.duration_ms)}</span>}
                            </div>
                            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </button>
                          {expanded && (
                            <div className="border-t p-3 bg-muted/30 space-y-3">
                              {step.error && (
                                <div className="text-sm text-red-500 bg-red-50 p-2 rounded">
                                  <strong>Error:</strong> {step.error}
                                </div>
                              )}
                              {step.healed_locator && (
                                <div className="text-sm text-green-500 bg-green-50 p-2 rounded">
                                  <strong>Healed Locator:</strong> {step.healed_locator}
                                </div>
                              )}
                              <div className="grid gap-2 md:grid-cols-2 text-sm">
                                {step.screenshot_path && (
                                  <Link href={step.screenshot_path} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-blue-500 hover:underline">
                                    <ImageIcon className="h-4 w-4" /> Screenshot
                                  </Link>
                                )}
                                {step.dom_snapshot_path && (
                                  <Link href={step.dom_snapshot_path} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-blue-500 hover:underline">
                                    <Code className="h-4 w-4" /> DOM Snapshot
                                  </Link>
                                )}
                                {step.trace_path && (
                                  <Link href={step.trace_path} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-blue-500 hover:underline">
                                    <Download className="h-4 w-4" /> Trace
                                  </Link>
                                )}
                              </div>
                              {step.console_logs.length > 0 && (
                                <details className="group">
                                  <summary className="cursor-pointer text-sm font-medium">Console Logs ({step.console_logs.length})</summary>
                                  <pre className="mt-2 p-2 bg-black text-green-300 text-xs overflow-x-auto rounded max-h-48 overflow-y-auto">
                                    {step.console_logs.join('\n')}
                                  </pre>
                                </details>
                              )}
                              {step.network_logs.length > 0 && (
                                <details className="group">
                                  <summary className="cursor-pointer text-sm font-medium">Network Logs ({step.network_logs.length})</summary>
                                  <pre className="mt-2 p-2 bg-black text-yellow-300 text-xs overflow-x-auto rounded max-h-48 overflow-y-auto">
                                    {JSON.stringify(step.network_logs.slice(0, 20), null, 2)}
                                  </pre>
                                </details>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>Live Logs</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px]">
                  <div className="font-mono text-xs space-y-1">
                    {logs.map((log, i) => (
                      <div key={i} className="text-muted-foreground">{log}</div>
                    ))}
                    {logs.length === 0 && <div className="text-muted-foreground">Waiting for events...</div>}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="report" className="mt-4">
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Run Summary</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-medium mb-2">Run Information</h4>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between"><dt className="text-muted-foreground">Run ID</dt><dd>{run.id}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Test Case</dt><dd>{run.test_case_id}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Environment</dt><dd>{run.environment_id}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Status</dt><dd><Badge className={statusColors[run.status] || 'bg-gray-100 text-gray-800'}>{run.status}</Badge></dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Started</dt><dd>{run.started_at ? formatDate(run.started_at) : 'N/A'}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Finished</dt><dd>{run.finished_at ? formatDate(run.finished_at) : 'N/A'}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Duration</dt><dd>{formatDuration(run.duration_ms || 0)}</dd></div>
                  </dl>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Step Summary</h4>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between"><dt className="text-muted-foreground">Total Steps</dt><dd>{run.total_steps}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Passed</dt><dd className="text-green-500">{run.passed_steps}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Failed</dt><dd className="text-red-500">{run.failed_steps}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Skipped</dt><dd className="text-gray-500">{run.skipped_steps}</dd></div>
                    <div className="flex justify-between"><dt className="text-muted-foreground">Pass Rate</dt><dd>{run.total_steps > 0 ? Math.round((run.passed_steps / run.total_steps) * 100) : 0}%</dd></div>
                  </dl>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Step Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 pr-4">#</th>
                        <th className="pb-2 pr-4">Action</th>
                        <th className="pb-2 pr-4">Status</th>
                        <th className="pb-2 pr-4">Duration</th>
                        <th className="pb-2 pr-4">Artifacts</th>
                        <th className="pb-2 pr-4">Error</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedSteps.map(step => (
                        <tr key={step.id} className="border-b">
                          <td className="py-2 pr-4 font-mono">{step.order + 1}</td>
                          <td className="py-2 pr-4">
                            <Badge variant="secondary">{(step as any).action}</Badge>
                            {((step as any).description) && <span className="ml-2 text-muted-foreground">{(step as any).description}</span>}
                          </td>
                          <td className="py-2 pr-4"><Badge className={getStatusColor(step.status)}>{step.status}</Badge></td>
                          <td className="py-2 pr-4">{step.duration_ms ? formatDuration(step.duration_ms) : '-'}</td>
                          <td className="py-2 pr-4">
                            <div className="flex gap-2">
                              {step.screenshot_path && <Link href={step.screenshot_path} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline"><ImageIcon className="h-4 w-4" /></Link>}
                              {step.dom_snapshot_path && <Link href={step.dom_snapshot_path} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline"><Code className="h-4 w-4" /></Link>}
                              {step.trace_path && <Link href={step.trace_path} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline"><Download className="h-4 w-4" /></Link>}
                            </div>
                          </td>
                          <td className="py-2 pr-4 text-red-500 max-w-xs truncate">{step.error || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="healing" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Healing Candidates</CardTitle>
            </CardHeader>
            <CardContent>
              {run.step_executions?.some(s => s.healing_candidate_id) ? (
                <div className="space-y-4">
                  {sortedSteps.filter(s => s.healing_candidate_id).map(step => (
                    <div key={step.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <Badge variant="secondary">{(step as any).action}</Badge>
                          <span className="ml-2 text-sm text-muted-foreground">Step {step.order + 1}</span>
                        </div>
                        <Badge variant="outline" className="text-purple-500 border-purple-500">Healing Candidate</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">Healing candidate available for this step. Review in the Healing Center.</p>
                      <Link href={`/healing?runId=${runId}`}>
                        <Button variant="outline" size="sm">Review Healing</Button>
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <RotateCcw className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-4 text-lg font-medium">No healing candidates</h3>
                  <p className="text-muted-foreground">Healing candidates appear when a step fails and the system suggests alternative locators</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}