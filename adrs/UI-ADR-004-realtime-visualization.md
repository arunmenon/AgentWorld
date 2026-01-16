# UI-ADR-004: Real-time Visualization

## Status
Accepted

## Dependencies
- **ADR-005**: Network Topology Architecture (topology types, NetworkX integration)
- **ADR-006**: Dual Memory Architecture (memory visualization requirements)
- **ADR-012**: API & WebSocket Event Schema (event types for real-time updates)
- **ADR-002**: Agent Scale (max 50 agents for visualization)
- **UI-ADR-001**: Design System (colors, animations, component specs)
- **UI-ADR-003**: Simulation Control (timeline integration)

## Context

AgentWorld simulations generate continuous streams of events that must be visualized in real-time:

1. **Agent activity**: Thinking, speaking, acting, reflecting
2. **Network communication**: Messages flowing between agents
3. **Memory evolution**: Observations accumulating, reflections generating
4. **Metrics updates**: Costs, token counts, message counts

### Visualization Requirements

| Aspect | Requirement | Technical Challenge |
|--------|-------------|---------------------|
| **Latency** | <100ms from event to visual | WebSocket + efficient rendering |
| **Throughput** | Handle 10+ events/second | Batching, virtualization |
| **Scale** | Up to 50 agents (ADR-002) | Force-directed layout performance |
| **Interactivity** | Click, hover, zoom, pan | Event delegation, canvas optimization |

### Framework Visualization Approaches (from ADR-001)

| Framework | Approach | Strengths | Limitations |
|-----------|----------|-----------|-------------|
| AI Town | 2D game canvas | Highly engaging | Limited data density |
| AgentSociety | D3.js dashboards | Good for metrics | Less agent-centric |
| TinyTroupe | Jupyter cells | Code-native | Not real-time |

## Decision

Implement a **multi-view real-time visualization system** using WebSocket events (ADR-012) and modern React rendering with D3.js for network graphs.

### 1. WebSocket Event to Visual Update Mapping

```
┌─────────────────────────────────────────────────────────────────────┐
│              WEBSOCKET EVENT → VISUAL UPDATE MAP                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Event Type           UI Component              Visual Response      │
│  ──────────────────────────────────────────────────────────────────│
│  agent_thinking       AgentNode, AgentCard      Pulsing animation   │
│  agent_spoke          ConversationStream        New message bubble  │
│  message_sent         TopologyGraph             Edge pulse animation│
│  memory_added         AgentInspector            Badge count update  │
│  reflection_gen       Timeline, Inspector       Marker + highlight  │
│  step_completed       Timeline, StatusBar       Marker advance      │
│  cost_updated         CostGauge                 Bar fill + color    │
│  simulation_paused    Timeline, Controls        State change        │
│  simulation_done      Global                    Completion banner   │
│  error_occurred       Toast, ErrorPanel         Error notification  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Network Topology Graph (Cross-ref: ADR-005)

```
┌─────────────────────────────────────────────────────────────────────┐
│                  TOPOLOGY VISUALIZATION                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │                    (Lisa)──────────(Bob)                    │   │
│  │                     /│╲              │╲                     │   │
│  │                    / │ ╲             │ ╲                    │   │
│  │                   /  │  ╲            │  ╲                   │   │
│  │              (Carol) │ (Dan)      (Eve)─(Frank)             │   │
│  │                   ╲  │  /                                   │   │
│  │                    ╲ │ /                                    │   │
│  │                    (Moderator)                              │   │
│  │                        ★                                    │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Node Visual States:                                                │
│  ───────────────────                                                │
│  ○ Idle          - Muted color, no animation                       │
│  ◐ Thinking      - Pulsing opacity (50%→100%→50%, 1s loop)        │
│  ● Speaking      - Full color + speech bubble icon                 │
│  ◉ Selected      - Ring highlight + scale 1.2x                     │
│  ○̲ Acting        - Double ring + lightning icon                    │
│                                                                     │
│  Edge Visual States:                                                │
│  ───────────────────                                                │
│  ─── Inactive    - Gray (#475569), 1px solid                       │
│  ─●─ Active      - Primary (#6366F1), animated dot traversal       │
│  ═══ High volume - Thicker stroke (2-4px based on message count)   │
│                                                                     │
│  Layout Algorithms (per ADR-005 topology type):                     │
│  ──────────────────────────────────────────────                    │
│  Mesh:        Force-directed (d3-force)                            │
│  Hub-spoke:   Radial layout with hub at center                     │
│  Hierarchical: Tree layout (d3-hierarchy)                          │
│  Small-world:  Force-directed with cluster detection               │
│  Scale-free:   Force-directed with degree-based node sizing        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. Topology Graph Component Specification

```typescript
interface TopologyGraphProps {
  // Data (from ADR-005)
  topology: TopologyType;  // mesh | hub_spoke | hierarchical | small_world | scale_free
  agents: Agent[];
  edges: Edge[];

  // Real-time updates (from ADR-012)
  activeAgent?: string;      // Currently thinking/speaking
  recentMessage?: Message;   // Animate edge pulse

  // Interaction
  selectedAgent?: string;
  onAgentSelect: (agentId: string) => void;
  onAgentHover: (agentId: string | null) => void;

  // Display options
  showLabels: boolean;
  showEdgeWeights: boolean;
  colorByTrait: 'openness' | 'extraversion' | 'none';  // ADR-004
}

// Visual configuration
const TOPOLOGY_CONFIG = {
  node: {
    radius: { min: 20, max: 40, default: 30 },
    colors: {
      idle: '#64748B',
      thinking: '#6366F1',
      speaking: '#22C55E',
      selected: '#FBBF24',
    },
  },
  edge: {
    stroke: { min: 1, max: 4 },
    colors: {
      inactive: '#475569',
      active: '#6366F1',
    },
    pulseSpeed: 300, // ms for dot to traverse edge
  },
  animation: {
    thinkingPulse: 1000,  // ms per cycle
    messageTravel: 300,    // ms for edge animation
    layoutTransition: 500, // ms for position changes
  },
};
```

### 4. Force-Directed Graph Implementation

```typescript
// Using react-force-graph or d3-force directly
import { ForceGraph2D } from 'react-force-graph';

function TopologyView({ topology, agents, edges, events }) {
  const graphRef = useRef();

  // Real-time event handling (Cross-ref: ADR-012)
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'agent_thinking':
          // Animate node pulse
          animateNodePulse(data.agent_id);
          break;

        case 'message_sent':
          // Animate edge with traveling dot
          animateEdge(data.sender_id, data.receiver_id);
          break;

        case 'agent_spoke':
          // Brief highlight then fade
          highlightNode(data.agent_id, 2000);
          break;
      }
    };
    return () => ws.close();
  }, []);

  // Node rendering with trait-based colors (ADR-004)
  const nodeCanvasObject = useCallback((node, ctx, scale) => {
    const agent = agents.find(a => a.id === node.id);
    const color = traitToColor(agent.traits);  // From UI-ADR-001

    // Draw node
    ctx.beginPath();
    ctx.arc(node.x, node.y, NODE_RADIUS, 0, 2 * Math.PI);
    ctx.fillStyle = node.isActive ? color : desaturate(color, 0.5);
    ctx.fill();

    // Draw thinking animation
    if (node.isThinking) {
      ctx.strokeStyle = '#6366F1';
      ctx.lineWidth = 3;
      ctx.globalAlpha = pulsingAlpha(Date.now());
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Draw label
    if (showLabels) {
      ctx.font = '12px Inter';
      ctx.fillStyle = '#F8FAFC';
      ctx.textAlign = 'center';
      ctx.fillText(agent.name, node.x, node.y + NODE_RADIUS + 15);
    }
  }, [agents, showLabels]);

  return (
    <ForceGraph2D
      ref={graphRef}
      graphData={{ nodes: agents, links: edges }}
      nodeCanvasObject={nodeCanvasObject}
      linkDirectionalParticles={2}  // Animated dots on edges
      linkDirectionalParticleSpeed={0.01}
      onNodeClick={handleNodeClick}
      onNodeHover={handleNodeHover}
      enableZoom={true}
      enablePan={true}
    />
  );
}
```

### 5. Conversation Stream Visualization

```
┌─────────────────────────────────────────────────────────────────────┐
│                  CONVERSATION STREAM                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  [Filter: All ▼] [Search: _______] [Group by: Time ▼]       │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                             │   │
│  │  ── Step 45 ──────────────────────────────── 10:23:01 ──   │   │
│  │                                                             │   │
│  │  ┌──────────────────────────────────────┐                  │   │
│  │  │ 🟣 Lisa                      10:23:01 │                  │   │
│  │  │ "I think the pricing model needs to   │                  │   │
│  │  │  account for different user tiers..." │                  │   │
│  │  └──────────────────────────────────────┘                  │   │
│  │                                                             │   │
│  │  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐                  │   │
│  │  │ 🔵 Bob                    💭 10:23:05 │                  │   │
│  │  │ Considering Lisa's point about       │                  │   │
│  │  │ pricing tiers and market segments... │                  │   │
│  │  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘                  │   │
│  │                                                             │   │
│  │  ┌══════════════════════════════════════┐                  │   │
│  │  │ 🔵 Bob                    ⚡ 10:23:08 │                  │   │
│  │  │ [Takes notes on pricing discussion]  │                  │   │
│  │  └══════════════════════════════════════┘                  │   │
│  │                                                             │   │
│  │  ── Step 46 ──────────────────────────────── 10:23:15 ──   │   │
│  │                                                             │   │
│  │  💉 Moderator Injection                                     │   │
│  │  "What about the enterprise segment?"                       │   │
│  │                                                             │   │
│  │  🟡 Carol is typing...                                      │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Virtualized Rendering (for performance):                           │
│  - Use react-window for list virtualization                        │
│  - Only render visible messages + 50 buffer                        │
│  - Smooth scroll with momentum                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6. Agent Inspector Panel (Cross-ref: ADR-004, ADR-006)

```
┌─────────────────────────────────────────────────────────────────────┐
│                  AGENT INSPECTOR                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │  ┌────┐   Lisa Chen                                         │   │
│  │  │ 🟣 │   Software Engineer                                 │   │
│  │  └────┘   "Tech-savvy, skeptical of marketing claims"       │   │
│  │                                                             │   │
│  │  Status: ● Speaking                                         │   │
│  │                                                             │   │
│  │  ┌──────────────────────────────────────────────────────┐  │   │
│  │  │ [Traits]  [Memory]  [Reasoning]  [Activity]          │  │   │
│  │  └──────────────────────────────────────────────────────┘  │   │
│  │                                                             │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                             │   │
│  │  TRAITS TAB (ADR-004):                                      │   │
│  │  ─────────────────────                                      │   │
│  │  Openness                                             0.85  │   │
│  │  ├────────────────────────────────────●────────────────┤   │   │
│  │  Practical                         Creative                 │   │
│  │                                                             │   │
│  │  Conscientiousness                                    0.72  │   │
│  │  ├──────────────────────────────●──────────────────────┤   │   │
│  │  Flexible                        Disciplined                │   │
│  │                                                             │   │
│  │  Extraversion                                         0.45  │   │
│  │  ├─────────────────────●───────────────────────────────┤   │   │
│  │  Reserved                        Outgoing                   │   │
│  │                                                             │   │
│  │  Agreeableness                                        0.68  │   │
│  │  ├────────────────────────────●────────────────────────┤   │   │
│  │  Competitive                     Cooperative                │   │
│  │                                                             │   │
│  │  Neuroticism                                          0.32  │   │
│  │  ├────────────●────────────────────────────────────────┤   │   │
│  │  Calm                            Anxious                    │   │
│  │                                                             │   │
│  │  Custom Traits:                                             │   │
│  │  ┌────────────────────────────────────────────────────┐    │   │
│  │  │ tech_savviness    ████████████████████░░  0.90    │    │   │
│  │  │ risk_tolerance    ████████░░░░░░░░░░░░░░  0.35    │    │   │
│  │  │ price_sensitivity ██████████████░░░░░░░░  0.65    │    │   │
│  │  └────────────────────────────────────────────────────┘    │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7. Memory Visualization (Cross-ref: ADR-006)

```
┌─────────────────────────────────────────────────────────────────────┐
│                  MEMORY TAB                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  [All ▼] [Observations: 34] [Reflections: 5]    🔍 Search   │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                             │   │
│  │  ⭐ REFLECTIONS (High-level insights)                       │   │
│  │  ────────────────────────────────                           │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │▌ "The team seems to prioritize cost over features   │   │   │
│  │  │  when evaluating new products."                     │   │   │
│  │  │                                                     │   │   │
│  │  │  💡 Importance: 9/10   🕐 5 min ago                  │   │   │
│  │  │  📎 Based on: 5 observations                        │   │   │
│  │  │  [View Source Memories] [View Reasoning]            │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │  📝 RECENT OBSERVATIONS                                     │   │
│  │  ─────────────────────────                                  │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │▌ "Bob mentioned budget constraints multiple times   │   │   │
│  │  │  during the pricing discussion."                    │   │   │
│  │  │  💡 7/10   🕐 2 min ago   📍 Focus Group             │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │▌ "Carol asked about enterprise pricing, suggesting  │   │   │
│  │  │  she's thinking about larger deployments."          │   │   │
│  │  │  💡 6/10   🕐 4 min ago   📍 Focus Group             │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │  [Load More...]                                             │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Importance Visualization:                                          │
│  ─────────────────────────                                          │
│  Border color gradient based on importance (1-10):                  │
│  1-3:  Gray (#64748B)    - Mundane                                 │
│  4-6:  Blue (#3B82F6)    - Notable                                 │
│  7-8:  Purple (#8B5CF6)  - Important                               │
│  9-10: Gold (#F59E0B)    - Critical                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8. Reasoning Trace Visualization (Cross-ref: ADR-015)

```
┌─────────────────────────────────────────────────────────────────────┐
│                  REASONING TAB                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Reasoning for Step 45    [Visibility: Full ▼]              │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                             │   │
│  │  1. CONTEXT RETRIEVED                                       │   │
│  │  ──────────────────────                                     │   │
│  │  ┌───────────────────────────────────────────────────┐     │   │
│  │  │ Memories retrieved (3):                           │     │   │
│  │  │ • "Bob mentioned budget constraints" (rel: 0.89)  │     │   │
│  │  │ • "Carol asked about enterprise" (rel: 0.76)      │     │   │
│  │  │ • "Team prioritizes cost" (rel: 0.72)             │     │   │
│  │  │                                                   │     │   │
│  │  │ Recent conversation (2 messages):                 │     │   │
│  │  │ • Bob: "The pricing seems high for SMBs"          │     │   │
│  │  │ • Carol: "What about volume discounts?"           │     │   │
│  │  └───────────────────────────────────────────────────┘     │   │
│  │                                                             │   │
│  │  2. PROMPT SENT                                             │   │
│  │  ──────────────                                             │   │
│  │  ┌───────────────────────────────────────────────────┐     │   │
│  │  │ You are Lisa, a Software Engineer with the        │     │   │
│  │  │ following personality traits:                     │     │   │
│  │  │ • High openness (0.85): Creative, curious         │     │   │
│  │  │ • Moderate conscientiousness (0.72)...            │     │   │
│  │  │                                                   │     │   │
│  │  │ [Expand Full Prompt]                              │     │   │
│  │  │                                                   │     │   │
│  │  │ 🔒 Some content redacted (API keys, system)       │     │   │
│  │  └───────────────────────────────────────────────────┘     │   │
│  │                                                             │   │
│  │  3. MODEL RESPONSE                                          │   │
│  │  ──────────────────                                         │   │
│  │  ┌───────────────────────────────────────────────────┐     │   │
│  │  │ Model: gpt-4o    Tokens: 234    Cost: $0.02       │     │   │
│  │  │ Latency: 1.2s    Temperature: 0.7                 │     │   │
│  │  │                                                   │     │   │
│  │  │ Response:                                         │     │   │
│  │  │ "I think the pricing model needs to account for   │     │   │
│  │  │  different user tiers. From my experience with    │     │   │
│  │  │  enterprise software, volume discounts are..."    │     │   │
│  │  └───────────────────────────────────────────────────┘     │   │
│  │                                                             │   │
│  │  [Copy Prompt] [Copy Response] [Export JSON]                │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9. Animation Specifications

```
┌─────────────────────────────────────────────────────────────────────┐
│                  ANIMATION LIBRARY                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  NODE ANIMATIONS                                                    │
│  ───────────────                                                    │
│  Thinking Pulse:                                                    │
│    - Opacity oscillation: 0.5 → 1.0 → 0.5                          │
│    - Duration: 1000ms per cycle                                     │
│    - Easing: ease-in-out                                            │
│    - CSS: animation: pulse 1s ease-in-out infinite                  │
│                                                                     │
│  Speaking Highlight:                                                │
│    - Scale: 1.0 → 1.1 → 1.0                                        │
│    - Ring appears and fades                                         │
│    - Duration: 300ms                                                │
│                                                                     │
│  Selection:                                                         │
│    - Scale: 1.0 → 1.15                                             │
│    - Ring stroke: 3px solid primary                                 │
│    - Duration: 150ms                                                │
│                                                                     │
│  EDGE ANIMATIONS                                                    │
│  ───────────────                                                    │
│  Message Pulse:                                                     │
│    - Particle/dot travels along edge                                │
│    - Duration: 300ms                                                │
│    - Color: primary (#6366F1)                                       │
│    - Size: 4px circle                                               │
│                                                                     │
│  Activity Glow:                                                     │
│    - Edge color transitions: muted → primary → muted               │
│    - Duration: 500ms                                                │
│                                                                     │
│  CONVERSATION ANIMATIONS                                            │
│  ───────────────────────                                            │
│  Message Entry:                                                     │
│    - Slide in from bottom                                           │
│    - Fade in opacity 0 → 1                                          │
│    - Duration: 200ms                                                │
│    - Easing: ease-out                                               │
│                                                                     │
│  Typing Indicator:                                                  │
│    - Three dots bouncing                                            │
│    - Duration: 1200ms per cycle                                     │
│    - Stagger: 100ms between dots                                    │
│                                                                     │
│  GLOBAL ANIMATIONS                                                  │
│  ─────────────────                                                  │
│  Step Transition:                                                   │
│    - Timeline marker slides to new position                         │
│    - Step counter increments with scale bounce                      │
│    - Duration: 150ms                                                │
│                                                                     │
│  Cost Warning:                                                      │
│    - Gauge color transitions                                        │
│    - Subtle shake animation at threshold                            │
│    - Toast notification slides in                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 10. Performance Optimizations

```typescript
// Performance strategies for real-time visualization

// 1. Event Batching
class EventBatcher {
  private buffer: Event[] = [];
  private flushInterval = 50; // ms

  push(event: Event) {
    this.buffer.push(event);
  }

  flush(): Event[] {
    const events = this.buffer;
    this.buffer = [];
    return events;
  }
}

// 2. Canvas Rendering for Graph
// Use Canvas instead of SVG for 50+ nodes
const useCanvasGraph = agents.length > 20;

// 3. Virtualized Lists
// react-window for conversation stream
<VariableSizeList
  height={600}
  itemCount={messages.length}
  itemSize={getMessageHeight}
  overscanCount={10}
>
  {MessageRow}
</VariableSizeList>

// 4. Memoization
const MemoizedNode = React.memo(AgentNode, (prev, next) => {
  return prev.agent.id === next.agent.id &&
         prev.isActive === next.isActive &&
         prev.isSelected === next.isSelected;
});

// 5. Web Worker for Graph Layout
// Offload force simulation to worker
const layoutWorker = new Worker('layout.worker.js');
layoutWorker.postMessage({ nodes, edges });
layoutWorker.onmessage = (e) => setPositions(e.data.positions);

// 6. Debounced Updates
const debouncedUpdate = useDebouncedCallback(
  (metrics) => updateMetrics(metrics),
  100  // Batch metric updates
);

// 7. Respect Reduced Motion
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

if (prefersReducedMotion) {
  // Disable animations, use instant transitions
}
```

### 11. Debug Mode

Debug mode provides enhanced visibility into simulation internals for developers and researchers troubleshooting agent behavior.

```
┌─────────────────────────────────────────────────────────────────────┐
│                  DEBUG MODE                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ACTIVATION:                                                        │
│  ───────────                                                        │
│  - Keyboard: Ctrl+Shift+D toggles debug mode                        │
│  - Settings: /settings/debug for persistent toggle                  │
│  - URL param: ?debug=true enables for session                       │
│  - CLI: agentworld run --debug                                      │
│                                                                     │
│  DEBUG INDICATOR:                                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  🔧 DEBUG MODE   │ All ▼ │ Collapse │              [× Exit] │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Orange banner at top of viewport when active                       │
│                                                                     │
│  DEBUG PANEL (collapsible bottom drawer):                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  [Event Log] [State Viewer] [Network] [Performance]          │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                              │   │
│  │  EVENT LOG TAB                                               │   │
│  │  ─────────────                                               │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ 10:23:01.234  ws:message_received  agent_thinking     │   │   │
│  │  │               {agent_id: "lisa_01", step: 45}         │   │   │
│  │  │                                                       │   │   │
│  │  │ 10:23:01.456  llm:request_sent     gpt-4o            │   │   │
│  │  │               {tokens: 1234, temperature: 0.7}        │   │   │
│  │  │                                                       │   │   │
│  │  │ 10:23:02.789  llm:response_received                  │   │   │
│  │  │               {tokens: 234, latency: 1.33s}           │   │   │
│  │  │                                                       │   │   │
│  │  │ 10:23:02.801  memory:added         observation        │   │   │
│  │  │               {importance: 7, agent: "lisa_01"}       │   │   │
│  │  │                                                       │   │   │
│  │  │ [Filter: All ▼] [Search: ___]  Auto-scroll: ☑        │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  │  STATE VIEWER TAB                                            │   │
│  │  ────────────────                                            │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ {                                                     │   │   │
│  │  │   "simulation": {                                     │   │   │
│  │  │     "id": "focus-group-42",                           │   │   │
│  │  │     "status": "running",                              │   │   │
│  │  │     "currentStep": 45,                                │   │   │
│  │  │     "agents": { ... }                                 │   │   │
│  │  │   },                                                  │   │   │
│  │  │   "ui": {                                             │   │   │
│  │  │     "selectedAgent": "lisa_01",                       │   │   │
│  │  │     "activePanel": "memory"                           │   │   │
│  │  │   }                                                   │   │   │
│  │  │ }                                                     │   │   │
│  │  │                                                       │   │   │
│  │  │ [Expand All] [Collapse All] [Copy State]              │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  │  NETWORK TAB                                                 │   │
│  │  ───────────                                                 │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ WS Status: ● Connected (latency: 23ms)                │   │   │
│  │  │ Messages/sec: 12    Reconnects: 0                     │   │   │
│  │  │                                                       │   │   │
│  │  │ Recent Messages:                                      │   │   │
│  │  │ ↓ agent_thinking     {agent_id: "lisa_01"}  45B      │   │   │
│  │  │ ↓ message_sent       {sender: "lisa_01"}    234B     │   │   │
│  │  │ ↑ stimulus_inject    {content: "..."}       128B     │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  │  PERFORMANCE TAB                                             │   │
│  │  ───────────────                                             │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │ FPS: 58    Render time: 12ms    Memory: 234MB        │   │   │
│  │  │                                                       │   │   │
│  │  │ Component Render Times:                               │   │   │
│  │  │ TopologyGraph:     8ms   ██████████████░░░░           │   │   │
│  │  │ ConversationList:  3ms   █████░░░░░░░░░░░░░           │   │   │
│  │  │ AgentInspector:    1ms   █░░░░░░░░░░░░░░░░░           │   │   │
│  │  │                                                       │   │   │
│  │  │ Event Processing:                                     │   │   │
│  │  │ Avg: 2.3ms   P95: 8ms   P99: 15ms                    │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ENHANCED NODE TOOLTIPS (debug mode only):                          │
│  ─────────────────────────────────────────                          │
│  ┌─────────────────────────────────────┐                           │
│  │ Agent: lisa_01                      │                           │
│  │ State: thinking                     │                           │
│  │ Memories: 34 obs / 5 refl           │                           │
│  │ Last action: 2.3s ago               │                           │
│  │ Pending LLM calls: 1                │                           │
│  │ Token usage: 12,450 / 100,000       │                           │
│  │                                      │                           │
│  │ [Copy Agent State]                   │                           │
│  └─────────────────────────────────────┘                           │
│                                                                     │
│  DEBUG KEYBOARD SHORTCUTS:                                          │
│  ─────────────────────────                                          │
│  Ctrl+Shift+D    Toggle debug mode                                  │
│  Ctrl+Shift+E    Export current state as JSON                       │
│  Ctrl+Shift+L    Copy last 100 events to clipboard                  │
│  Ctrl+Shift+P    Toggle performance overlay                         │
│  Ctrl+Shift+S    Step simulation forward (when paused)              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Debug Mode TypeScript Interface

```typescript
interface DebugState {
  enabled: boolean;
  activeTab: 'events' | 'state' | 'network' | 'performance';
  eventFilters: {
    types: EventType[];
    agents: string[];
    searchQuery: string;
  };
  autoScroll: boolean;
  performanceMetrics: {
    fps: number;
    renderTimeMs: number;
    memoryUsageMB: number;
    componentRenderTimes: Record<string, number>;
  };
}

interface DebugEvent {
  id: string;
  timestamp: Date;
  category: 'ws' | 'llm' | 'memory' | 'ui' | 'error';
  type: string;
  data: Record<string, unknown>;
  formattedTime: string;  // HH:mm:ss.SSS
}

// Debug mode provider
const DebugContext = createContext<{
  debugState: DebugState;
  toggleDebug: () => void;
  logEvent: (event: DebugEvent) => void;
  exportState: () => void;
} | null>(null);
```

### 12. State Management Architecture

Comprehensive state management strategy for the visualization layer.

```
┌─────────────────────────────────────────────────────────────────────┐
│                  STATE MANAGEMENT ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  STATE DOMAINS                                                      │
│  ─────────────                                                      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                              │   │
│  │   SERVER STATE           UI STATE              URL STATE     │   │
│  │   (React Query)          (Zustand)             (Router)      │   │
│  │   ─────────────          ────────              ─────────     │   │
│  │                                                              │   │
│  │   • Simulations          • Selected agent      • ?step=N     │   │
│  │   • Agents               • Active panel        • ?agent=ID   │   │
│  │   • Messages             • Panel collapsed     • ?panel=X    │   │
│  │   • Memories             • View mode           • ?view=MODE  │   │
│  │   • Metrics              • Zoom level          • ?debug=true │   │
│  │                          • Filter query                      │   │
│  │   Fetched from API       Local component       Shareable     │   │
│  │   Cached, invalidated    state, ephemeral      bookmarkable  │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  DATA FLOW                                                          │
│  ─────────                                                          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                                                               │ │
│  │   WebSocket ──────┐                                           │ │
│  │                   │                                           │ │
│  │                   ▼                                           │ │
│  │   ┌─────────────────────────────┐                            │ │
│  │   │     Event Processor         │                            │ │
│  │   │  (batching, deduplication)  │                            │ │
│  │   └─────────────────────────────┘                            │ │
│  │                   │                                           │ │
│  │       ┌───────────┼───────────┐                              │ │
│  │       ▼           ▼           ▼                              │ │
│  │   ┌───────┐  ┌─────────┐  ┌───────┐                         │ │
│  │   │Server │  │ UI      │  │ Debug │                         │ │
│  │   │State  │  │ State   │  │ Log   │                         │ │
│  │   │Store  │  │ Store   │  │       │                         │ │
│  │   └───┬───┘  └────┬────┘  └───────┘                         │ │
│  │       │           │                                          │ │
│  │       └─────┬─────┘                                          │ │
│  │             ▼                                                │ │
│  │   ┌─────────────────────────────┐                            │ │
│  │   │      React Components       │                            │ │
│  │   │  (TopologyGraph, Stream,    │                            │ │
│  │   │   Inspector, Timeline)      │                            │ │
│  │   └─────────────────────────────┘                            │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### State Store Implementations

```typescript
// ============================================
// 1. SERVER STATE (React Query)
// ============================================
// For data that comes from the API and needs caching

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Simulation data
export function useSimulation(simId: string) {
  return useQuery({
    queryKey: ['simulation', simId],
    queryFn: () => api.getSimulation(simId),
    staleTime: 1000,  // Consider fresh for 1s
    refetchOnWindowFocus: false,  // WS keeps it updated
  });
}

// Agent data with real-time updates
export function useAgent(simId: string, agentId: string) {
  const queryClient = useQueryClient();

  // WebSocket updates invalidate cache
  useEffect(() => {
    const ws = connectWebSocket(simId);
    ws.on('agent_updated', (data) => {
      if (data.agent_id === agentId) {
        queryClient.setQueryData(
          ['agent', simId, agentId],
          (old) => ({ ...old, ...data })
        );
      }
    });
    return () => ws.disconnect();
  }, [simId, agentId]);

  return useQuery({
    queryKey: ['agent', simId, agentId],
    queryFn: () => api.getAgent(simId, agentId),
  });
}

// Messages with pagination
export function useMessages(simId: string, step?: number) {
  return useInfiniteQuery({
    queryKey: ['messages', simId, { step }],
    queryFn: ({ pageParam = 0 }) =>
      api.getMessages(simId, { step, offset: pageParam }),
    getNextPageParam: (lastPage) => lastPage.nextOffset,
  });
}

// ============================================
// 2. UI STATE (Zustand)
// ============================================
// For ephemeral UI state that doesn't need to persist

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

interface UIState {
  // Selection
  selectedAgentId: string | null;
  activePanel: 'traits' | 'memory' | 'reasoning' | 'activity' | null;

  // Panel visibility
  leftPanelCollapsed: boolean;
  rightPanelCollapsed: boolean;

  // View options
  viewMode: 'topology' | 'conversation' | 'split' | 'analysis';
  showLabels: boolean;
  colorByTrait: 'openness' | 'extraversion' | 'none';

  // Graph state
  zoomLevel: number;
  panPosition: { x: number; y: number };

  // Filters
  filterQuery: string;
  filterAgents: string[];

  // Actions
  selectAgent: (id: string | null) => void;
  setActivePanel: (panel: UIState['activePanel']) => void;
  toggleLeftPanel: () => void;
  toggleRightPanel: () => void;
  setViewMode: (mode: UIState['viewMode']) => void;
  setZoom: (level: number) => void;
  setFilter: (query: string) => void;
}

export const useUIStore = create<UIState>()(
  subscribeWithSelector((set) => ({
    // Initial state
    selectedAgentId: null,
    activePanel: null,
    leftPanelCollapsed: false,
    rightPanelCollapsed: false,
    viewMode: 'topology',
    showLabels: true,
    colorByTrait: 'none',
    zoomLevel: 1,
    panPosition: { x: 0, y: 0 },
    filterQuery: '',
    filterAgents: [],

    // Actions
    selectAgent: (id) => set({ selectedAgentId: id }),
    setActivePanel: (panel) => set({ activePanel: panel }),
    toggleLeftPanel: () => set((s) => ({ leftPanelCollapsed: !s.leftPanelCollapsed })),
    toggleRightPanel: () => set((s) => ({ rightPanelCollapsed: !s.rightPanelCollapsed })),
    setViewMode: (mode) => set({ viewMode: mode }),
    setZoom: (level) => set({ zoomLevel: level }),
    setFilter: (query) => set({ filterQuery: query }),
  }))
);

// ============================================
// 3. URL STATE SYNC
// ============================================
// Sync specific UI state with URL for sharing/bookmarking

import { useSearchParams } from 'react-router-dom';

export function useURLSyncedState() {
  const [searchParams, setSearchParams] = useSearchParams();
  const uiStore = useUIStore();

  // Parse URL params on mount
  useEffect(() => {
    const step = searchParams.get('step');
    const agent = searchParams.get('agent');
    const panel = searchParams.get('panel');
    const debug = searchParams.get('debug');

    if (agent) uiStore.selectAgent(agent);
    if (panel) uiStore.setActivePanel(panel as UIState['activePanel']);
    // ... other params
  }, []);

  // Update URL when relevant state changes
  useEffect(() => {
    const updates: Record<string, string> = {};

    if (uiStore.selectedAgentId) {
      updates.agent = uiStore.selectedAgentId;
    }
    if (uiStore.activePanel) {
      updates.panel = uiStore.activePanel;
    }

    setSearchParams(updates, { replace: true });
  }, [uiStore.selectedAgentId, uiStore.activePanel]);
}

// ============================================
// 4. REAL-TIME STATE (WebSocket)
// ============================================
// Handle incoming events and update appropriate stores

interface RealtimeState {
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastEventTime: Date | null;
  activeAgents: Set<string>;
  thinkingAgents: Set<string>;
}

export const useRealtimeStore = create<RealtimeState>((set) => ({
  connectionStatus: 'connecting',
  lastEventTime: null,
  activeAgents: new Set(),
  thinkingAgents: new Set(),
}));

// WebSocket event processor
class EventProcessor {
  private queryClient: QueryClient;
  private eventBuffer: Event[] = [];
  private flushTimeout: number | null = null;

  constructor(queryClient: QueryClient) {
    this.queryClient = queryClient;
  }

  process(event: WebSocketEvent) {
    // Buffer events for batch processing
    this.eventBuffer.push(event);

    if (!this.flushTimeout) {
      this.flushTimeout = window.setTimeout(() => {
        this.flush();
        this.flushTimeout = null;
      }, 50);  // 50ms batching window
    }
  }

  private flush() {
    const events = this.eventBuffer;
    this.eventBuffer = [];

    // Group by type for efficient updates
    const byType = groupBy(events, 'type');

    // Update server state (React Query)
    if (byType.agent_updated) {
      byType.agent_updated.forEach((e) => {
        this.queryClient.setQueryData(
          ['agent', e.simulation_id, e.agent_id],
          (old) => ({ ...old, ...e.data })
        );
      });
    }

    if (byType.message_sent) {
      byType.message_sent.forEach((e) => {
        this.queryClient.setQueryData(
          ['messages', e.simulation_id],
          (old) => addMessage(old, e.data)
        );
      });
    }

    // Update realtime state (Zustand)
    const thinkingAgents = new Set(
      byType.agent_thinking?.map((e) => e.agent_id) ?? []
    );
    useRealtimeStore.setState({ thinkingAgents });
  }
}
```

#### State Management Guidelines

```
┌─────────────────────────────────────────────────────────────────────┐
│                  STATE MANAGEMENT RULES                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  WHEN TO USE EACH STORE:                                            │
│  ────────────────────────                                           │
│                                                                     │
│  Use React Query (Server State) when:                               │
│  • Data comes from API endpoints                                    │
│  • Data needs to be cached across components                        │
│  • Data needs to be refetched/invalidated                          │
│  • Data is shared across multiple components                        │
│  Examples: Simulations, agents, messages, memories, metrics        │
│                                                                     │
│  Use Zustand (UI State) when:                                       │
│  • State is purely UI-related (selections, toggles)                 │
│  • State doesn't persist across sessions                            │
│  • State needs to be accessed outside React tree                    │
│  • State changes frequently (zoom, pan, filters)                    │
│  Examples: Selected agent, panel visibility, zoom level            │
│                                                                     │
│  Use URL State when:                                                │
│  • State should be shareable via URL                                │
│  • State should survive page refresh                                │
│  • State represents a "location" in the app                         │
│  Examples: Current step, selected agent, active view               │
│                                                                     │
│  Use Local Component State (useState) when:                         │
│  • State is only used by single component                           │
│  • State is truly transient (hover, focus)                         │
│  • State doesn't need to be observed by other components           │
│  Examples: Dropdown open, tooltip visible, input value             │
│                                                                     │
│  ANTI-PATTERNS TO AVOID:                                            │
│  ────────────────────────                                           │
│                                                                     │
│  ❌ Storing server data in Zustand (use React Query)               │
│  ❌ Syncing all state to URL (only shareable state)                │
│  ❌ Creating derived state stores (compute in selectors)           │
│  ❌ Mutating state directly (always use actions)                   │
│  ❌ Over-normalizing UI state (keep it simple)                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 13. Responsive Visualization

```
┌─────────────────────────────────────────────────────────────────────┐
│                  RESPONSIVE BREAKPOINTS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Desktop Large (≥1440px):                                           │
│  ─────────────────────────                                          │
│  - Full topology graph with labels                                  │
│  - Conversation and inspector side-by-side                          │
│  - All timeline controls visible                                    │
│                                                                     │
│  Desktop (1024-1439px):                                             │
│  ─────────────────────                                              │
│  - Topology graph (labels on hover only)                            │
│  - Collapsible side panels                                          │
│  - Condensed timeline                                               │
│                                                                     │
│  Tablet (768-1023px):                                               │
│  ────────────────────                                               │
│  - Swipeable views (topology ↔ conversation)                       │
│  - Bottom sheet inspector                                           │
│  - Simplified timeline                                              │
│                                                                     │
│  Mobile (<768px):                                                   │
│  ────────────────                                                   │
│  - Conversation view primary (no topology)                          │
│  - Agent list as horizontal scroll                                  │
│  - Minimal controls (play/pause, step)                              │
│  - Full-screen inspector on tap                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Consequences

### Positive

- **Real-time feedback** keeps users engaged during simulation
- **Multiple views** support different analysis modes
- **Rich agent inspection** enables deep behavioral analysis
- **Memory visualization** makes ADR-006 system observable
- **Reasoning traces** provide transparency (ADR-015)
- **Performance optimizations** handle max 50 agents smoothly

### Negative

- **WebSocket dependency** requires stable connection
- **Canvas rendering** sacrifices some accessibility
- **Animation complexity** needs careful reduced-motion handling
- **Multiple view states** increase testing surface

### Implementation Stack

```
Visualization:
- react-force-graph (D3-force based)
- Framer Motion (animations)
- react-window (virtualization)

State:
- Zustand (local UI state)
- React Query (server state)

WebSocket:
- Native WebSocket or socket.io-client
- Reconnection logic with exponential backoff
```

### Cross-References

| ADR | Relationship |
|-----|--------------|
| **ADR-002** | Max 50 agents informs graph performance budget |
| **ADR-004** | Trait vectors displayed in inspector, node colors |
| **ADR-005** | Topology types determine graph layout algorithms |
| **ADR-006** | Memory system visualized in inspector panel |
| **ADR-012** | WebSocket events drive all real-time updates |
| **ADR-015** | Reasoning visibility integrated in inspector |
| **UI-ADR-001** | Color palette, animations, component styling |
| **UI-ADR-002** | View modes, panel layout, empty states |
| **UI-ADR-003** | Timeline control integration |
| **UI-ADR-005** | CLI provides text-based alternative |
| **UI-ADR-006** | Persona library visualization |
| **UI-ADR-007** | Results analysis uses visualization patterns |
| **UI-ADR-008** | Experiment comparison views |
