import { useState } from 'react'
import { Settings as SettingsIcon, Key, Database, Bell, Palette } from 'lucide-react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Label,
} from '@/components/ui'

export default function Settings() {
  const [apiKey, setApiKey] = useState('')
  const [apiEndpoint, setApiEndpoint] = useState('http://localhost:8000')

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-foreground-secondary">
          Configure your AgentWorld preferences.
        </p>
      </div>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Key className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle>API Configuration</CardTitle>
              <CardDescription>
                Configure the connection to your AgentWorld backend.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="api-endpoint">API Endpoint</Label>
            <Input
              id="api-endpoint"
              value={apiEndpoint}
              onChange={(e) => setApiEndpoint(e.target.value)}
              placeholder="http://localhost:8000"
            />
            <p className="text-xs text-foreground-muted">
              The URL of your AgentWorld API server.
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="api-key">API Key (Optional)</Label>
            <Input
              id="api-key"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
            />
            <p className="text-xs text-foreground-muted">
              Only required if API authentication is enabled.
            </p>
          </div>
          <Button>Save API Settings</Button>
        </CardContent>
      </Card>

      {/* LLM Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-accent/10 flex items-center justify-center">
              <Database className="h-5 w-5 text-accent" />
            </div>
            <div>
              <CardTitle>LLM Provider</CardTitle>
              <CardDescription>
                Configure your language model provider settings.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="openai-key">OpenAI API Key</Label>
            <Input
              id="openai-key"
              type="password"
              placeholder="sk-..."
            />
            <p className="text-xs text-foreground-muted">
              Your OpenAI API key for GPT models.
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="default-model">Default Model</Label>
            <select
              id="default-model"
              className="flex h-10 w-full rounded-md border border-border bg-background-secondary px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>
          <Button>Save LLM Settings</Button>
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-success/10 flex items-center justify-center">
              <Palette className="h-5 w-5 text-success" />
            </div>
            <div>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>
                Customize the look and feel of the application.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Dark Mode</p>
              <p className="text-sm text-foreground-secondary">
                Toggle between light and dark themes.
              </p>
            </div>
            <Button variant="outline" disabled>
              Dark (Default)
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Compact Mode</p>
              <p className="text-sm text-foreground-secondary">
                Reduce spacing for more content density.
              </p>
            </div>
            <Button variant="outline" disabled>
              Off
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-warning/10 flex items-center justify-center">
              <Bell className="h-5 w-5 text-warning" />
            </div>
            <div>
              <CardTitle>Notifications</CardTitle>
              <CardDescription>
                Configure notification preferences.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Simulation Complete</p>
              <p className="text-sm text-foreground-secondary">
                Notify when a simulation finishes running.
              </p>
            </div>
            <Button variant="outline" disabled>
              On
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Cost Alerts</p>
              <p className="text-sm text-foreground-secondary">
                Warn when approaching cost limits.
              </p>
            </div>
            <Button variant="outline" disabled>
              On
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center">
              <SettingsIcon className="h-5 w-5 text-foreground-secondary" />
            </div>
            <div>
              <CardTitle>About AgentWorld</CardTitle>
              <CardDescription>
                Application information and version.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-foreground-secondary">
          <p>Version: 0.1.0</p>
          <p>Build: Development</p>
          <p>
            <a
              href="https://github.com/anthropics/agentworld"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              GitHub Repository
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
