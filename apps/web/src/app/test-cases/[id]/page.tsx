'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useTestCase, useUpdateTestCase } from '@/hooks/use-test-cases';
import { useProjects } from '@/hooks/use-projects';
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
import { Textarea } from '@/components/ui/textarea';
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
  Plus,
  Trash2,
  GripVertical,
  ChevronUp,
  ChevronDown,
  Save,
  Loader2,
  Play,
  ArrowLeft,
} from 'lucide-react';
import { formatDate, cn } from '@/lib/utils';
import type { TestStep, TestCase, CreateTestStepRequest, UpdateTestCaseRequest } from '@/types';
import { v4 as uuidv4 } from 'uuid';

const ACTIONS = [
  'goto', 'click', 'fill', 'select', 'hover', 'wait', 'assert', 'screenshot', 'scroll', 'press', 'check', 'uncheck'
] as const;

const LOCATOR_STRATEGIES = [
  'css', 'xpath', 'text', 'role', 'testId', 'id', 'name', 'placeholder', 'label'
] as const;

const ASSERTION_TYPES = [
  'visible', 'hidden', 'enabled', 'disabled', 'text', 'value', 'count', 'url', 'title'
] as const;

const OPERATORS = ['equals', 'contains', 'matches', 'greaterThan', 'lessThan'] as const;

export default function TestCaseEditorPage() {
  const params = useParams();
  const router = useRouter();
  const testCaseId = params.id as string;
  const [steps, setSteps] = useState<TestStep[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [showAddStep, setShowAddStep] = useState(false);
  const [newStep, setNewStep] = useState<Partial<TestStep>>({ action: 'click', order: 0 });

  const { data: testCase, isLoading, refetch } = useTestCase(testCaseId);
  const updateTestCase = useUpdateTestCase(testCaseId);
  const { data: projectsData } = useProjects({ page_size: 100 });
  const { toast } = useToast();

  // Initialize from test case data
  if (testCase && steps.length === 0) {
    setName(testCase.name);
    setDescription(testCase.description || '');
    setTags(testCase.tags.join(', '));
    setSteps(testCase.steps.map((s, i) => ({ ...s, order: i })));
  }

  const handleSave = async () => {
    if (!name.trim()) {
      toast({ title: 'Error', description: 'Test case name is required', variant: 'destructive' });
      return;
    }

    setSaving(true);
    try {
      const updateData: UpdateTestCaseRequest = {
        name,
        description: description || undefined,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
        steps: steps.map((s, i) => ({
          order: i,
          action: s.action,
          target: s.target,
          locator: s.locator,
          locator_strategy: s.locator_strategy,
          value: s.value,
          options: s.options,
          assertion: s.assertion,
          description: s.description,
          continue_on_failure: s.continue_on_failure,
        })),
      };
      await updateTestCase.mutateAsync(updateData);
      toast({ title: 'Saved', description: 'Test case updated successfully' });
      router.back();
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to save test case', variant: 'destructive' });
    } finally {
      setSaving(false);
    }
  };

  const addStep = () => {
    const step: TestStep = {
      id: uuidv4(),
      order: steps.length,
      action: newStep.action as TestStep['action'],
      target: newStep.target,
      locator: newStep.locator,
      locator_strategy: newStep.locator_strategy,
      value: newStep.value,
      options: newStep.options || {},
      assertion: newStep.assertion,
      description: newStep.description,
      continue_on_failure: newStep.continue_on_failure || false,
    };
    setSteps([...steps, step]);
    setNewStep({ action: 'click', order: 0 });
    setShowAddStep(false);
  };

  const removeStep = (id: string) => {
    setSteps(steps.filter(s => s.id !== id).map((s, i) => ({ ...s, order: i })));
  };

  const moveStep = (id: string, direction: 'up' | 'down') => {
    const index = steps.findIndex(s => s.id === id);
    if (direction === 'up' && index > 0) {
      const newSteps = [...steps];
      [newSteps[index], newSteps[index - 1]] = [newSteps[index - 1], newSteps[index]];
      setSteps(newSteps.map((s, i) => ({ ...s, order: i })));
    } else if (direction === 'down' && index < steps.length - 1) {
      const newSteps = [...steps];
      [newSteps[index], newSteps[index + 1]] = [newSteps[index + 1], newSteps[index]];
      setSteps(newSteps.map((s, i) => ({ ...s, order: i })));
    }
  };

  const updateStep = (id: string, field: keyof TestStep, value: any) => {
    setSteps(steps.map(s => s.id === id ? { ...s, [field]: value } : s));
  };

  const handleDragStart = (e: React.DragEvent, id: string) => {
    setDraggingId(id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!draggingId || draggingId === targetId) return;

    const dragIndex = steps.findIndex(s => s.id === draggingId);
    const targetIndex = steps.findIndex(s => s.id === targetId);
    const newSteps = [...steps];
    const [dragged] = newSteps.splice(dragIndex, 1);
    newSteps.splice(targetIndex, 0, dragged);
    setSteps(newSteps.map((s, i) => ({ ...s, order: i })));
    setDraggingId(null);
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

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Test Case Editor</h1>
            <p className="text-muted-foreground text-sm">Define steps for your automated test</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save
              </>
            )}
          </Button>
        </div>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Test Case Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Test case name"
              />
            </div>
            <div>
              <Label htmlFor="tags">Tags (comma separated)</Label>
              <Input
                id="tags"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="smoke, regression, critical"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this test case covers"
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Test Steps ({steps.length})</CardTitle>
          <Button variant="outline" size="sm" onClick={() => setShowAddStep(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Step
          </Button>
        </CardHeader>
        <CardContent>
          {showAddStep && (
            <div className="mb-4 p-4 border rounded-lg bg-muted/50 space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label>Action</Label>
                  <Select value={newStep.action} onValueChange={(v) => setNewStep({ ...newStep, action: v as any })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {ACTIONS.map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Target URL (for goto)</Label>
                  <Input value={newStep.target || ''} onChange={(e) => setNewStep({ ...newStep, target: e.target.value })} placeholder="/login" />
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <Label>Locator</Label>
                  <Input value={newStep.locator || ''} onChange={(e) => setNewStep({ ...newStep, locator: e.target.value })} placeholder="[data-testid=submit]" />
                </div>
                <div>
                  <Label>Strategy</Label>
                  <Select value={newStep.locator_strategy || 'css'} onValueChange={(v) => setNewStep({ ...newStep, locator_strategy: v as any })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {LOCATOR_STRATEGIES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Value (for fill/select/press)</Label>
                  <Input value={newStep.value || ''} onChange={(e) => setNewStep({ ...newStep, value: e.target.value })} placeholder="test@example.com" />
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <Label>Assertion Type</Label>
                  <Select value={newStep.assertion?.type || 'visible'} onValueChange={(v) => setNewStep({ ...newStep, assertion: { ...newStep.assertion, type: v as any } })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {ASSERTION_TYPES.map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Expected Value</Label>
                  <Input value={newStep.assertion?.expected || ''} onChange={(e) => setNewStep({ ...newStep, assertion: { ...newStep.assertion, expected: e.target.value } })} placeholder="true" />
                </div>
                <div>
                  <Label>Operator</Label>
                  <Select value={newStep.assertion?.operator || 'equals'} onValueChange={(v) => setNewStep({ ...newStep, assertion: { ...newStep.assertion, operator: v as any } })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {OPERATORS.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label>Description</Label>
                <Input value={newStep.description || ''} onChange={(e) => setNewStep({ ...newStep, description: e.target.value })} placeholder="Click the submit button" />
              </div>
              <div className="flex gap-2">
                <Button onClick={addStep}>Add Step</Button>
                <Button variant="outline" onClick={() => setShowAddStep(false)}>Cancel</Button>
              </div>
            </div>
          )}

          {steps.length === 0 && !showAddStep && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No steps yet. Click "Add Step" to start building your test.</p>
            </div>
          )}

          <div className="space-y-2">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className="border rounded-lg p-4 bg-background"
                draggable
                onDragStart={(e) => handleDragStart(e, step.id)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, step.id)}
                style={{ opacity: draggingId === step.id ? 0.5 : 1 }}
              >
                <div className="flex items-start gap-4">
                  <div className="flex flex-col items-center gap-1 text-muted-foreground">
                    <GripVertical className="h-5 w-5 cursor-grab" />
                    <span className="text-xs font-mono">{index + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0 space-y-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{step.action}</Badge>
                      {step.description && <span className="text-sm text-muted-foreground">{step.description}</span>}
                    </div>
                    <div className="grid gap-3 md:grid-cols-4">
                      {step.action === 'goto' && (
                        <div className="md:col-span-2">
                          <Label className="text-xs">Target</Label>
                          <Input
                            size="sm"
                            value={step.target || ''}
                            onChange={(e) => updateStep(step.id, 'target', e.target.value)}
                            placeholder="/path"
                          />
                        </div>
                      )}
                      {(step.action !== 'goto' && step.action !== 'wait' && step.action !== 'screenshot' && step.action !== 'scroll') && (
                        <>
                          <div>
                            <Label className="text-xs">Locator</Label>
                            <Input
                              size="sm"
                              value={step.locator || ''}
                              onChange={(e) => updateStep(step.id, 'locator', e.target.value)}
                              placeholder="[data-testid=button]"
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Strategy</Label>
                            <Select value={step.locator_strategy || 'css'} onValueChange={(v) => updateStep(step.id, 'locator_strategy', v)}>
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {LOCATOR_STRATEGIES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                        </>
                      )}
                      {(step.action === 'fill' || step.action === 'select' || step.action === 'press') && (
                        <div>
                          <Label className="text-xs">Value</Label>
                          <Input
                            size="sm"
                            value={step.value || ''}
                            onChange={(e) => updateStep(step.id, 'value', e.target.value)}
                            placeholder="value"
                          />
                        </div>
                      )}
                      {step.assertion && (
                        <div className="md:col-span-4 border-t pt-3">
                          <Label className="text-xs">Assertion</Label>
                          <div className="flex gap-2 flex-wrap">
                            <Select value={step.assertion.type} onValueChange={(v) => updateStep(step.id, 'assertion', { ...step.assertion!, type: v })}>
                              <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {ASSERTION_TYPES.map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                              </SelectContent>
                            </Select>
                            <Select value={step.assertion.operator || 'equals'} onValueChange={(v) => updateStep(step.id, 'assertion', { ...step.assertion!, operator: v })}>
                              <SelectTrigger className="w-[130px]"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {OPERATORS.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                              </SelectContent>
                            </Select>
                            <Input
                              size="sm"
                              className="flex-1 min-w-[150px]"
                              value={step.assertion.expected || ''}
                              onChange={(e) => updateStep(step.id, 'assertion', { ...step.assertion!, expected: e.target.value })}
                              placeholder="expected value"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Label className="text-xs flex items-center gap-1">
                        <input
                          type="checkbox"
                          checked={step.continue_on_failure}
                          onChange={(e) => updateStep(step.id, 'continue_on_failure', e.target.checked)}
                          className="rounded"
                        />
                        Continue on failure
                      </Label>
                    </div>
                  </div>
                  <div className="flex flex-col items-center gap-1">
                    <Button variant="ghost" size="icon" onClick={() => moveStep(step.id, 'up')} disabled={index === 0}>
                      <ChevronUp className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => moveStep(step.id, 'down')} disabled={index === steps.length - 1}>
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => removeStep(step.id)} className="text-destructive hover:text-destructive">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}