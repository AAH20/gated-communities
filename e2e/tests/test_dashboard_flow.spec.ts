import { test, expect } from '@playwright/test';

test.describe('Dashboard Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display dashboard title', async ({ page }) => {
    const heading = page.getByRole('heading', { name: /dashboard/i });
    await expect(heading).toBeVisible();
  });

  test('should display stats cards', async ({ page }) => {
    const statsSection = page.locator('[data-testid="stats-section"], .stats-grid, .dashboard-stats');
    await expect(statsSection).toBeVisible();
  });

  test('should show community count stat', async ({ page }) => {
    const communityStat = page.locator('[data-testid="stat-communities"], .stat-card:has-text("Communities")');
    await expect(communityStat).toBeVisible();
    await expect(communityStat).toContainText(/\d+/);
  });

  test('should show posts count stat', async ({ page }) => {
    const postsStat = page.locator('[data-testid="stat-posts"], .stat-card:has-text("Posts")');
    await expect(postsStat).toBeVisible();
    await expect(postsStat).toContainText(/\d+/);
  });

  test('should navigate to communities page', async ({ page }) => {
    const navLink = page.getByRole('link', { name: /communities/i });
    await navLink.click();
    await expect(page).toHaveURL(/communities/);
  });

  test('should navigate to posts page', async ({ page }) => {
    const navLink = page.getByRole('link', { name: /Posts/i });
    await navLink.click();
    await expect(page).toHaveURL(/posts/);
  });

  test('should display recent activity section', async ({ page }) => {
    const activitySection = page.locator('[data-testid="recent-activity"], .activity-feed, .recent-activity');
    await expect(activitySection).toBeVisible();
  });

  test('should handle empty dashboard gracefully', async ({ page }) => {
    const emptyState = page.locator('[data-testid="empty-state"], .empty-state, .no-data');
    if (await emptyState.isVisible()) {
      await expect(emptyState).toContainText(/no data|empty|nothing here/i);
    }
  });

  test('should have working navigation menu', async ({ page }) => {
    const nav = page.locator('nav, [role="navigation"]');
    await expect(nav).toBeVisible();
    const navLinks = nav.getByRole('link');
    const count = await navLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display user profile or avatar', async ({ page }) => {
    const avatar = page.locator('[data-testid="user-avatar"], .avatar, .user-profile img');
    await expect(avatar).toBeVisible();
  });

  test('should handle dashboard load errors', async ({ page }) => {
    const errorBanner = page.locator('[data-testid="error-banner"], .error-message, .alert-error');
    if (await errorBanner.isVisible()) {
      await expect(errorBanner).toContainText(/error|failed|unable/i);
    }
  });
});
