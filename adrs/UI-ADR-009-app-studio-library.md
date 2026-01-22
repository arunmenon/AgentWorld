# UI-ADR-009: App Studio Library & Navigation

## Status
Proposed

## Date
2026-01-22

## Dependencies
- **UI-ADR-001**: Design System (card components, colors)
- **UI-ADR-002**: Information Architecture (navigation structure)
- **ADR-018**: App Studio Backend (API endpoints)

## Context

### Problem Statement
Users need a central place to browse, manage, and create simulated apps. The App Studio should feel like a first-class feature alongside Simulations and Personas.

### Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| REQ-09-01 | App Library Page | Must | Browse all app definitions |
| REQ-09-02 | Navigation Integration | Must | App Studio in main nav |
| REQ-09-03 | Category Filtering | Must | Filter apps by category |
| REQ-09-04 | Search | Should | Search apps by name/description |
| REQ-09-05 | Grid/List Views | Should | Toggle between view modes |
| REQ-09-06 | App Cards | Must | Visual card for each app |
| REQ-09-07 | Quick Actions | Should | Edit, duplicate, delete from library |
| REQ-09-08 | Empty State | Must | Guidance when no apps exist |
| REQ-09-09 | Sorting | Should | Sort apps by name, date, category |
| REQ-09-10 | Pagination | Should | Handle large app collections |
| REQ-09-11 | Backend Governance | Must | UI respects backend-enforced built-in rules |

## Decision

### URL Structure

| Path | Description |
|------|-------------|
| `/apps` | App library (main page) |
| `/apps/new` | Create new app (wizard) |
| `/apps/:id` | Edit existing app |
| `/apps/:id/test` | Test sandbox |

### Navigation Addition

```
AgentWorld
├── Dashboard
├── Simulations
├── Personas
├── App Studio  ← NEW (icon: Layers/Puzzle)
│   └── /apps (default)
└── Settings
```

### App Library Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  🧩 App Studio                                       [+ Create App] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🔍 Search apps...                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [All] [💳 Payments] [🛒 Shopping] [📧 Communication] [📅 Calendar] │
│  [💬 Social] [🔧 Custom]         [Sort: Updated ▼] [Grid] [List] │
│                                                                     │
│  SYSTEM APPS (3)                                                    │
│  ───────────────────────────────────────────────────────────────── │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│  │ 💳              │ │ 🛒              │ │ 📧              │       │
│  │ PayPal          │ │ Amazon          │ │ Gmail           │       │
│  │ 6 actions       │ │ 5 actions       │ │ 4 actions       │       │
│  │                 │ │                 │ │                 │       │
│  │ Payment app     │ │ Shopping app    │ │ Email app       │       │
│  │ for transfers   │ │ with cart...    │ │ for sending...  │       │
│  │                 │ │                 │ │                 │       │
│  │ [View] [⋮]      │ │ [View] [⋮]      │ │ [View] [⋮]      │       │
│  │ 🔒 Built-in     │ │ 🔒 Built-in     │ │ 🔒 Built-in     │       │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘       │
│                                                                     │
│  MY APPS (2)                                                        │
│  ───────────────────────────────────────────────────────────────── │
│  ┌─────────────────┐ ┌─────────────────┐                           │
│  │ 🏦              │ │ 📱              │                           │
│  │ Venmo           │ │ Slack           │                           │
│  │ 4 actions       │ │ 3 actions       │                           │
│  │                 │ │                 │                           │
│  │ Social payment  │ │ Team messaging  │                           │
│  │ with friends    │ │ with channels   │                           │
│  │                 │ │                 │                           │
│  │ [Edit] [⋮]      │ │ [Edit] [⋮]      │                           │
│  │ Updated 2d ago  │ │ Updated 1w ago  │                           │
│  └─────────────────┘ └─────────────────┘                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### App Card Component

```
┌─────────────────┐
│ [Icon]          │  ← Category-colored background
│ Name            │
│ X actions       │
│                 │
│ Description     │  ← 2-line truncated
│ (truncated...)  │
│                 │
│ [Action] [⋮]    │  ← Edit/View + overflow menu
│ Status/Time     │  ← Built-in badge OR updated time
└─────────────────┘
```

```tsx
interface AppCardProps {
  app: AppDefinition;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onView: () => void;
}

function AppCard({ app, onEdit, onDuplicate, onDelete, onView }: AppCardProps) {
  const isBuiltin = app.is_builtin;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div
            className={cn(
              "w-12 h-12 rounded-lg flex items-center justify-center text-2xl",
              getCategoryColor(app.category)
            )}
          >
            {app.icon || getCategoryIcon(app.category)}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onView}>
                <Eye className="mr-2 h-4 w-4" />
                View Details
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onDuplicate}>
                <Copy className="mr-2 h-4 w-4" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Download className="mr-2 h-4 w-4" />
                Export as JSON
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={onDelete}
                disabled={isBuiltin}
                className="text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent>
        <h3 className="font-semibold text-lg">{app.name}</h3>
        <p className="text-sm text-muted-foreground">
          {app.actions.length} action{app.actions.length !== 1 ? 's' : ''}
        </p>
        <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
          {app.description}
        </p>
      </CardContent>

      <CardFooter className="flex items-center justify-between pt-0">
        <Button
          variant={isBuiltin ? "outline" : "default"}
          size="sm"
          onClick={isBuiltin ? onView : onEdit}
        >
          {isBuiltin ? "View" : "Edit"}
        </Button>
        <span className="text-xs text-muted-foreground">
          {isBuiltin ? (
            <span className="flex items-center gap-1">
              <Lock className="h-3 w-3" />
              Built-in
            </span>
          ) : (
            `Updated ${formatRelativeTime(app.updated_at)}`
          )}
        </span>
      </CardFooter>
    </Card>
  );
}
```

### Context Menu (⋮)

```
┌─────────────────────────┐
│ View Details        👁️  │
│ ─────────────────────── │
│ Duplicate           📋  │
│ Export as JSON      ↗️  │
│ ─────────────────────── │
│ Delete              🗑️  │  ← Disabled for built-in
└─────────────────────────┘
```

### Empty State

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                         🧩                                          │
│                                                                     │
│                   No apps yet                                       │
│                                                                     │
│     Apps let your agents interact with simulated services           │
│     like payment systems, shopping carts, and email.                │
│                                                                     │
│     [+ Create Your First App]   [Browse Templates]                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Sorting Options

| Sort Key | Label | Description |
|----------|-------|-------------|
| `updated_at` | Updated | Most recently updated first (default) |
| `created_at` | Created | Most recently created first |
| `name` | Name | Alphabetical A-Z |
| `category` | Category | Grouped by category |

### Pagination

For collections exceeding 50 apps, pagination is applied:

```
┌─────────────────────────────────────────────────────────────────────┐
│  ...app cards...                                                    │
│                                                                     │
│  Showing 1-20 of 75 apps            [← Prev] [1] [2] [3] [4] [Next →]│
└─────────────────────────────────────────────────────────────────────┘
```

- **Page size:** 20 apps per page
- **URL state:** `?page=2` persists pagination
- **Combined filters:** Pagination resets when search/category changes

### Backend Governance

The UI **must respect backend-enforced governance rules** from ADR-018:

1. **Built-in apps are read-only**: The backend returns `403 Forbidden` for any modification attempts on built-in apps. The UI should:
   - Disable Edit button (show "View" instead)
   - Disable Delete menu item
   - Show 🔒 badge indicating protected status

2. **Backend is authoritative**: Even if a malicious client tries to modify a built-in app, the backend rejects the request. The UI enforcement is for UX, not security.

3. **Error handling**: If a 403 is received unexpectedly, show: "This app cannot be modified"

### Category Colors

| Category | Background | Icon |
|----------|------------|------|
| payment | `bg-green-100` | 💳 |
| shopping | `bg-blue-100` | 🛒 |
| communication | `bg-purple-100` | 📧 |
| calendar | `bg-yellow-100` | 📅 |
| social | `bg-pink-100` | 💬 |
| custom | `bg-gray-100` | 🔧 |

### Component Architecture

```
web/src/
├── pages/
│   └── Apps.tsx                    # Main library page
├── components/
│   └── app-studio/
│       ├── AppCard.tsx             # Individual app card
│       ├── AppCardGrid.tsx         # Grid layout container
│       ├── AppCardList.tsx         # List layout container
│       ├── AppCategoryTabs.tsx     # Category filter tabs
│       ├── AppSearchInput.tsx      # Search input
│       └── AppEmptyState.tsx       # Empty state component
└── lib/
    ├── api/
    │   └── app-definitions.ts      # API client functions
    └── types/
        └── apps.ts                 # AppDefinition types
```

### TypeScript Interfaces

```typescript
// lib/types/apps.ts

export interface AppDefinition {
  id: string;
  app_id: string;
  name: string;
  description: string;
  category: AppCategory;
  icon: string;
  version: number;
  definition: AppDefinitionDetails;
  is_builtin: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export type AppCategory =
  | 'payment'
  | 'shopping'
  | 'communication'
  | 'calendar'
  | 'social'
  | 'custom';

export interface AppDefinitionDetails {
  app_id: string;
  name: string;
  description: string;
  category: AppCategory;
  icon: string;
  actions: ActionDefinition[];
  state_schema: StateField[];
  initial_config: Record<string, unknown>;
}

export interface ActionDefinition {
  name: string;
  description: string;
  parameters: Record<string, ParamSpec>;
  returns: Record<string, unknown>;
  logic: LogicBlock[];
}

export interface ParamSpec {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description?: string;
  required?: boolean;
  default?: unknown;
  minValue?: number;
  maxValue?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  enum?: unknown[];
}

export interface StateField {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  default?: unknown;
  perAgent?: boolean;
  description?: string;
}

export type LogicBlock =
  | ValidateBlock
  | UpdateBlock
  | NotifyBlock
  | ReturnBlock
  | ErrorBlock
  | BranchBlock
  | LoopBlock;

// ... block type definitions
```

### API Client

```typescript
// lib/api/app-definitions.ts

import { AppDefinition, AppDefinitionDetails } from '../types/apps';

const BASE_URL = '/api/v1/app-definitions';

export interface ListAppDefinitionsParams {
  category?: string;
  search?: string;
  sort_by?: 'updated_at' | 'created_at' | 'name' | 'category';
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export async function listAppDefinitions(
  params?: ListAppDefinitionsParams
): Promise<PaginatedResponse<AppDefinition>> {
  const searchParams = new URLSearchParams();
  if (params?.category) searchParams.set('category', params.category);
  if (params?.search) searchParams.set('search', params.search);
  if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params?.sort_order) searchParams.set('sort_order', params.sort_order);
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size) searchParams.set('page_size', String(params.page_size));

  const response = await fetch(`${BASE_URL}?${searchParams}`);
  if (!response.ok) throw new Error('Failed to fetch app definitions');
  return response.json();
}

export async function getAppDefinition(id: string): Promise<AppDefinition> {
  const response = await fetch(`${BASE_URL}/${id}`);
  if (!response.ok) throw new Error('Failed to fetch app definition');
  return response.json();
}

export async function createAppDefinition(
  definition: AppDefinitionDetails
): Promise<AppDefinition> {
  const response = await fetch(BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(definition),
  });
  if (!response.ok) throw new Error('Failed to create app definition');
  return response.json();
}

export async function updateAppDefinition(
  id: string,
  updates: Partial<AppDefinitionDetails>
): Promise<AppDefinition> {
  const response = await fetch(`${BASE_URL}/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error('Failed to update app definition');
  return response.json();
}

export async function deleteAppDefinition(id: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete app definition');
}

export async function duplicateAppDefinition(
  id: string,
  newName: string
): Promise<AppDefinition> {
  const response = await fetch(`${BASE_URL}/${id}/duplicate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_name: newName }),
  });
  if (!response.ok) throw new Error('Failed to duplicate app definition');
  return response.json();
}

export async function testAppAction(
  id: string,
  action: string,
  agentId: string,
  params: Record<string, unknown>
): Promise<TestResult> {
  const response = await fetch(`${BASE_URL}/${id}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, agent_id: agentId, params }),
  });
  if (!response.ok) throw new Error('Failed to test app action');
  return response.json();
}
```

## Consequences

### Positive
- Consistent with existing Personas library pattern
- Clear visual hierarchy (system vs user apps)
- Easy discovery via categories
- Quick actions accessible
- Familiar patterns for existing users

### Negative
- Another top-level nav item (5 total)
- Grid view may not scale well for many apps
- Category tabs take horizontal space

### Neutral
- Requires maintaining parity with Personas UI
- Search behavior must match user expectations

---

## Validation Checklist

### REQ-09-01: App Library Page

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-01-01 | Navigate to /apps | Page loads | No errors, content visible |
| V09-01-02 | Page shows all apps | All definitions displayed | Count matches API response |
| V09-01-03 | Page loads with empty DB | Empty state shown | Empty state component visible |
| V09-01-04 | Page handles API error | Error state shown | Error message, retry option |

### REQ-09-02: Navigation Integration

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-02-01 | Main nav has App Studio | Item visible | Nav item in shell |
| V09-02-02 | Click App Studio | Routes to /apps | URL is /apps |
| V09-02-03 | Active state | Item highlighted | Active class applied |
| V09-02-04 | Mobile nav | App Studio in mobile menu | Visible in collapsed menu |

### REQ-09-03: Category Filtering

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-03-01 | Click category tab | Filters to category | Only matching apps shown |
| V09-03-02 | Click "All" tab | Shows all apps | No filtering applied |
| V09-03-03 | Category has no apps | Empty state for category | "No payment apps" message |
| V09-03-04 | Filter persists on refresh | URL has filter param | `?category=payment` |

### REQ-09-04: Search

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-04-01 | Type search term | Results filter | Matching apps shown |
| V09-04-02 | Search name match | App found | Case-insensitive match |
| V09-04-03 | Search description match | App found | Searches description |
| V09-04-04 | No matches | Empty state | "No apps matching..." |
| V09-04-05 | Clear search | All apps shown | Full list restored |
| V09-04-06 | Search + category | Both filters applied | Combined filtering |

### REQ-09-05: Grid/List Views

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-05-01 | Default view | Grid displayed | Cards in grid layout |
| V09-05-02 | Click list view | List displayed | Cards in list layout |
| V09-05-03 | View preference persists | Same on refresh | localStorage saves preference |
| V09-05-04 | Responsive grid | Columns adjust | 3→2→1 cols on smaller screens |

### REQ-09-06: App Cards

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-06-01 | Card shows icon | Icon visible | Correct emoji/icon |
| V09-06-02 | Card shows name | Name visible | Correct app name |
| V09-06-03 | Card shows action count | Count visible | "X actions" label |
| V09-06-04 | Card shows description | Truncated text | 2-line max with ellipsis |
| V09-06-05 | Built-in badge | Badge shown | 🔒 Built-in for system apps |
| V09-06-06 | Updated time | Time shown | "Updated 2d ago" for user apps |

### REQ-09-07: Quick Actions

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-07-01 | Click Edit (user app) | Opens edit wizard | Routes to /apps/:id |
| V09-07-02 | Click View (system app) | Opens view mode | Read-only display |
| V09-07-03 | Open context menu | Menu opens | All options visible |
| V09-07-04 | Click Duplicate | Creates copy | New app in list |
| V09-07-05 | Click Delete | Confirmation dialog | App removed after confirm |
| V09-07-06 | Delete disabled for built-in | Option grayed out | Cannot delete system apps |

### REQ-09-08: Empty State

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-08-01 | No apps at all | Full empty state | Guidance text shown |
| V09-08-02 | Click create button | Opens wizard | Routes to /apps/new |
| V09-08-03 | Click browse templates | Opens template picker | Template modal opens |

### REQ-09-09: Sorting

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-09-01 | Default sort | Updated descending | Most recent first |
| V09-09-02 | Sort by name | Alphabetical | A-Z order |
| V09-09-03 | Sort by created | By creation date | Newest first |
| V09-09-04 | Toggle sort direction | Reverses order | Click toggles asc/desc |
| V09-09-05 | Sort persists in URL | `?sort_by=name` | Reload preserves sort |

### REQ-09-10: Pagination

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-10-01 | < 20 apps | No pagination | Single page shown |
| V09-10-02 | > 20 apps | Pagination shown | Page controls visible |
| V09-10-03 | Click next page | Page 2 loads | URL shows `?page=2` |
| V09-10-04 | Filter change | Resets to page 1 | Category change resets |
| V09-10-05 | Total count | Accurate count | "Showing 1-20 of 75" |

### REQ-09-11: Backend Governance

| Test ID | Scenario | Expected Result | Verification |
|---------|----------|-----------------|--------------|
| V09-11-01 | Built-in app shows badge | 🔒 visible | Lock icon shown |
| V09-11-02 | Built-in app no Edit | View button only | Edit disabled |
| V09-11-03 | Built-in app no Delete | Menu item disabled | Grayed out |
| V09-11-04 | Backend 403 on modify | Error toast | "Cannot be modified" |
| V09-11-05 | Duplicate built-in | Creates new copy | Copy is editable |

---

## Implementation Files

### New Files
| File | Purpose |
|------|---------|
| `web/src/pages/Apps.tsx` | Main library page |
| `web/src/components/app-studio/AppCard.tsx` | App card component |
| `web/src/components/app-studio/AppCardGrid.tsx` | Grid container |
| `web/src/components/app-studio/AppCardList.tsx` | List container |
| `web/src/components/app-studio/AppCategoryTabs.tsx` | Category tabs |
| `web/src/components/app-studio/AppSearchInput.tsx` | Search input |
| `web/src/components/app-studio/AppEmptyState.tsx` | Empty state |
| `web/src/lib/api/app-definitions.ts` | API client |
| `web/src/lib/types/apps.ts` | TypeScript types |

### Modified Files
| File | Changes |
|------|---------|
| `web/src/App.tsx` | Add /apps routes |
| `web/src/components/Layout.tsx` | Add App Studio nav item |

---

## References

- UI-ADR-001: Design System - Card components, colors
- UI-ADR-002: Information Architecture - Navigation structure
- UI-ADR-006: Persona Builder - Similar library pattern
- ADR-018: App Studio Backend - API endpoints
