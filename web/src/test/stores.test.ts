import { describe, it, expect, beforeEach } from 'vitest'
import { useUIStore } from '@/stores/uiStore'
import { useSimulationStore } from '@/stores/simulationStore'

describe('useUIStore', () => {
  beforeEach(() => {
    // Reset store state
    useUIStore.setState({
      sidebarCollapsed: false,
      theme: 'dark',
      simulationsViewMode: 'list',
      personasViewMode: 'grid',
      notifications: [],
    })
  })

  it('toggles sidebar', () => {
    const store = useUIStore.getState()
    expect(store.sidebarCollapsed).toBe(false)

    store.toggleSidebar()
    expect(useUIStore.getState().sidebarCollapsed).toBe(true)

    store.toggleSidebar()
    expect(useUIStore.getState().sidebarCollapsed).toBe(false)
  })

  it('sets theme', () => {
    const store = useUIStore.getState()
    store.setTheme('light')
    expect(useUIStore.getState().theme).toBe('light')
  })

  it('sets view modes', () => {
    const store = useUIStore.getState()
    store.setSimulationsViewMode('grid')
    expect(useUIStore.getState().simulationsViewMode).toBe('grid')

    store.setPersonasViewMode('list')
    expect(useUIStore.getState().personasViewMode).toBe('list')
  })

  it('manages notifications', () => {
    const store = useUIStore.getState()

    store.addNotification({
      type: 'success',
      title: 'Test notification',
      message: 'Test message',
    })

    expect(useUIStore.getState().notifications).toHaveLength(1)
    expect(useUIStore.getState().notifications[0].title).toBe('Test notification')

    const notificationId = useUIStore.getState().notifications[0].id
    store.removeNotification(notificationId)
    expect(useUIStore.getState().notifications).toHaveLength(0)
  })

  it('clears all notifications', () => {
    const store = useUIStore.getState()

    store.addNotification({ type: 'info', title: 'Test 1' })
    store.addNotification({ type: 'info', title: 'Test 2' })
    expect(useUIStore.getState().notifications).toHaveLength(2)

    store.clearNotifications()
    expect(useUIStore.getState().notifications).toHaveLength(0)
  })
})

describe('useSimulationStore', () => {
  beforeEach(() => {
    useSimulationStore.setState({
      socket: null,
      connected: false,
      connectionError: null,
      activeSimulationId: null,
      events: [],
    })
  })

  it('sets active simulation', () => {
    const store = useSimulationStore.getState()
    store.setActiveSimulation('sim-123')
    expect(useSimulationStore.getState().activeSimulationId).toBe('sim-123')
  })

  it('adds events', () => {
    const store = useSimulationStore.getState()
    store.addEvent({ type: 'test', data: 'value' })
    expect(useSimulationStore.getState().events).toHaveLength(1)
    expect(useSimulationStore.getState().events[0].type).toBe('test')
  })

  it('limits events to 100', () => {
    const store = useSimulationStore.getState()

    // Add 110 events
    for (let i = 0; i < 110; i++) {
      store.addEvent({ type: 'test', index: i })
    }

    expect(useSimulationStore.getState().events).toHaveLength(100)
  })

  it('clears events', () => {
    const store = useSimulationStore.getState()
    store.addEvent({ type: 'test' })
    store.addEvent({ type: 'test' })
    expect(useSimulationStore.getState().events).toHaveLength(2)

    store.clearEvents()
    expect(useSimulationStore.getState().events).toHaveLength(0)
  })
})
