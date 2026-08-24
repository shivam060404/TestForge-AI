'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useLocatorMemory, useEpisodeMemory, useFailurePatterns, useSearchMemory } from '@/hooks/use-memory';
import { useProjects } from '@/hooks/use-projects';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
} from '@/components/ui/dialog';
import {
  Input,
} from '@/components/ui/input';
import {
  Search,
  Database,
  FileText,
  AlertTriangle,
  Image as ImageIcon,
  Loader2,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
} from 'lucide-react';
import { formatDate, cn } from '@/lib/utils';
import type { LocatorMemory, EpisodeMemory, FailurePattern, MemoryType } from '@/types';

export default function MemoryBrowserPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get('projectId') || '';
  const [activeTab, setActiveTab] = useState<MemoryType>('locator');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<{
    locators: LocatorMemory[];
    episodes: EpisodeMemory[];
    failure_patterns: FailurePattern[];
  } | null>(null);
  const [searching, setSearching] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const { data: projectsData } = useProjects({ page_size: 100 });
  const { data: locators, isLoading: locatorsLoading } = useLocatorMemory(projectId);
  const { data: episodes, isLoading: episodesLoading } = useEpisodeMemory(projectId);
  const { data: patterns, isLoading: patternsLoading } = useFailurePatterns(projectId);
  const searchMemory = useSearchMemory(projectId);

  const handleSearch = async () => {
    if (!searchQuery.trim() || !projectId) return;
    setSearching(true);
    try {
      const results = await searchMemory.mutateAsync({
        query: searchQuery,
        types: ['locator', 'episode', 'failure_pattern'],
        limit: 50,
      });
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed', error);
    } finally {
      setSearching(false);
    }
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  const toggleExpand = (id: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const isLoading = locatorsLoading || episodesLoading || patternsLoading;

  if (isLoading && !locators && !episodes && !patterns) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="h-64 bg-muted rounded" />
        </div>
      </div>
    );
  }

  const renderLocatorRow = (locator: LocatorMemory) => {
    const expanded = expandedItems.has(locator.id);
    const successRate = locator.success_count + locator.failure_count > 0
      ? Math.round((locator.success_count / (locator.success_count + locator.failure_count)) * 100)
      : 0;

    return (
      <div key={locator.id} className="border rounded-lg overflow-hidden">
        <button
          onClick={() => toggleExpand(locator.id)}
          className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <Database className="h-4 w-4 text-muted-foreground" />
            <div className="flex-1 min-w-0">
              <p className="font-mono text-sm truncate">{locator.selector}</p>
              <p className="text-xs text-muted-foreground truncate">{locator.page_url}</p>
            </div>
            <Badge variant="secondary">{locator.strategy}</Badge>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className={cn(successRate >= 80 ? 'text-green-500' : successRate >= 50 ? 'text-yellow-500' : 'text-red-500')}>
                {successRate}% success
              </span>
              <span>{locator.success_count + locator.failure_count} uses</span>
            </div>
          </div>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {expanded && (
          <div className="border-t p-3 bg-muted/30 grid gap-2 md:grid-cols-2 text-sm">
            <div><span className="text-muted-foreground">Element Role:</span> <span className="ml-2 font-mono">{locator.element_role || 'N/A'}</span></div>
            <div><span className="text-muted-foreground">Element Text:</span> <span className="ml-2 font-mono truncate">{locator.element_text || 'N/A'}</span></div>
            <div className="md:col-span-2 flex items-center gap-2">
              <Button variant="ghost" size="icon" onClick={() => copyToClipboard(locator.selector, locator.id)}>
                {copiedId === locator.id ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
              <span className="text-xs text-muted-foreground">Last used: {formatDate(locator.last_used_at)}</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderEpisodeRow = (episode: EpisodeMemory) => {
    const expanded = expandedItems.has(episode.id);
    const outcomeColors: Record<string, string> = {
      success: 'bg-green-100 text-green-800',
      failure: 'bg-red-100 text-red-800',
      partial: 'bg-yellow-100 text-yellow-800',
    };

    return (
      <div key={episode.id} className="border rounded-lg overflow-hidden">
        <button
          onClick={() => toggleExpand(episode.id)}
          className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{episode.intent}</p>
              <p className="text-xs text-muted-foreground">{episode.steps.length} steps</p>
            </div>
            <Badge className={cn(outcomeColors[episode.outcome])}>{episode.outcome}</Badge>
            <span className="text-xs text-muted-foreground">{formatDate(episode.created_at)}</span>
          </div>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {expanded && (
          <div className="border-t p-3 bg-muted/30">
            <div className="space-y-2">
              {episode.steps.map((step, i) => (
                <div key={i} className="text-sm font-mono text-muted-foreground">
                  {i + 1}. {step.action} {step.locator ? `(${step.locator})` : ''} {step.target || ''}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderPatternRow = (pattern: FailurePattern) => {
    const expanded = expandedItems.has(pattern.id);

    return (
      <div key={pattern.id} className="border rounded-lg overflow-hidden">
        <button
          onClick={() => toggleExpand(pattern.id)}
          className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            <div className="flex-1 min-w-0">
              <p className="font-mono text-sm truncate">{pattern.error_pattern}</p>
              <p className="text-xs text-muted-foreground">Action: {pattern.step_action}</p>
            </div>
            <Badge variant="secondary">{pattern.frequency} occurrences</Badge>
            <span className="text-xs text-muted-foreground">{formatDate(pattern.last_seen_at)}</span>
          </div>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {expanded && (
          <div className="border-t p-3 bg-muted/30 space-y-2">
            {pattern.suggested_fix && (
              <div className="text-sm">
                <span className="font-medium">Suggested Fix:</span> <span className="ml-2">{pattern.suggested_fix}</span>
              </div>
            )}
            <div className="text-xs text-muted-foreground">First seen: {formatDate(pattern.created_at)}</div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Memory Browser</h1>
          <p className="text-muted-foreground">Explore learned locators, test episodes, and failure patterns</p>
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

      <div className="flex gap-4 mb-6">
        <div className="flex-1 max-w-md relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search memory..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            className="pl-10"
            disabled={searching}
          />
        </div>
        <Button onClick={handleSearch} disabled={searching || !searchQuery.trim()}>
          {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
        </Button>
      </div>

      {searchResults && (
        <div className="mb-6 p-4 bg-muted/50 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium">Search Results for "{searchQuery}"</h3>
            <Button variant="ghost" size="sm" onClick={() => { setSearchQuery(''); setSearchResults(null); }}>
              Clear
            </Button>
          </div>
          <div className="grid gap-4 md:grid-cols-3 text-sm">
            <div>
              <span className="text-muted-foreground">Locators: </span>
              <span className="font-medium">{searchResults.locators.length}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Episodes: </span>
              <span className="font-medium">{searchResults.episodes.length}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Failure Patterns: </span>
              <span className="font-medium">{searchResults.failure_patterns.length}</span>
            </div>
          </div>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList>
          <TabsTrigger value="locator">
            <Database className="mr-2 h-4 w-4" />
            Locators ({locators?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="episode">
            <FileText className="mr-2 h-4 w-4" />
            Episodes ({episodes?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="failure_pattern">
            <AlertTriangle className="mr-2 h-4 w-4" />
            Failure Patterns ({patterns?.length || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="locator" className="mt-4">
          {searchResults ? (
            <div className="space-y-2">
              {searchResults.locators.map(renderLocatorRow)}
            </div>
          ) : locators?.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Database className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-4 text-lg font-medium">No locator memory</h3>
                <p className="text-muted-foreground">Locator memory builds up as tests run and succeed/fail</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {locators?.map(renderLocatorRow)}
            </div>
          )}
        </TabsContent>

        <TabsContent value="episode" className="mt-4">
          {searchResults ? (
            <div className="space-y-2">
              {searchResults.episodes.map(renderEpisodeRow)}
            </div>
          ) : episodes?.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-4 text-lg font-medium">No episode memory</h3>
                <p className="text-muted-foreground">Episodes are stored after test runs complete</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {episodes?.map(renderEpisodeRow)}
            </div>
          )}
        </TabsContent>

        <TabsContent value="failure_pattern" className="mt-4">
          {searchResults ? (
            <div className="space-y-2">
              {searchResults.failure_patterns.map(renderPatternRow)}
            </div>
          ) : patterns?.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <AlertTriangle className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-4 text-lg font-medium">No failure patterns</h3>
                <p className="text-muted-foreground">Failure patterns are learned from repeated test failures</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {patterns?.map(renderPatternRow)}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}