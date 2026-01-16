import { describe, it, expect } from 'vitest'
import { cn, formatNumber, formatCurrency, truncate, capitalize } from '@/lib/utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz')
  })

  it('merges tailwind classes correctly', () => {
    expect(cn('p-4', 'p-6')).toBe('p-6')
  })
})

describe('formatNumber', () => {
  it('formats numbers with commas', () => {
    expect(formatNumber(1000)).toBe('1,000')
    expect(formatNumber(1000000)).toBe('1,000,000')
  })
})

describe('formatCurrency', () => {
  it('formats currency values', () => {
    const result = formatCurrency(0.0001)
    expect(result).toContain('$')
    expect(result).toContain('0.0001')
  })
})

describe('truncate', () => {
  it('truncates long strings', () => {
    expect(truncate('Hello, World!', 5)).toBe('Hello...')
  })

  it('does not truncate short strings', () => {
    expect(truncate('Hi', 5)).toBe('Hi')
  })
})

describe('capitalize', () => {
  it('capitalizes first letter', () => {
    expect(capitalize('hello')).toBe('Hello')
    expect(capitalize('HELLO')).toBe('Hello')
  })
})
