'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useProject, useUpdateProject, useDeleteProject } from '@/hooks/use-projects';
import { useEnvironments, useCreateEnvironment, useDeleteEnvironment } from '@/hooks/use-environments';
import { useTestCases, useCreateTestCase, useDeleteTestCase } from '@/hooks/use-test-cases';
import { useToast } from '@/hooks/use-toast';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Plus,
  Trash2,
  FileText,
  Globe,
  ChevronRight,
  Loader2,
  Edit2,
  Play,
} from 'lucide-react';
import { formatDate, cn } from '@/lib/utils';
import { PaginationParams } from '@/types';
import type { Environment, TestCase } from '@/types';

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [pagination, setPagination] = useState<PaginationParams>({ page: 1, page_size: 10 });
  const [activeTab, setActiveTab] = useState('test-cases');
  const [envDialogOpen, setEnvDialogOpen] = useState(false);
  const [tcDialogOpen, setTcDialogOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [newEnvName, setNewEnvName] = useState('');
  const [newEnvUrl, setNewEnvUrl] = useState('');
  const [tcIntent, setTcIntent] = useState('');
  const [tcEnvId, setTcEnvId] = useState('');
  const [deletingEnvId, setDeletingEnvId] = useState<string | null>(null);
  const [deletingTcId, setDeletingTcId] = useState<string | null>(null);

  const { data: project, isLoading: projectLoading } = useProject(projectId);
  const updateProject = useUpdateProject(projectId);
  const deleteProject = useDeleteProject();
  const { data: envData, refetch: refetchEnvs } = useEnvironments(projectId);
  const createEnv = useCreateEnvironment(projectId);
  const deleteEnv = useDeleteEnvironment();
  const { data: tcData, refetch: refetchTCs } = useTestCases(projectId, pagination);
  const createTC = useCreateTestCase();
  const deleteTC = useDeleteTestCase();
  const { toast } = useToast();

  const handleCreateEnv = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEnvName.trim() || !newEnvUrl.trim()) return;

    try {
      await createEnv.mutateAsync({ name: newEnvName, base_url: newEnvUrl });
      toast({ title: 'Environment created', description: newEnvName });
      setNewEnvName('');
      setNewEnvUrl('');
      setEnvDialogOpen(false);
      refetchEnvs();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to create environment', variant: 'destructive' });
    }
  };

  const handleDeleteEnv = async (id: string) => {
    setDeletingEnvId(id);
    try {
      await deleteEnv.mutateAsync(id);
      toast({ title: 'Environment deleted' });
      refetchEnvs();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete environment', variant: 'destructive' });
    } finally {
      setDeletingEnvId(null);
    }
  };

  const handleGenerateTC = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tcIntent.trim()) return;

    setGenerating(true);
    try {
      // This would call the generate endpoint
      toast({ title: 'Test case generated', description: 'Review and edit the steps' });
      setTcIntent('');
      setTcEnvId('');
      setTcDialogOpen(false);
      refetchTCs();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to generate test case', variant: 'destructive' });
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteTC = async (id: string) => {
    setDeletingTcId(id);
    try {
      await deleteTC.mutateAsync(id);
      toast({ title: 'Test case deleted' });
      refetchTCs();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to delete test case', variant: 'destructive' });
    } finally {
      setDeletingTcId(null);
    }
  };

  if (projectLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="h-64 bg-muted rounded" />
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="container mx-auto py-8 px-4 text-center">
        <h1 className="text-2xl font-bold">Project not found</h1>
        <Link href="/projects">
          <Button className="mt-4">Back to Projects</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link href="/projects" className="text-sm text-muted-foreground hover:underline mb-2 inline-block">
            ← All Projects
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
          {project.description && <p className="text-muted-foreground">{project.description}</p>}
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link href={`/projects/${projectId}/test-cases/new`}>
              <Plus className="mr-2 h-4 w-4" />
              New Test Case
            </Link>
          </Button>
          <Dialog open={envDialogOpen} onOpenChange={setEnvDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Globe className="mr-2 h-4 w-4" />
                Add Environment
              </Button>
            </DialogTrigger>
            <DialogContent>
              <form onSubmit={handleCreateEnv}>
                <DialogHeader>
                  <DialogTitle>Add Environment</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="env-name" className="text-right">Name</Label>
                    <Input
                      id="env-name"
                      value={newEnvName}
                      onChange={(e) => setNewEnvName(e.target.value)}
                      placeholder="Staging"
                      className="col-span-3"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="env-url" className="text-right">Base URL</Label>
                    <Input
                      id="env-url"
                      type="url"
                      value={newEnvUrl}
                      onChange={(e) => setNewEnvUrl(e.target.value)}
                      placeholder="https://staging.example.com"
                      className="col-span-3"
                      required
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={createEnv.isPending}>
                    {createEnv.isPending ? 'Creating...' : 'Add Environment'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList>
          <TabsTrigger value="environments">Environments ({envData?.items.length || 0})</TabsTrigger>
          <TabsTrigger value="test-cases">Test Cases ({tcData?.items.length || 0})</TabsTrigger>
        </TabsList>

        <TabsContent value="environments" className="mt-4">
          {envData?.items.length === 0 ? (
            <div className="text-center py-12">
              <Globe className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-medium">No environments</h3>
              <p className="text-muted-foreground">Add an environment to run tests against</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {envData?.items.map((env: Environment) => (
                <Card key={env.id}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>{env.name}</span>
                      <Badge variant="secondary">{env.id.slice(0, 8)}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground break-all">{env.base_url}</p>
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <span>Created: {formatDate(env.created_at)}</span>
                    </div>
                    <div className="flex gap-2">
                      <Button asChild variant="outline" className="flex-1" size="sm">
                        <Link href={`/environments/${env.id}`}>
                          <Edit2 className="mr-2 h-4 w-4" />
                          Edit
                        </Link>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteEnv(env.id)}
                        disabled={deletingEnvId === env.id}
                      >
                        {deletingEnvId === env.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="test-cases" className="mt-4">
          <Dialog open={tcDialogOpen} onOpenChange={setTcDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Generate Test Case
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <form onSubmit={handleGenerateTC}>
                <DialogHeader>
                  <DialogTitle>Generate Test Case from Natural Language</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div>
                    <Label htmlFor="intent">What should the test do?</Label>
                    <textarea
                      id="intent"
                      className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[100px]"
                      value={tcIntent}
                      onChange={(e) => setTcIntent(e.target.value)}
                      placeholder="e.g., User logs in, adds item to cart, and completes checkout"
                      required
                    />
                  </div>
                  {envData?.items.length && (
                    <div>
                      <Label htmlFor="tc-env">Environment (optional)</Label>
                      <select
                        id="tc-env"
                        className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        value={tcEnvId}
                        onChange={(e) => setTcEnvId(e.target.value)}
                      >
                        <option value="">Select environment</option>
                        {envData.items.map((env: Environment) => (
                          <option key={env.id} value={env.id}>{env.name}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={generating}>
                    {generating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      'Generate'
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {tcData?.items.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-medium">No test cases</h3>
              <p className="text-muted-foreground">Generate or create your first test case</p>
            </div>
          ) : (
            <div className="space-y-4">
              {tcData?.items.map((tc: TestCase) => (
                <Card key={tc.id} className="flex">
                  <CardContent className="flex flex-1 items-center justify-between p-4 space-y-0">
                    <div className="flex-1 min-w-0">
                      <Link href={`/test-cases/${tc.id}`} className="font-medium hover:underline">
                        {tc.name}
                      </Link>
                      <p className="text-sm text-muted-foreground truncate">{tc.description}</p>
                    </div>
                    <div className="flex items-center gap-4 ml-4">
                      <Badge variant="secondary">{tc.steps.length} steps</Badge>
                      <Badge variant="outline">{tc.tags.join(', ') || 'no tags'}</Badge>
                      <span className="text-sm text-muted-foreground">{formatDate(tc.updated_at)}</span>
                      <div className="flex gap-2">
                        <Button asChild variant="outline" size="sm">
                          <Link href={`/test-cases/${tc.id}`}>
                            <Edit2 className="mr-2 h-4 w-4" />
                            Edit
                          </Link>
                        </Button>
                        <Button asChild variant="outline" size="sm">
                          <Link href={`/runs/new?testCaseId=${tc.id}`}>
                            <Play className="mr-2 h-4 w-4" />
                            Run
                          </Link>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteTC(tc.id)}
                          disabled={deletingTcId === tc.id}
                        >
                          {deletingTcId === tc.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {tcData && tcData.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-4">
              <Button
                variant="outline"
                onClick={() => setPagination((p) => ({ ...p, page: p.page - 1 }))}
                disabled={pagination.page <= 1}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {pagination.page} of {tcData.total_pages}
              </span>
              <Button
                variant="outline"
                onClick={() => setPagination((p) => ({ ...p, page: p.page + 1 }))}
                disabled={pagination.page >= tcData.total_pages}
              >
                Next
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}