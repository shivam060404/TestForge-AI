'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useDesignInsights, useVisualBaselines } from '@/hooks/use-design';
import { useProjects } from '@/hooks/use-projects';
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
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Image as ImageIcon,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  Eye,
  Download,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { formatDate, cn } from '@/lib/utils';
import type { VisualBaseline, VisualComparison, AccessibilityIssue, DesignInsight } from '@/types';
import Image from 'next/image';

export default function DesignInsightsPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get('projectId') || '';
  const runId = searchParams.get('runId') || '';
  const [selectedBaseline, setSelectedBaseline] = useState<VisualBaseline | null>(null);
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [selectedComparison, setSelectedComparison] = useState<VisualComparison | null>(null);
  const [imageIndex, setImageIndex] = useState(0);

  const { data: projectsData } = useProjects({ page_size: 100 });
  const { data: insights, isLoading: insightsLoading } = useDesignInsights(runId);
  const { data: baselinesData, isLoading: baselinesLoading } = useVisualBaselines(projectId);

  const impactColors: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    serious: 'bg-orange-100 text-orange-800',
    moderate: 'bg-yellow-100 text-yellow-800',
    minor: 'bg-gray-100 text-gray-800',
  };

  const impactIcons: Record<string, React.ReactNode> = {
    critical: <XCircle className="h-4 w-4" />,
    serious: <AlertCircle className="h-4 w-4" />,
    moderate: <AlertCircle className="h-4 w-4" />,
    minor: <AlertCircle className="h-4 w-4" />,
  };

  if ((insightsLoading || baselinesLoading) && !insights && !baselinesData) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="h-64 bg-muted rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Design Intelligence</h1>
          <p className="text-muted-foreground">Visual regression and accessibility insights</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={projectId} onValueChange={(v) => window.location.search = `?projectId=${v}${runId ? `&runId=${runId}` : ''}`}>
            <SelectTrigger className="w-[200px]"><SelectValue placeholder="Select project" /></SelectTrigger>
            <SelectContent>
              {projectsData?.items.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </div>

      {runId && insights && (
        <div className="space-y-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Run Design Insights</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {insights.visual_comparisons.length > 0 && (
                <div>
                  <h3 className="font-medium mb-4">Visual Comparisons ({insights.visual_comparisons.length})</h3>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {insights.visual_comparisons.map(comp => (
                      <Card key={comp.baseline_id}>
                        <CardContent className="pt-4">
                          <div className="flex items-center justify-between mb-2">
                            <Badge className={comp.match ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                              {comp.match ? 'Match' : 'Mismatch'}
                            </Badge>
                            <span className="text-sm text-muted-foreground">{comp.difference_percent.toFixed(2)}% diff</span>
                          </div>
                          <div className="text-sm">
                            <p className="text-muted-foreground">Baseline: {comp.baseline_id.slice(0, 8)}...</p>
                            <p className="text-muted-foreground">Step: {comp.step_execution_id.slice(0, 8)}...</p>
                          </div>
                          {comp.diff_image_path && (
                            <Button variant="outline" size="sm" className="mt-2" onClick={() => {
                              setSelectedComparison(comp);
                              setComparisonModalOpen(true);
                            }}>
                              <Eye className="mr-2 h-4 w-4" />
                              View Diff
                            </Button>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {insights.accessibility_issues.length > 0 && (
                <div>
                  <h3 className="font-medium mb-4">Accessibility Issues ({insights.accessibility_issues.length})</h3>
                  <div className="space-y-3">
                    {insights.accessibility_issues.map(issue => (
                      <Card key={issue.id} className="border-l-4" style={{ borderLeftColor: issue.impact === 'critical' ? 'red' : issue.impact === 'serious' ? 'orange' : issue.impact === 'moderate' ? 'yellow' : 'gray' }}>
                        <CardContent className="pt-4">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                {impactIcons[issue.impact]}
                                <Badge className={cn(impactColors[issue.impact])}>{issue.impact}</Badge>
                                <span className="font-medium">{issue.description}</span>
                              </div>
                              <p className="text-sm text-muted-foreground">Rule: {issue.rule_id}</p>
                              {issue.selector && <p className="text-sm text-muted-foreground mt-1 font-mono">{issue.selector}</p>}
                              {issue.help && <p className="text-sm text-blue-500 mt-1">{issue.help}</p>}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {insights.visual_comparisons.length === 0 && insights.accessibility_issues.length === 0 && (
                <div className="text-center py-8">
                  <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
                  <h3 className="mt-4 text-lg font-medium">No design issues detected</h3>
                  <p className="text-muted-foreground">All visual comparisons passed and no accessibility issues found</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Visual Baselines ({(baselinesData ?? []).length})</CardTitle>
          <Button asChild>
            <Link href="/design/baselines/new">
              <ImageIcon className="mr-2 h-4 w-4" />
              Create Baseline
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {(baselinesData ?? []).length === 0 ? (
            <div className="text-center py-12">
              <ImageIcon className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-medium">No visual baselines</h3>
              <p className="text-muted-foreground">Create baselines from successful test runs to enable visual regression testing</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {(baselinesData ?? []).map((baseline) => (
                <Card key={baseline.id}>
                  <CardContent className="pt-4">
                    <div className="aspect-video bg-muted rounded mb-3 relative overflow-hidden">
                      <Image
                        src={baseline.image_path}
                        alt={baseline.name}
                        fill
                        className="object-cover"
                        sizes="300px"
                      />
                    </div>
                    <h4 className="font-medium truncate">{baseline.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      {baseline.viewport.width}×{baseline.viewport.height} • {formatDate(baseline.created_at)}
                    </p>
                    <div className="flex gap-2 mt-3">
                      <Button variant="outline" size="sm" className="flex-1" onClick={() => {
                        setSelectedBaseline(baseline);
                        setComparisonModalOpen(true);
                      }}>
                        <Eye className="mr-2 h-4 w-4" />
                        Compare
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={comparisonModalOpen} onOpenChange={setComparisonModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>Visual Comparison</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            {selectedComparison && selectedComparison.diff_image_path && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Badge className={selectedComparison.match ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                    {selectedComparison.match ? 'Match' : 'Mismatch'}
                  </Badge>
                  <span className="text-sm text-muted-foreground">{selectedComparison.difference_percent.toFixed(2)}% difference</span>
                </div>
                <div className="relative aspect-video bg-muted rounded overflow-hidden">
                  <Image
                    src={selectedComparison.diff_image_path}
                    alt="Visual diff"
                    fill
                    className="object-contain"
                  />
                </div>
              </div>
            )}
            {selectedBaseline && !selectedComparison && (
              <div className="relative aspect-video bg-muted rounded overflow-hidden">
                <Image
                  src={selectedBaseline.image_path}
                  alt={selectedBaseline.name}
                  fill
                  className="object-contain"
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setComparisonModalOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}