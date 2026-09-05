'use client';

import { useState } from 'react';
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
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Save,
  Loader2,
  Key,
  Server,
  Database,
  Eye,
  Bug,
  Brain,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function SettingsPage() {
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('general');
  const { toast } = useToast();

  const handleSave = async () => {
    setSaving(true);
    await new Promise(r => setTimeout(r, 1000));
    setSaving(false);
    toast({ title: 'Settings saved' });
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Configure your Autonomous QA Agent</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="general">
            <Server className="mr-2 h-4 w-4" />
            General
          </TabsTrigger>
          <TabsTrigger value="execution">
            <Bug className="mr-2 h-4 w-4" />
            Test Execution
          </TabsTrigger>
          <TabsTrigger value="healing">
            <Brain className="mr-2 h-4 w-4" />
            Self-Healing
          </TabsTrigger>
          <TabsTrigger value="design">
            <Eye className="mr-2 h-4 w-4" />
            Design Intelligence
          </TabsTrigger>
          <TabsTrigger value="integrations">
            <Key className="mr-2 h-4 w-4" />
            Integrations
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="org-name">Organization Name</Label>
                  <Input id="org-name" defaultValue="Acme Corp" placeholder="Your organization" />
                </div>
                <div>
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select timezone" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="UTC">UTC</SelectItem>
                      <SelectItem value="America/New_York">Eastern Time</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                      <SelectItem value="Europe/London">London</SelectItem>
                      <SelectItem value="Europe/Paris">Paris</SelectItem>
                      <SelectItem value="Asia/Tokyo">Tokyo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Dark Mode</Label>
                  <p className="text-sm text-muted-foreground">Enable dark theme</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">Receive notifications for test failures</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-healing Enabled</Label>
                  <p className="text-sm text-muted-foreground">Automatically apply high-confidence healing</p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="execution">
          <Card>
            <CardHeader>
              <CardTitle>Test Execution</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <Label htmlFor="default-timeout">Default Step Timeout (ms)</Label>
                  <Input id="default-timeout" type="number" defaultValue="30000" />
                </div>
                <div>
                  <Label htmlFor="navigation-timeout">Navigation Timeout (ms)</Label>
                  <Input id="navigation-timeout" type="number" defaultValue="60000" />
                </div>
                <div>
                  <Label htmlFor="max-retries">Max Retries</Label>
                  <Input id="max-retries" type="number" defaultValue="2" />
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="browser">Default Browser</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select browser" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="chromium">Chromium</SelectItem>
                      <SelectItem value="firefox">Firefox</SelectItem>
                      <SelectItem value="webkit">WebKit</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="headless">Headless Mode</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select mode" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="true">Headless</SelectItem>
                      <SelectItem value="false">Headful</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Video Recording</Label>
                  <p className="text-sm text-muted-foreground">Record video of test execution</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Trace Collection</Label>
                  <p className="text-sm text-muted-foreground">Collect Playwright traces for debugging</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Parallel Execution</Label>
                  <p className="text-sm text-muted-foreground">Run multiple tests in parallel</p>
                </div>
                <Switch />
              </div>
              <div>
                <Label htmlFor="max-parallel">Max Parallel Workers</Label>
                <Input id="max-parallel" type="number" defaultValue="3" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="healing">
          <Card>
            <CardHeader>
              <CardTitle>Self-Healing Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="healing-confidence">Auto-approve Confidence Threshold</Label>
                  <Input id="healing-confidence" type="number" step="0.05" min="0" max="1" defaultValue="0.85" />
                  <p className="text-sm text-muted-foreground">Minimum confidence for auto-approval (0-1)</p>
                </div>
                <div>
                  <Label htmlFor="healing-strategies">Healing Strategies</Label>
                  <Select>
                    <SelectTrigger><SelectValue placeholder="Select strategies" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="testId">data-testid</SelectItem>
                      <SelectItem value="id">ID</SelectItem>
                      <SelectItem value="role">ARIA Role</SelectItem>
                      <SelectItem value="text">Text Content</SelectItem>
                      <SelectItem value="css">CSS Selector</SelectItem>
                      <SelectItem value="xpath">XPath</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="max-candidates">Max Candidates per Failure</Label>
                  <Input id="max-candidates" type="number" defaultValue="5" />
                </div>
                <div>
                  <Label htmlFor="healing-timeout">Healing Timeout (ms)</Label>
                  <Input id="healing-timeout" type="number" defaultValue="10000" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Learn from Approvals</Label>
                  <p className="text-sm text-muted-foreground">Store approved healings for future use</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Cross-project Memory</Label>
                  <p className="text-sm text-muted-foreground">Share healing learnings across projects</p>
                </div>
                <Switch />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="design">
          <Card>
            <CardHeader>
              <CardTitle>Design Intelligence</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <Label htmlFor="visual-threshold">Visual Diff Threshold (%)</Label>
                  <Input id="visual-threshold" type="number" step="0.1" min="0" max="100" defaultValue="10" />
                </div>
                <div>
                  <Label htmlFor="viewport-width">Default Viewport Width</Label>
                  <Input id="viewport-width" type="number" defaultValue="1280" />
                </div>
                <div>
                  <Label htmlFor="viewport-height">Default Viewport Height</Label>
                  <Input id="viewport-height" type="number" defaultValue="720" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Visual Regression Testing</Label>
                  <p className="text-sm text-muted-foreground">Compare screenshots against baselines</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Accessibility Checks</Label>
                  <p className="text-sm text-muted-foreground">Run axe-core accessibility audits</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Performance Metrics</Label>
                  <p className="text-sm text-muted-foreground">Collect Core Web Vitals</p>
                </div>
                <Switch />
              </div>
              <div>
                <Label htmlFor="axe-rules">Accessibility Rules</Label>
                <Select>
                  <SelectTrigger><SelectValue placeholder="Select rules" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="color-contrast">Color Contrast</SelectItem>
                    <SelectItem value="label">Form Labels</SelectItem>
                    <SelectItem value="keyboard">Keyboard Navigation</SelectItem>
                    <SelectItem value="aria">ARIA Attributes</SelectItem>
                    <SelectItem value="focus">Focus Management</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="integrations">
          <Card>
            <CardHeader>
              <CardTitle>Integrations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium">CI/CD</h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">GitHub Actions</p>
                        <p className="text-sm text-muted-foreground">Run tests on push/PR</p>
                      </div>
                      <Switch />
                    </div>
                  </div>
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">GitLab CI</p>
                        <p className="text-sm text-muted-foreground">Pipeline integration</p>
                      </div>
                      <Switch />
                    </div>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <h4 className="font-medium">Notifications</h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Slack</p>
                        <p className="text-sm text-muted-foreground">Channel notifications</p>
                      </div>
                      <Switch />
                    </div>
                  </div>
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Microsoft Teams</p>
                        <p className="text-sm text-muted-foreground">Team notifications</p>
                      </div>
                      <Switch />
                    </div>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <h4 className="font-medium">Issue Tracking</h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Jira</p>
                        <p className="text-sm text-muted-foreground">Create issues from failures</p>
                      </div>
                      <Switch />
                    </div>
                  </div>
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Linear</p>
                        <p className="text-sm text-muted-foreground">Create issues from failures</p>
                      </div>
                      <Switch />
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="mt-6 flex justify-end">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <><Save className="mr-2 h-4 w-4" />Save Settings</>}
        </Button>
      </div>
    </div>
  );
}