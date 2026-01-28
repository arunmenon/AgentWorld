/**
 * Tests for dual-control UI components (ADR-020.1).
 *
 * Test Suites:
 * 1. AccessTypeSelector (UI-01 to UI-06)
 * 2. RoleCheckboxes (UI-07 to UI-12)
 * 3. StateTypeSelector (UI-13 to UI-17)
 * 4. ToolTypeBadge and ToolTypeSelector (UI-18 to UI-23)
 * 5. RoleSelector and RoleBadge (UI-24 to UI-30)
 * 6. CoordinationMarker (UI-31 to UI-35)
 * 7. CoordinationPanel (UI-36 to UI-39)
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import { AccessTypeSelector, type AccessType } from '@/components/app-studio/access/AccessTypeSelector'
import { RoleCheckboxes, type AgentRole } from '@/components/app-studio/access/RoleCheckboxes'
import { StateTypeSelector, type StateType } from '@/components/app-studio/access/StateTypeSelector'
import { ToolTypeBadge, ToolTypeSelector, type ToolType } from '@/components/app-studio/ToolTypeBadge'
import { RoleSelector, RoleBadge } from '@/components/simulation/roles/RoleSelector'
import { CoordinationMarker, CoordinationMarkerCompact } from '@/components/simulation/timeline/CoordinationMarker'
import { CoordinationPanel, CoordinationSummary } from '@/components/simulation/timeline/CoordinationPanel'

// =============================================================================
// Test Suite 1: AccessTypeSelector (UI-01 to UI-06)
// =============================================================================

describe('AccessTypeSelector', () => {
  it('UI-01: renders with "shared" selected by default', () => {
    const onChange = vi.fn()
    render(<AccessTypeSelector value="shared" onChange={onChange} />)

    const sharedRadio = screen.getByLabelText(/shared \(default\)/i)
    expect(sharedRadio).toBeChecked()
  })

  it('UI-02: selecting SHARED triggers onChange', () => {
    const onChange = vi.fn()
    render(<AccessTypeSelector value="role_restricted" onChange={onChange} />)

    const sharedOption = screen.getByLabelText(/shared \(default\)/i)
    fireEvent.click(sharedOption)

    expect(onChange).toHaveBeenCalledWith('shared')
  })

  it('UI-03: selecting ROLE_RESTRICTED triggers onChange', () => {
    const onChange = vi.fn()
    render(<AccessTypeSelector value="shared" onChange={onChange} />)

    const roleRestrictedOption = screen.getByLabelText(/role-restricted/i)
    fireEvent.click(roleRestrictedOption)

    expect(onChange).toHaveBeenCalledWith('role_restricted')
  })

  it('UI-04: selecting PER_AGENT triggers onChange', () => {
    const onChange = vi.fn()
    render(<AccessTypeSelector value="shared" onChange={onChange} />)

    const perAgentOption = screen.getByLabelText(/per-agent instance/i)
    fireEvent.click(perAgentOption)

    expect(onChange).toHaveBeenCalledWith('per_agent')
  })

  it('UI-05: displays icons for each option', () => {
    const onChange = vi.fn()
    render(<AccessTypeSelector value="shared" onChange={onChange} />)

    // All three options should be visible
    expect(screen.getByText(/shared \(default\)/i)).toBeInTheDocument()
    expect(screen.getByText(/role-restricted/i)).toBeInTheDocument()
    expect(screen.getByText(/per-agent instance/i)).toBeInTheDocument()
  })

  it('UI-06: displays description text for each option', () => {
    const onChange = vi.fn()
    render(<AccessTypeSelector value="shared" onChange={onChange} />)

    expect(screen.getByText(/all agents in the simulation can access this app/i)).toBeInTheDocument()
    expect(screen.getByText(/only agents with specific roles can access/i)).toBeInTheDocument()
    expect(screen.getByText(/each agent gets their own isolated copy/i)).toBeInTheDocument()
  })
})

// =============================================================================
// Test Suite 2: RoleCheckboxes (UI-07 to UI-12)
// =============================================================================

describe('RoleCheckboxes', () => {
  it('UI-07: renders with empty selection', () => {
    const onChange = vi.fn()
    render(<RoleCheckboxes value={[]} onChange={onChange} />)

    const checkboxes = screen.getAllByRole('checkbox')
    checkboxes.forEach(checkbox => {
      expect(checkbox).not.toBeChecked()
    })
  })

  it('UI-08: checking SERVICE_AGENT adds role to array', () => {
    const onChange = vi.fn()
    render(<RoleCheckboxes value={[]} onChange={onChange} />)

    const serviceAgentCheckbox = screen.getByLabelText(/service agent/i)
    fireEvent.click(serviceAgentCheckbox)

    expect(onChange).toHaveBeenCalledWith(['service_agent'])
  })

  it('UI-09: checking CUSTOMER adds role to array', () => {
    const onChange = vi.fn()
    render(<RoleCheckboxes value={[]} onChange={onChange} />)

    const customerCheckbox = screen.getByLabelText(/customer/i)
    fireEvent.click(customerCheckbox)

    expect(onChange).toHaveBeenCalledWith(['customer'])
  })

  it('UI-10: checking PEER adds role to array', () => {
    const onChange = vi.fn()
    render(<RoleCheckboxes value={[]} onChange={onChange} />)

    const peerCheckbox = screen.getByLabelText(/peer/i)
    fireEvent.click(peerCheckbox)

    expect(onChange).toHaveBeenCalledWith(['peer'])
  })

  it('UI-11: multiple selections work correctly', () => {
    const onChange = vi.fn()
    render(<RoleCheckboxes value={['service_agent']} onChange={onChange} />)

    const customerCheckbox = screen.getByLabelText(/customer/i)
    fireEvent.click(customerCheckbox)

    expect(onChange).toHaveBeenCalledWith(['service_agent', 'customer'])
  })

  it('UI-12: unchecking role removes from array', () => {
    const onChange = vi.fn()
    render(<RoleCheckboxes value={['service_agent', 'customer']} onChange={onChange} />)

    const serviceAgentCheckbox = screen.getByLabelText(/service agent/i)
    fireEvent.click(serviceAgentCheckbox)

    expect(onChange).toHaveBeenCalledWith(['customer'])
  })
})

// =============================================================================
// Test Suite 3: StateTypeSelector (UI-13 to UI-17)
// =============================================================================

describe('StateTypeSelector', () => {
  it('UI-13: renders with "shared" selected by default', () => {
    const onChange = vi.fn()
    render(<StateTypeSelector value="shared" onChange={onChange} accessType="shared" />)

    const sharedRadio = screen.getByLabelText(/shared state/i)
    expect(sharedRadio).toBeChecked()
  })

  it('UI-14: selecting SHARED triggers onChange', () => {
    const onChange = vi.fn()
    render(<StateTypeSelector value="per_agent" onChange={onChange} accessType="shared" />)

    const sharedOption = screen.getByLabelText(/shared state/i)
    fireEvent.click(sharedOption)

    expect(onChange).toHaveBeenCalledWith('shared')
  })

  it('UI-15: selecting PER_AGENT triggers onChange', () => {
    const onChange = vi.fn()
    render(<StateTypeSelector value="shared" onChange={onChange} accessType="shared" />)

    const perAgentOption = screen.getByLabelText(/per-agent state/i)
    fireEvent.click(perAgentOption)

    expect(onChange).toHaveBeenCalledWith('per_agent')
  })

  it('UI-16: gating logic - shared option disabled when accessType is per_agent', () => {
    const onChange = vi.fn()
    render(<StateTypeSelector value="per_agent" onChange={onChange} accessType="per_agent" />)

    const sharedOption = screen.getByLabelText(/shared state/i)
    expect(sharedOption).toBeDisabled()
  })

  it('UI-17: forced selection - per_agent accessType forces per_agent state', () => {
    const onChange = vi.fn()
    render(<StateTypeSelector value="shared" onChange={onChange} accessType="per_agent" />)

    // Per-agent should be selected (forced)
    const perAgentOption = screen.getByLabelText(/per-agent state/i)
    expect(perAgentOption).toBeChecked()

    // Gating rule message should be visible
    expect(screen.getByText(/gating rule/i)).toBeInTheDocument()
  })
})

// =============================================================================
// Test Suite 4: ToolTypeBadge and ToolTypeSelector (UI-18 to UI-23)
// =============================================================================

describe('ToolTypeBadge', () => {
  it('UI-18: renders READ badge correctly', () => {
    render(<ToolTypeBadge type="read" />)

    expect(screen.getByText('READ')).toBeInTheDocument()
    expect(screen.getByTitle(/query only, no modifications/i)).toBeInTheDocument()
  })

  it('UI-19: renders WRITE badge correctly', () => {
    render(<ToolTypeBadge type="write" />)

    expect(screen.getByText('WRITE')).toBeInTheDocument()
    expect(screen.getByTitle(/modifies state/i)).toBeInTheDocument()
  })

  it('UI-20: applies correct color classes', () => {
    const { rerender } = render(<ToolTypeBadge type="read" />)

    let badge = screen.getByText('READ').parentElement
    expect(badge).toHaveClass('bg-blue-100')

    rerender(<ToolTypeBadge type="write" />)

    badge = screen.getByText('WRITE').parentElement
    expect(badge).toHaveClass('bg-orange-100')
  })
})

describe('ToolTypeSelector', () => {
  it('UI-21: selecting READ triggers onChange', () => {
    const onChange = vi.fn()
    render(<ToolTypeSelector value="write" onChange={onChange} />)

    const readOption = screen.getByRole('radio', { name: /read/i })
    fireEvent.click(readOption)

    expect(onChange).toHaveBeenCalledWith('read')
  })

  it('UI-22: selecting WRITE triggers onChange', () => {
    const onChange = vi.fn()
    render(<ToolTypeSelector value="read" onChange={onChange} />)

    const writeOption = screen.getByRole('radio', { name: /write/i })
    fireEvent.click(writeOption)

    expect(onChange).toHaveBeenCalledWith('write')
  })

  it('UI-23: displays descriptions for each option', () => {
    const onChange = vi.fn()
    render(<ToolTypeSelector value="write" onChange={onChange} />)

    expect(screen.getByText(/this action only queries\/reads data/i)).toBeInTheDocument()
    expect(screen.getByText(/this action creates, updates, or deletes data/i)).toBeInTheDocument()
  })
})

// =============================================================================
// Test Suite 5: RoleSelector and RoleBadge (UI-24 to UI-30)
// =============================================================================

describe('RoleSelector', () => {
  it('UI-24: renders dropdown correctly', () => {
    const onChange = vi.fn()
    render(<RoleSelector value="peer" onChange={onChange} showHelp={false} />)

    // Should show the selected role
    expect(screen.getByText(/peer \(default\)/i)).toBeInTheDocument()
  })

  it('UI-25: clicking opens dropdown and selecting changes value', async () => {
    const onChange = vi.fn()
    render(<RoleSelector value="peer" onChange={onChange} showHelp={false} />)

    // Click to open dropdown - get the button by its visible text
    const button = screen.getByRole('button')
    fireEvent.click(button)

    // Wait for dropdown and select service_agent
    const serviceAgentOption = await screen.findByText(/service agent/i)
    fireEvent.click(serviceAgentOption)

    expect(onChange).toHaveBeenCalledWith('service_agent')
  })

  it('UI-26: disabled prop works', () => {
    const onChange = vi.fn()
    render(<RoleSelector value="peer" onChange={onChange} disabled showHelp={false} />)

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })
})

describe('RoleBadge', () => {
  it('UI-27: SERVICE_AGENT renders with correct styling', () => {
    render(<RoleBadge role="service_agent" />)

    expect(screen.getByText(/service agent/i)).toBeInTheDocument()
    expect(screen.getByText('🎧')).toBeInTheDocument()
  })

  it('UI-28: CUSTOMER renders with correct styling', () => {
    render(<RoleBadge role="customer" />)

    expect(screen.getByText(/customer/i)).toBeInTheDocument()
    expect(screen.getByText('📱')).toBeInTheDocument()
  })

  it('UI-29: PEER renders with correct styling', () => {
    render(<RoleBadge role="peer" />)

    expect(screen.getByText(/peer/i)).toBeInTheDocument()
    expect(screen.getByText('👥')).toBeInTheDocument()
  })

  it('UI-30: size variants work correctly', () => {
    const { rerender } = render(<RoleBadge role="peer" size="sm" />)

    let badge = screen.getByText(/peer/i).parentElement
    expect(badge).toHaveClass('text-xs')

    rerender(<RoleBadge role="peer" size="md" />)

    badge = screen.getByText(/peer/i).parentElement
    expect(badge).toHaveClass('text-sm')
  })
})

// =============================================================================
// Test Suite 6: CoordinationMarker (UI-31 to UI-35)
// =============================================================================

describe('CoordinationMarker', () => {
  const defaultProps = {
    from: { id: 'agent_1', role: 'service_agent' as const },
    to: { id: 'customer_1', role: 'customer' as const },
    expectedAction: 'view_my_trips',
  }

  it('UI-31: success marker renders correctly', () => {
    render(<CoordinationMarker type="complete" {...defaultProps} />)

    expect(screen.getByText(/coordination complete/i)).toBeInTheDocument()
    expect(screen.getByText(/handoff successful/i)).toBeInTheDocument()
  })

  it('UI-32: failure marker renders correctly', () => {
    render(
      <CoordinationMarker
        type="failed"
        {...defaultProps}
        actualAction="wrong_action"
      />
    )

    expect(screen.getByText(/coordination failed/i)).toBeInTheDocument()
    expect(screen.getByText(/wrong action/i)).toBeInTheDocument()
  })

  it('UI-33: pending/requested marker renders correctly', () => {
    render(<CoordinationMarker type="requested" {...defaultProps} />)

    expect(screen.getByText(/coordination requested/i)).toBeInTheDocument()
    expect(screen.getByText(/awaiting response/i)).toBeInTheDocument()
  })

  it('UI-34: latency display shows turns', () => {
    render(<CoordinationMarker type="complete" {...defaultProps} latency={3} />)

    expect(screen.getByText(/3 turns/i)).toBeInTheDocument()
  })

  it('UI-35: expected action is displayed', () => {
    render(<CoordinationMarker type="requested" {...defaultProps} />)

    expect(screen.getByText(/view_my_trips/i)).toBeInTheDocument()
  })
})

describe('CoordinationMarkerCompact', () => {
  it('renders compact marker for different types', () => {
    const { rerender } = render(<CoordinationMarkerCompact type="complete" />)

    expect(screen.getByText('✅')).toBeInTheDocument()

    rerender(<CoordinationMarkerCompact type="failed" />)
    expect(screen.getByText('❌')).toBeInTheDocument()

    rerender(<CoordinationMarkerCompact type="requested" />)
    expect(screen.getByText('🎯')).toBeInTheDocument()
  })

  it('shows latency in compact format', () => {
    render(<CoordinationMarkerCompact type="complete" latency={2} />)

    expect(screen.getByText('(2t)')).toBeInTheDocument()
  })
})

// =============================================================================
// Test Suite 7: CoordinationPanel (UI-36 to UI-39)
// =============================================================================

describe('CoordinationPanel', () => {
  const defaultMetrics = {
    totalHandoffsRequired: 5,
    handoffsCompleted: 4,
    coordinationSuccessRate: 0.8,
    avgInstructionToActionTurns: 2.5,
    unnecessaryUserActions: 1,
    instructionClarityScore: 0.75,
    userConfusionCount: 2,
  }

  it('UI-36: displays all metrics', () => {
    render(<CoordinationPanel metrics={defaultMetrics} />)

    expect(screen.getByText(/coordination metrics/i)).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument() // Required
    expect(screen.getByText('4')).toBeInTheDocument() // Completed
  })

  it('UI-37: shows success rate as percentage', () => {
    render(<CoordinationPanel metrics={defaultMetrics} />)

    expect(screen.getByText('80%')).toBeInTheDocument()
  })

  it('UI-38: shows clarity scoring', () => {
    render(<CoordinationPanel metrics={defaultMetrics} />)

    expect(screen.getByText('75%')).toBeInTheDocument() // Clarity score
  })

  it('UI-39: handles undefined clarity score', () => {
    const metricsWithoutClarity = {
      ...defaultMetrics,
      instructionClarityScore: undefined,
    }

    render(<CoordinationPanel metrics={metricsWithoutClarity} />)

    expect(screen.getByText(/clarity scoring not available/i)).toBeInTheDocument()
  })
})

describe('CoordinationSummary', () => {
  it('displays compact summary', () => {
    const metrics = {
      totalHandoffsRequired: 3,
      handoffsCompleted: 2,
      coordinationSuccessRate: 0.67,
      avgInstructionToActionTurns: 1.5,
      unnecessaryUserActions: 0,
      userConfusionCount: 0,
    }

    render(<CoordinationSummary metrics={metrics} />)

    expect(screen.getByText('2/3')).toBeInTheDocument()
    expect(screen.getByText('67%')).toBeInTheDocument()
  })

  it('applies color coding based on success rate', () => {
    const highSuccessMetrics = {
      totalHandoffsRequired: 10,
      handoffsCompleted: 9,
      coordinationSuccessRate: 0.9,
      avgInstructionToActionTurns: 1.0,
      unnecessaryUserActions: 0,
      userConfusionCount: 0,
    }

    render(<CoordinationSummary metrics={highSuccessMetrics} />)

    const successText = screen.getByText('90%')
    expect(successText).toHaveClass('text-green-500')
  })
})
