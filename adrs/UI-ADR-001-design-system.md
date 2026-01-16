# UI-ADR-001: Design System & Visual Language

## Status
Accepted

## Dependencies
- **ADR-007**: Visualization Strategy (establishes CLI + Web dual interface approach)
- **ADR-004**: Trait Vector Persona System (trait visualization requirements)
- **ADR-002**: Agent Scale (max 50 agents informs visual density decisions)

## Context

AgentWorld requires a cohesive visual language that supports two critical use cases:

1. **Research workflows**: Scientists and researchers need precise, information-dense interfaces for analyzing agent behavior
2. **Product testing**: Product managers need intuitive visualizations to understand simulated user feedback

### Design Philosophy Requirements

The UI must embody six core principles derived from user research:

| Principle | Description | Implementation Impact |
|-----------|-------------|----------------------|
| **Observable** | See everything happening in real-time | Rich real-time dashboards, activity feeds |
| **Controllable** | Adjust parameters without stopping | Live controls, inline editing |
| **Explorable** | Dive into any agent's state at any time | Deep drill-down capabilities |
| **Reproducible** | Share and repeat experiments exactly | Export configs, seed display, checkpoints |
| **Efficient** | Fast iteration cycle | Quick start templates, keyboard shortcuts |
| **Progressive** | Simple to start, powerful when needed | Progressive disclosure, advanced toggles |

### The "Mission Control" Metaphor

Drawing inspiration from NASA Mission Control and financial trading floors, the interface centers on:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MISSION CONTROL METAPHOR                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Central Viewport        Peripheral Telemetry     Control Surfaces  │
│  ┌─────────────────┐    ┌─────────────────┐      ┌─────────────┐   │
│  │                 │    │                 │      │             │   │
│  │   Simulation    │    │  Agent Status   │      │  Play/Pause │   │
│  │   Main Event    │    │  Memory Usage   │      │  Step       │   │
│  │   Stream        │    │  Token Costs    │      │  Inject     │   │
│  │                 │    │  Network Stats  │      │  Export     │   │
│  │                 │    │                 │      │             │   │
│  └─────────────────┘    └─────────────────┘      └─────────────┘   │
│                                                                     │
│  "Status at a glance,   "Continuous health     "Precise control    │
│   details on demand"     monitoring"            when needed"        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Existing Framework Approaches (from ADR-001 analysis)

| Framework | Visual Approach | Strengths | Weaknesses |
|-----------|-----------------|-----------|------------|
| AI Town | 2D game sandbox | Engaging, intuitive | Limited analytics |
| TinyTroupe | Jupyter notebooks | Flexible, code-native | Not production-ready |
| AgentSociety | Web dashboards | Metrics-focused | Less agent detail |
| CrewAI | CLI logs | Developer-friendly | No visual overview |

## Decision

Implement a comprehensive design system based on the **Mission Control metaphor** with a dark-theme-first, information-dense visual language.

### 1. Color System

```
┌─────────────────────────────────────────────────────────────────────┐
│                       COLOR PALETTE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SEMANTIC COLORS                                                    │
│  ─────────────────                                                  │
│  Primary:     #6366F1 (Indigo-500)   - Actions, links, focus       │
│  Secondary:   #8B5CF6 (Violet-500)   - Accents, highlights         │
│  Success:     #10B981 (Emerald-500)  - Running, healthy, complete  │
│  Warning:     #F59E0B (Amber-500)    - Caution, approaching limits │
│  Error:       #EF4444 (Red-500)      - Errors, stopped, critical   │
│  Info:        #3B82F6 (Blue-500)     - Informational, neutral      │
│                                                                     │
│  BACKGROUND LAYERS (Dark Theme)                                     │
│  ─────────────────────────────                                      │
│  Base:        #0F172A (Slate-900)    - App background              │
│  Surface:     #1E293B (Slate-800)    - Cards, panels               │
│  Elevated:    #334155 (Slate-700)    - Modals, dropdowns           │
│  Subtle:      #475569 (Slate-600)    - Dividers, borders           │
│                                                                     │
│  TEXT HIERARCHY                                                     │
│  ──────────────                                                     │
│  Primary:     #F8FAFC (Slate-50)     - Headlines, important text   │
│  Secondary:   #CBD5E1 (Slate-300)    - Body text, descriptions     │
│  Muted:       #94A3B8 (Slate-400)    - Labels, timestamps          │
│  Disabled:    #64748B (Slate-500)    - Inactive elements           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Trait-Derived Agent Colors (Cross-ref: ADR-004)

Agent avatars use colors derived from their Big Five trait vectors:

```python
def trait_to_color(trait_vector: TraitVector) -> str:
    """
    Map dominant trait to agent color for visual consistency.

    Trait Mapping (from ADR-004):
    - High Openness (>0.7):     Purple (#A78BFA) - Creative, curious
    - High Conscientiousness:   Blue (#60A5FA)   - Organized, disciplined
    - High Extraversion:        Orange (#F97316) - Outgoing, energetic
    - High Agreeableness:       Green (#4ADE80)  - Cooperative, trusting
    - High Neuroticism:         Red (#F87171)    - Anxious, reactive
    - Balanced/Neutral:         Gray (#9CA3AF)   - No dominant trait
    """
    traits = [
        (trait_vector.openness, '#A78BFA'),
        (trait_vector.conscientiousness, '#60A5FA'),
        (trait_vector.extraversion, '#F97316'),
        (trait_vector.agreeableness, '#4ADE80'),
        (trait_vector.neuroticism, '#F87171'),
    ]
    dominant = max(traits, key=lambda x: x[0])
    return dominant[1] if dominant[0] > 0.7 else '#9CA3AF'
```

### 3. Typography System

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TYPOGRAPHY SCALE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  FONT FAMILY                                                        │
│  ───────────                                                        │
│  Primary:    Inter (UI elements, body text)                         │
│  Monospace:  JetBrains Mono (code, logs, agent IDs)                │
│                                                                     │
│  SIZE SCALE                                                         │
│  ──────────                                                         │
│  xs:   12px / 1.5   - Timestamps, badges, metadata                 │
│  sm:   14px / 1.5   - Secondary text, labels                       │
│  base: 16px / 1.5   - Body text, descriptions                      │
│  lg:   18px / 1.5   - Subheadings, emphasized text                 │
│  xl:   20px / 1.4   - Section headers                              │
│  2xl:  24px / 1.3   - Page titles                                  │
│  3xl:  30px / 1.2   - Dashboard headlines                          │
│                                                                     │
│  WEIGHTS                                                            │
│  ───────                                                            │
│  Regular:   400  - Body text                                        │
│  Medium:    500  - Labels, buttons                                  │
│  Semibold:  600  - Headings, emphasis                               │
│  Bold:      700  - Critical information                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4. Spacing & Layout System

```
SPACING SCALE (8px base unit):
─────────────────────────────
1:  4px   - Tight grouping (icon + label)
2:  8px   - Related elements
3:  12px  - Component internal padding
4:  16px  - Section spacing
5:  20px  - Card padding
6:  24px  - Panel gaps
8:  32px  - Major sections
10: 40px  - Page margins
12: 48px  - Header height

BORDER RADIUS:
──────────────
sm:   4px  - Buttons, inputs
md:   8px  - Cards, panels
lg:  12px  - Modals, dialogs
full: 9999px - Avatars, badges

SHADOWS (Dark Theme):
────────────────────
sm:   0 1px 2px rgba(0,0,0,0.3)      - Subtle elevation
md:   0 4px 6px rgba(0,0,0,0.4)      - Cards
lg:   0 10px 15px rgba(0,0,0,0.5)    - Modals
glow: 0 0 20px rgba(99,102,241,0.3)  - Focus states

ELEVATION SYSTEM (4 levels):
────────────────────────────
Level 0:  Base surface - No shadow, bg-slate-900
Level 1:  Raised - shadow-sm, bg-slate-800 (cards, list items)
Level 2:  Floating - shadow-md, bg-slate-700 (dropdowns, tooltips)
Level 3:  Modal - shadow-lg, bg-slate-700 (dialogs, modals, command palette)

┌─────────────────────────────────────────────────────────────────┐
│              ELEVATION VISUAL HIERARCHY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Level 3: Modal ████████████████████  (shadow-lg)              │
│                 ████████████████████                            │
│           ↑                                                     │
│  Level 2: ██████████████████████████████  (shadow-md)          │
│           Floating (dropdowns, popovers)                        │
│           ↑                                                     │
│  Level 1: ████████████████████████████████████  (shadow-sm)    │
│           Raised (cards, panels)                                │
│           ↑                                                     │
│  Level 0: ██████████████████████████████████████████  (none)   │
│           Base (page background)                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

ICON SIZING SCALE:
──────────────────
xs:   12px  - Inline indicators (status dots)
sm:   16px  - Button icons, input adornments
md:   20px  - Navigation icons, list item icons
lg:   24px  - Card headers, section icons
xl:   32px  - Empty state illustrations, feature icons
2xl:  48px  - Hero illustrations, onboarding
```

### 5. Component Visual Specifications

#### TraitSlider (Cross-ref: ADR-004)

```
┌─────────────────────────────────────────────────────────────────────┐
│  TraitSlider Component                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Openness                                                    0.85   │
│  ├─────────────────────────────────────────●────────────────────┤  │
│  Practical                              Creative                    │
│                                                                     │
│  Visual Specs:                                                      │
│  - Track: 4px height, rounded-full, bg-slate-700                   │
│  - Fill: gradient from gray to trait color                         │
│  - Thumb: 16px circle, white, shadow-md                            │
│  - Labels: text-xs, text-slate-400                                 │
│  - Value: text-sm, font-mono, text-slate-200                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### MemoryCard (Cross-ref: ADR-006)

```
┌─────────────────────────────────────────────────────────────────────┐
│  MemoryCard Component                                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ ▌ "Discussed product pricing with Bob. He seemed hesitant..."  ││
│  │                                                                 ││
│  │ 🕐 2 min ago    💡 Importance: 7/10    📍 Focus Group          ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Visual Specs:                                                      │
│  - Card: bg-slate-800, rounded-md, border-l-4                      │
│  - Border color: importance gradient (1-3: gray, 4-6: blue,        │
│                                        7-8: purple, 9-10: gold)    │
│  - Content: text-sm, text-slate-200                                │
│  - Metadata: text-xs, text-slate-400, flex gap-4                   │
│  - Observation: solid border | Reflection: dashed border           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### ConversationBubble

```
┌─────────────────────────────────────────────────────────────────────┐
│  ConversationBubble Variants                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SPEECH (Agent speaking):                                           │
│  ┌──────────────────────────────────────────┐                      │
│  │  Lisa                              10:23  │                      │
│  │  "I think the pricing is too high for    │                      │
│  │   the target market we discussed."       │                      │
│  └──────────────────────────────────────────┘                      │
│  bg-slate-700, rounded-lg, border-none                             │
│                                                                     │
│  THOUGHT (Agent thinking):                                          │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐                      │
│  │  Lisa                          💭 10:23  │                      │
│  │  Considering how to phrase my concern... │                      │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘                      │
│  bg-slate-800, dashed border, italic text                          │
│                                                                     │
│  ACTION (Agent doing):                                              │
│  ┌══════════════════════════════════════════┐                      │
│  │  Lisa                          ⚡ 10:23  │                      │
│  │  [Writes notes about pricing feedback]   │                      │
│  └══════════════════════════════════════════┘                      │
│  bg-indigo-900/30, double border, text-indigo-200                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6. Form Validation Patterns

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FORM VALIDATION SYSTEM                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  VALIDATION STATES                                                  │
│  ─────────────────                                                  │
│  Default:   border-slate-600, focus:border-primary                 │
│  Valid:     border-emerald-500, icon-check (right side)            │
│  Invalid:   border-red-500, icon-alert-circle (right side)         │
│  Warning:   border-amber-500, icon-alert-triangle                  │
│  Disabled:  border-slate-700, bg-slate-800/50, cursor-not-allowed  │
│                                                                     │
│  INPUT FIELD ANATOMY                                                │
│  ────────────────────                                               │
│                                                                     │
│  Label (required)                                                   │
│  ┌────────────────────────────────────────────────┬────┐           │
│  │ Placeholder text...                            │ ⚠  │           │
│  └────────────────────────────────────────────────┴────┘           │
│  Helper text or error message                                       │
│                                                                     │
│  VISUAL SPECIFICATIONS                                              │
│  ─────────────────────                                              │
│  Label:                                                             │
│    - text-sm, font-medium, text-slate-300                          │
│    - Required indicator: text-red-400 "*"                          │
│    - margin-bottom: 4px                                            │
│                                                                     │
│  Input:                                                             │
│    - height: 40px (default), 36px (compact), 48px (large)          │
│    - padding: 12px horizontal, centered vertical                    │
│    - border-radius: 4px (sm)                                       │
│    - border-width: 1px (default), 2px (focus/error)                │
│    - bg-slate-800                                                  │
│                                                                     │
│  Helper/Error Text:                                                 │
│    - text-xs, margin-top: 4px                                      │
│    - Helper: text-slate-400                                        │
│    - Error: text-red-400                                           │
│    - Success: text-emerald-400                                     │
│                                                                     │
│  VALIDATION ICON PLACEMENT                                          │
│  ─────────────────────────                                          │
│    - Position: absolute, right: 12px, vertically centered          │
│    - Size: 16px (sm icon scale)                                    │
│    - Colors: match validation state                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Form Field Example States

```
┌─────────────────────────────────────────────────────────────────────┐
│  Form Field States                                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DEFAULT STATE                                                      │
│  Simulation Name *                                                  │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Enter a name for your simulation                           │    │
│  └────────────────────────────────────────────────────────────┘    │
│  Give your simulation a descriptive name                            │
│                                                                     │
│  FOCUS STATE                                                        │
│  Simulation Name *                                                  │
│  ┌════════════════════════════════════════════════════════════┐    │
│  │ Product Focus Group                                        │    │
│  └════════════════════════════════════════════════════════════┘    │
│  Give your simulation a descriptive name                            │
│  (border: 2px solid #6366F1, glow shadow)                          │
│                                                                     │
│  VALID STATE                                                        │
│  Simulation Name *                                                  │
│  ┌────────────────────────────────────────────────────────┬───┐    │
│  │ Product Focus Group                                    │ ✓ │    │
│  └────────────────────────────────────────────────────────┴───┘    │
│  (border: 1px solid #10B981, check icon)                           │
│                                                                     │
│  ERROR STATE                                                        │
│  Simulation Name *                                                  │
│  ┌────────────────────────────────────────────────────────┬───┐    │
│  │                                                        │ ⚠ │    │
│  └────────────────────────────────────────────────────────┴───┘    │
│  ⚠ Simulation name is required                                      │
│  (border: 1px solid #EF4444, error icon, red helper text)          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Inline Validation Rules

```typescript
// Validation timing
interface ValidationConfig {
  validateOn: 'blur' | 'change' | 'submit';  // Default: 'blur'
  revalidateOn: 'change';                     // After first validation
  debounceMs: 300;                            // For change validation
}

// Common validation patterns
const validationPatterns = {
  required: (value: string) => value.trim().length > 0,
  minLength: (min: number) => (value: string) => value.length >= min,
  maxLength: (max: number) => (value: string) => value.length <= max,
  pattern: (regex: RegExp) => (value: string) => regex.test(value),
  range: (min: number, max: number) => (value: number) => value >= min && value <= max,

  // AgentWorld-specific
  agentCount: (value: number) => value >= 2 && value <= 50,
  traitValue: (value: number) => value >= 0 && value <= 1,
  simulationName: (value: string) => /^[a-zA-Z0-9][a-zA-Z0-9\s\-_]{2,49}$/.test(value),
};
```

### 7. Animation & Motion

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MOTION SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TIMING FUNCTIONS                                                   │
│  ────────────────                                                   │
│  ease-out:     cubic-bezier(0, 0, 0.2, 1)   - Entrances           │
│  ease-in:      cubic-bezier(0.4, 0, 1, 1)   - Exits               │
│  ease-in-out:  cubic-bezier(0.4, 0, 0.2, 1) - State changes       │
│  spring:       cubic-bezier(0.34, 1.56, 0.64, 1) - Playful        │
│                                                                     │
│  DURATIONS                                                          │
│  ─────────                                                          │
│  instant:  75ms   - Micro-interactions (hover, focus)              │
│  fast:    150ms   - Button clicks, toggles                         │
│  normal:  300ms   - Panel slides, fades                            │
│  slow:    500ms   - Modal entrances, page transitions              │
│  slower:  700ms   - Complex animations                             │
│                                                                     │
│  ANIMATION PATTERNS                                                 │
│  ──────────────────                                                 │
│  Message arrival:    Slide in from bottom + fade (normal)          │
│  Agent thinking:     Pulsing opacity 50%-100% (1s loop)            │
│  Network pulse:      Edge glow propagation (300ms)                 │
│  Step transition:    Timeline marker slide (fast)                  │
│  Panel collapse:     Height + opacity (normal)                     │
│  Error shake:        Horizontal oscillation 3x (fast)              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7. Iconography

Use **Lucide Icons** (MIT licensed, consistent with modern React ecosystem):

```
Simulation States:      Agent Actions:          UI Elements:
────────────────       ──────────────          ────────────
Play         ▶        Speech     💬           Menu        ☰
Pause        ⏸        Thought    💭           Settings    ⚙
Stop         ⏹        Action     ⚡           Search      🔍
Step         ⏭        Memory     🧠           Filter      ⧉
Rewind       ⏮        Reflect    💡           Export      ↗

Status Indicators:     Network/Topology:        Data/Metrics:
─────────────────     ─────────────────        ─────────────
Running      ●        Mesh       ◇◇◇          Chart       📊
Paused       ◐        Hub-spoke  ✳            Cost        💰
Completed    ✓        Tree       🌳           Tokens      #
Error        ✕        Small-world 🕸           Time        🕐
```

### 8. Accessibility Requirements (WCAG 2.1 AA)

```
COLOR CONTRAST:
──────────────
- Normal text:  4.5:1 minimum (all text-slate-300+ on bg-slate-800)
- Large text:   3:1 minimum (headings, 18px+)
- UI elements:  3:1 minimum (borders, icons)

FOCUS STATES:
────────────
- Visible focus ring: 2px solid #6366F1 + 2px offset
- Focus-within for compound components
- Skip links for keyboard navigation

MOTION:
───────
- Respect prefers-reduced-motion
- No auto-playing animations > 5 seconds
- Pause controls for all animated content

ARIA:
─────
- Live regions for real-time updates (aria-live="polite")
- Role annotations for custom components
- Descriptive labels for all interactive elements
```

## Consequences

### Positive

- **Consistent visual language** across Web and CLI interfaces
- **Information density** appropriate for research workflows
- **Trait visualization** provides immediate personality recognition (ADR-004)
- **Accessibility compliance** ensures broad usability
- **Dark theme** reduces eye strain during extended sessions
- **Animation system** provides feedback without distraction

### Negative

- **Dark theme only** at launch (light theme deferred)
- **Custom component library** requires initial development investment
- **Strict color semantics** may limit future design flexibility

### Implementation Notes

1. **CSS Framework**: Use Tailwind CSS for utility classes matching this system
2. **Component Library**: Build with Radix UI primitives for accessibility
3. **Icon Set**: Lucide React for consistent iconography
4. **Animation**: Framer Motion for declarative animations
5. **Color Tokens**: Define as CSS custom properties for theme support

### Cross-References

| ADR | Relationship |
|-----|--------------|
| **ADR-002** | Max 50 agents informs visual density decisions |
| **ADR-004** | Trait vectors map to agent avatar colors |
| **ADR-006** | Memory importance maps to visual gradients |
| **ADR-007** | Establishes dual CLI/Web interface requirement |
| **ADR-012** | WebSocket events drive real-time visual updates |
| **UI-ADR-002** | Information architecture uses this design system |
| **UI-ADR-003** | Control interfaces styled per this system |
| **UI-ADR-004** | Visualizations use color and motion system |
| **UI-ADR-005** | CLI uses Rich library matching these colors |
| **UI-ADR-006** | Persona builder uses trait sliders, form validation |
| **UI-ADR-007** | Results analysis uses color system for visualizations |
| **UI-ADR-008** | Experiments UI uses elevation and component patterns |
