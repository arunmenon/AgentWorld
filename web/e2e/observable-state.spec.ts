/**
 * E2E tests for Phase 1: Observable State Fields (τ²-bench)
 *
 * Tests the StateSchemaEditor component and observable toggle functionality
 * in the App Studio wizard.
 */

import { test, expect } from '@playwright/test'

test.describe('Observable State Fields (τ²-bench Phase 1)', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to App Studio
    await page.goto('/apps')
  })

  test('should display state schema editor when template has state fields', async ({ page }) => {
    // Click create new app
    await page.click('text=Create App')

    // Select Payment App template (has state fields with observable)
    await page.click('text=Payment App')

    // Go to Info step
    await page.click('text=Next')

    // Fill required fields
    await page.fill('input[id="name"]', 'Test Payment App')

    // Scroll down to see State Schema section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Wait for state schema section to appear (use first() for the heading)
    await expect(page.getByRole('heading', { name: 'State Schema' }).first()).toBeVisible()

    // Verify observable/hidden counts are shown
    await expect(page.locator('text=/\\d+ observable/').first()).toBeVisible()
    await expect(page.locator('text=/\\d+ hidden/').first()).toBeVisible()
  })

  test('should toggle field observability', async ({ page }) => {
    // Click create new app
    await page.click('text=Create App')

    // Select Payment App template
    await page.click('text=Payment App')

    // Go to Info step
    await page.click('text=Next')

    // Fill required fields
    await page.fill('input[id="name"]', 'Test Payment App')

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Find the first observable toggle (balance field should be observable)
    const firstToggle = page.locator('[data-testid="observable-toggle-0"]')
    await expect(firstToggle).toBeVisible()

    // The balance field should start as observable (eye icon visible)
    // Click to toggle it to hidden
    await firstToggle.click()

    // Verify the hidden indicator appears on the first field row
    await expect(page.locator('[data-testid="state-field-row-0"]').locator('text=Hidden from user agents')).toBeVisible()

    // Click again to toggle back to observable
    await firstToggle.click()

    // Hidden indicator should disappear from first field
    await expect(page.locator('[data-testid="state-field-row-0"]').locator('text=Hidden from user agents')).not.toBeVisible()
  })

  test('should show hidden field styling', async ({ page }) => {
    // Click create new app
    await page.click('text=Create App')

    // Select Payment App template
    await page.click('text=Payment App')

    // Go to Info step
    await page.click('text=Next')

    // Fill required fields
    await page.fill('input[id="name"]', 'Test Payment App')

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // The fraud_score field (index 2) should be hidden by default
    const hiddenFieldRow = page.locator('[data-testid="state-field-row-2"]')
    await expect(hiddenFieldRow).toBeVisible()

    // Verify it has the warning background styling (indicating hidden)
    // The hidden field should show the "Hidden from user agents" message
    const hiddenIndicator = hiddenFieldRow.locator('text=Hidden from user agents')
    await expect(hiddenIndicator).toBeVisible()
  })

  test.skip('should persist observable state through wizard navigation', async ({ page }) => {
    // TODO: Investigate state persistence issue when navigating back in wizard
    // Click create new app
    await page.click('text=Create App')

    // Select Payment App template
    await page.click('text=Payment App')

    // Go to Info step
    await page.click('text=Next')

    // Fill required fields
    await page.fill('input[id="name"]', 'Observable Persistence Test')

    // Scroll and find first toggle
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Wait for the state field row to be visible
    await expect(page.locator('[data-testid="state-field-row-0"]')).toBeVisible()

    // Toggle the balance field to hidden
    await page.click('[data-testid="observable-toggle-0"]')

    // Verify toggle worked before navigating
    await expect(page.locator('[data-testid="state-field-row-0"]').locator('text=Hidden from user agents')).toBeVisible()

    // Go to Actions step
    await page.click('text=Next')

    // Wait for Actions step to load
    await expect(page.getByRole('heading', { name: 'Actions' })).toBeVisible()

    // Go back to Info step
    await page.click('text=Back')

    // Wait a moment for navigation
    await page.waitForTimeout(500)

    // Scroll down again
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Wait for state field row to be visible again
    await expect(page.locator('[data-testid="state-field-row-0"]')).toBeVisible({ timeout: 10000 })

    // Verify the field is still hidden (hidden indicator should be visible)
    await expect(page.locator('[data-testid="state-field-row-0"]').locator('text=Hidden from user agents')).toBeVisible({ timeout: 10000 })
  })

  test('should add new state field with observable toggle', async ({ page }) => {
    // Click create new app
    await page.click('text=Create App')

    // Select Payment App template
    await page.click('text=Payment App')

    // Go to Info step
    await page.click('text=Next')

    // Fill required fields
    await page.fill('input[id="name"]', 'New Field Test')

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Count initial fields
    const initialCount = await page.locator('[data-testid^="state-field-row-"]').count()

    // Click Add State Field
    await page.click('text=Add State Field')

    // Verify new field was added
    const newCount = await page.locator('[data-testid^="state-field-row-"]').count()
    expect(newCount).toBe(initialCount + 1)

    // New field should have observable toggle
    const newFieldToggle = page.locator(`[data-testid="observable-toggle-${initialCount}"]`)
    await expect(newFieldToggle).toBeVisible()
  })

  test('should remove state field', async ({ page }) => {
    // Click create new app
    await page.click('text=Create App')

    // Select Payment App template
    await page.click('text=Payment App')

    // Go to Info step
    await page.click('text=Next')

    // Fill required fields
    await page.fill('input[id="name"]', 'Remove Field Test')

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Count initial fields
    const initialCount = await page.locator('[data-testid^="state-field-row-"]').count()

    // Click remove on first field
    await page.click('[data-testid="remove-field-0"]')

    // Verify field was removed
    const newCount = await page.locator('[data-testid^="state-field-row-"]').count()
    expect(newCount).toBe(initialCount - 1)
  })

  test('should edit field name', async ({ page }) => {
    // Click create new app
    await page.click('text=Create App')

    // Select Payment App template
    await page.click('text=Payment App')

    // Go to Info step
    await page.click('text=Next')

    // Fill required fields
    await page.fill('input[id="name"]', 'Edit Field Test')

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Edit first field name
    const nameInput = page.locator('[data-testid="field-name-0"]')
    await nameInput.clear()
    await nameInput.fill('custom_balance')

    // Verify the change
    await expect(nameInput).toHaveValue('custom_balance')
  })

  test('should display help text about observable fields', async ({ page }) => {
    // Click create new app
    await page.click('text=Create App')

    // Select Payment App template
    await page.click('text=Payment App')

    // Go to Info step
    await page.click('text=Next')

    // Fill required fields
    await page.fill('input[id="name"]', 'Help Text Test')

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // Verify help text is shown
    await expect(page.locator('text=Observable Fields (τ²-bench)')).toBeVisible()
    await expect(page.locator('text=/observable fields are what user agents can "see"/')).toBeVisible()
  })
})
