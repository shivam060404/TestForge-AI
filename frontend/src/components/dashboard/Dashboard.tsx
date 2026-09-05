'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Play, FileText, Bug, Eye, Database, TrendingUp } from 'lucide-react';
import Link from 'next/link';

const stats = [
  { name: 'Projects', value: '12', icon: FileText, color: 'text-blue-500', href: '/projects' },
  { name: 'Test Cases', value: '247', icon: FileText, color: 'text-green-500', href: '/test-cases' },
  { name: 'Runs (24h)', value: '89', icon: Play, color: 'text-purple-500', href: '/runs' },
  { name: 'Healing Rate', value: '94%', icon: Bug, color: 'text-orange-500', href: '/healing' },
];

const recentRuns = [
  { id: 'run-001', project: 'E-commerce Checkout', testCase: 'Complete purchase flow', status: 'passed', duration: '1m 23s', time: '2 min ago' },
  { id: 'run-002', project: 'User Dashboard', testCase: 'Data visualization load', status: 'failed', duration: '45s', time: '15 min ago' },
  { id: 'run-003', project: 'API Integration', testCase: 'Payment webhook handling', status: 'healing', duration: '2m 10s', time: '1 hour ago' },
  { id: 'run-004', project: 'Mobile App', testCase: 'Onboarding sequence', status: 'passed', duration: '3m 45s', time: '3 hours ago' },
  { id: 'run-005', project: 'Admin Panel', testCase: 'User management CRUD', status: 'passed', duration: '1m 55s', time: '5 hours ago' },
];

export function Dashboard() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your QA automation workspace</p>
        </div>
        <Button asChild>
          <Link href="/projects/new">
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat) => (
          <Card key={stat.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.name}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="md:col-span-4 lg:col-span-4">
          <CardHeader>
            <CardTitle>Recent Test Runs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentRuns.map((run) => (
                <Link key={run.id} href={`/runs/${run.id}`} className="block hover:bg-accent rounded-lg p-4 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{run.testCase}</p>
                      <p className="text-sm text-muted-foreground">{run.project}</p>
                    </div>
                    <div className="flex items-center gap-3 ml-4">
                      <Badge variant="status" status={run.status} />
                      <span className="text-sm text-muted-foreground">{run.duration}</span>
                      <span className="text-xs text-muted-foreground">{run.time}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2 lg:col-span-2">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button asChild variant="outline" className="w-full justify-start gap-3">
              <Link href="/projects/new">
                <Plus className="h-4 w-4" />
                Create Project
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full justify-start gap-3">
              <Link href="/test-cases/new">
                <FileText className="h-4 w-4" />
                Write Test Case
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full justify-start gap-3">
              <Link href="/runs/new">
                <Play className="h-4 w-4" />
                Run Tests
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full justify-start gap-3">
              <Link href="/healing">
                <Bug className="h-4 w-4" />
                Review Healing
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full justify-start gap-3">
              <Link href="/design">
                <Eye className="h-4 w-4" />
                Design Insights
              </Link>
            </Button>
            <Button asChild variant="outline" className="w-full justify-start gap-3">
              <Link href="/memory">
                <Database className="h-4 w-4" />
                Memory Browser
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="md:col-span-1 lg:col-span-1">
          <CardHeader>
            <CardTitle>System Health</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">API Status</span>
              <Badge variant="status" status="passed">Healthy</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Worker Pool</span>
              <Badge variant="status" status="running">3 Active</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Browser Pool</span>
              <Badge variant="status" status="passed">5/5 Ready</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Storage</span>
              <Badge variant="secondary">2.3 GB / 10 GB</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}