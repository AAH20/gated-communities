import { test, expect } from '@playwright/test';

test.describe('Communities Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/communities');
  });

  test('should display communities page title', async ({ page }) => {
    const heading = page.getByRole('heading', { name: /communities/i });
    await expect(heading).toBeVisible();
  });

  test('should display communities list', async ({ page }) => {
    const list = page.locator('[data-testid="communities-list"], .communities-grid, .community-list');
    await expect(list).toBeVisible();
  });

  test('should have create community button', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /create|new|add community/i });
    await expect(createBtn).toBeVisible();
  });

  test('should open create community modal', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /create|new|add community/i });
    await createBtn.click();
    const modal = page.locator('[data-testid="create-community-modal"], .modal, [role="dialog"]');
    await expect(modal).toBeVisible();
  });

  test('should create a new community', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /create|new|add community/i });
    await createBtn.click();

    const nameInput = page.locator('[data-testid="community-name-input"], input[name="name"], input[placeholder*="name" i]');
    await nameInput.fill('Test Community');

    const descInput = page.locator('[data-testid="community-description-input"], textarea[name="description"], textarea[placeholder*="description" i]');
    await descInput.fill('A test community for E2E testing');

    const submitBtn = page.getByRole('button', { name: /create|submit|save/i });
    await submitBtn.click();

    const successMsg = page.locator('[data-testid="success-message"], .success, .toast-success');
    await expect(successMsg).toBeVisible({ timeout: 10000 });
  });

  test('should validate required fields in create form', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /create|new|add community/i });
    await createBtn.click();

    const submitBtn = page.getByRole('button', { name: /create|submit|save/i });
    await submitBtn.click();

    const validationError = page.locator('[data-testid="validation-error"], .error-message, .field-error');
    await expect(validationError.first()).toBeVisible();
  });

  test('should view community details', async ({ page }) => {
    const communityCard = page.locator('[data-testid="community-card"], .community-card, .community-item').first();
    await communityCard.click();

    const details = page.locator('[data-testid="community-details"], .community-detail, .community-profile');
    await expect(details).toBeVisible();
  });

  test('should edit a community', async ({ page }) => {
    const communityCard = page.locator('[data-testid="community-card"], .community-card, .community-item').first();
    await communityCard.click();

    const editBtn = page.getByRole('button', { name: /edit|modify|update/i });
    await editBtn.click();

    const nameInput = page.locator('[data-testid="community-name-input"], input[name="name"]');
    await nameInput.fill('Updated Community Name');

    const saveBtn = page.getByRole('button', { name: /save|update|submit/i });
    await saveBtn.click();

    const successMsg = page.locator('[data-testid="success-message"], .success, .toast-success');
    await expect(successMsg).toBeVisible({ timeout: 10000 });
  });

  test('should delete a community', async ({ page }) => {
    const communityCard = page.locator('[data-testid="community-card"], .community-card, .community-item').first();
    await communityCard.click();

    const deleteBtn = page.getByRole('button', { name: /delete|remove/i });
    await deleteBtn.click();

    const confirmBtn = page.getByRole('button', { name: /confirm|yes|delete/i });
    await confirmBtn.click();

    const successMsg = page.locator('[data-testid="success-message"], .success, .toast-success');
    await expect(successMsg).toBeVisible({ timeout: 10000 });
  });

  test('should cancel community deletion', async ({ page }) => {
    const communityCard = page.locator('[data-testid="community-card"], .community-card, .community-item').first();
    await communityCard.click();

    const deleteBtn = page.getByRole('button', { name: /delete|remove/i });
    await deleteBtn.click();

    const cancelBtn = page.getByRole('button', { name: /cancel|no/i });
    await cancelBtn.click();

    const details = page.locator('[data-testid="community-details"], .community-detail');
    await expect(details).toBeVisible();
  });

  test('should search communities', async ({ page }) => {
    const searchInput = page.locator('[data-testid="search-input"], input[type="search"], input[placeholder*="search" i]');
    await searchInput.fill('test');

    const results = page.locator('[data-testid="communities-list"], .communities-grid');
    await expect(results).toBeVisible();
  });

  test('should handle community not found', async ({ page }) => {
    await page.goto('/communities/nonexistent-id');
    const notFound = page.locator('[data-testid="not-found"], .not-found, .error-404');
    await expect(notFound).toBeVisible();
  });

  test('should join a community', async ({ page }) => {
    const communityCard = page.locator('[data-testid="community-card"], .community-card, .community-item').first();
    await communityCard.click();

    const joinBtn = page.getByRole('button', { name: /join|become member/i });
    await joinBtn.click();

    const successMsg = page.locator('[data-testid="success-message"], .success, .toast-success');
    await expect(successMsg).toBeVisible({ timeout: 10000 });
  });

  test('should leave a community', async ({ page }) => {
    const communityCard = page.locator('[data-testid="community-card"], .community-card, .community-item').first();
    await communityCard.click();

    const leaveBtn = page.getByRole('button', { name: /leave|exit/i });
    await leaveBtn.click();

    const confirmBtn = page.getByRole('button', { name: /confirm|yes|leave/i });
    await confirmBtn.click();

    const successMsg = page.locator('[data-testid="success-message"], .success, .toast-success');
    await expect(successMsg).toBeVisible({ timeout: 10000 });
  });
});
