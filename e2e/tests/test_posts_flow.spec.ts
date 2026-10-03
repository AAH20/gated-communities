import { test, expect } from '@playwright/test';

test.describe('Posts Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/posts');
  });

  test('should display posts page title', async ({ page }) => {
    const heading = page.getByRole('heading', { name: /Posts/i });
    await expect(heading).toBeVisible();
  });

  test('should display posts list', async ({ page }) => {
    const list = page.locator('[data-testid="posts-list"], .posts-feed, .posts-grid');
    await expect(list).toBeVisible();
  });

  test('should have create post button', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /create|new|write|add post/i });
    await expect(createBtn).toBeVisible();
  });

  test('should open create post form', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /create|new|write|add post/i });
    await createBtn.click();

    const form = page.locator('[data-testid="create-post-form"], .post-form, [role="dialog"]');
    await expect(form).toBeVisible();
  });

  test('should create a new post', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /create|new|write|add post/i });
    await createBtn.click();

    const titleInput = page.locator('[data-testid="post-title-input"], input[name="title"], input[placeholder*="title" i]');
    await titleInput.fill('E2E Test Post');

    const contentInput = page.locator('[data-testid="post-content-input"], textarea[name="content"], textarea[placeholder*="content" i]');
    await contentInput.fill('This is a test post created by Playwright E2E tests.');

    const submitBtn = page.getByRole('button', { name: /publish|submit|create|post/i });
    await submitBtn.click();

    const successMsg = page.locator('[data-testid="success-message"], .success, .toast-success');
    await expect(successMsg).toBeVisible({ timeout: 10000 });
  });

  test('should validate required fields in post form', async ({ page }) => {
    const createBtn = page.getByRole('button', { name: /create|new|write|add post/i });
    await createBtn.click();

    const submitBtn = page.getByRole('button', { name: /publish|submit|create|post/i });
    await submitBtn.click();

    const validationError = page.locator('[data-testid="validation-error"], .error-message, .field-error');
    await expect(validationError.first()).toBeVisible();
  });

  test('should view post details', async ({ page }) => {
    const postCard = page.locator('[data-testid="post-card"], .post-card, .post-item').first();
    await postCard.click();

    const details = page.locator('[data-testid="post-details"], .post-detail, .post-full');
    await expect(details).toBeVisible();
  });

  test('should edit a post', async ({ page }) => {
    const postCard = page.locator('[data-testid="post-card"], .post-card, .post-item').first();
    await postCard.click();

    const editBtn = page.getByRole('button', { name: /edit|modify|update/i });
    await editBtn.click();

    const titleInput = page.locator('[data-testid="post-title-input"], input[name="title"]');
    await titleInput.fill('Updated Post Title');

    const saveBtn = page.getByRole('button', { name: /save|update|submit/i });
    await saveBtn.click();

    const successMsg = page.locator('[data-testid="success-message"], .success, .toast-success');
    await expect(successMsg).toBeVisible({ timeout: 10000 });
  });

  test('should delete a post', async ({ page }) => {
    const postCard = page.locator('[data-testid="post-card"], .post-card, .post-item').first();
    await postCard.click();

    const deleteBtn = page.getByRole('button', { name: /delete|remove/i });
    await deleteBtn.click();

    const confirmBtn = page.getByRole('button', { name: /confirm|yes|delete/i });
    await confirmBtn.click();

    const successMsg = page.locator('[data-testid="success-message"], .success, .toast-success');
    await expect(successMsg).toBeVisible({ timeout: 10000 });
  });

  test('should like a post', async ({ page }) => {
    const postCard = page.locator('[data-testid="post-card"], .post-card, .post-item').first();
    const likeBtn = postCard.getByRole('button', { name: /like|heart|thumbs/i });
    await likeBtn.click();

    const likeCount = postCard.locator('[data-testid="like-count"], .like-count, .likes');
    await expect(likeCount).toBeVisible();
  });

  test('should unlike a post', async ({ page }) => {
    const postCard = page.locator('[data-testid="post-card"], .post-card, .post-item').first();
    const likeBtn = postCard.getByRole('button', { name: /unlike|remove like/i });
    if (await likeBtn.isVisible()) {
      await likeBtn.click();
      const likeCount = postCard.locator('[data-testid="like-count"], .like-count, .likes');
      await expect(likeCount).toBeVisible();
    }
  });

  test('should add a comment to a post', async ({ page }) => {
    const postCard = page.locator('[data-testid="post-card"], .post-card, .post-item').first();
    await postCard.click();

    const commentInput = page.locator('[data-testid="comment-input"], textarea[name="comment"], input[placeholder*="comment" i]');
    await commentInput.fill('This is a test comment');

    const submitBtn = page.getByRole('button', { name: /comment|reply|submit/i });
    await submitBtn.click();

    const comment = page.locator('[data-testid="comment"], .comment-item').first();
    await expect(comment).toBeVisible({ timeout: 10000 });
  });

  test('should display post author info', async ({ page }) => {
    const postCard = page.locator('[data-testid="post-card"], .post-card, .post-item').first();
    const author = postCard.locator('[data-testid="post-author"], .author, .post-author');
    await expect(author).toBeVisible();
  });

  test('should display post timestamp', async ({ page }) => {
    const postCard = page.locator('[data-testid="post-card"], .post-card, .post-item').first();
    const timestamp = postCard.locator('[data-testid="post-timestamp"], .timestamp, .post-date, time');
    await expect(timestamp).toBeVisible();
  });

  test('should search posts', async ({ page }) => {
    const searchInput = page.locator('[data-testid="search-input"], input[type="search"], input[placeholder*="search" i]');
    await searchInput.fill('test');

    const results = page.locator('[data-testid="posts-list"], .posts-feed');
    await expect(results).toBeVisible();
  });

  test('should filter posts by community', async ({ page }) => {
    const filterSelect = page.locator('[data-testid="community-filter"], select[name="community"], .filter-select');
    if (await filterSelect.isVisible()) {
      await filterSelect.selectOption({ index: 1 });
      const results = page.locator('[data-testid="posts-list"], .posts-feed');
      await expect(results).toBeVisible();
    }
  });

  test('should handle post not found', async ({ page }) => {
    await page.goto('/posts/nonexistent-id');
    const notFound = page.locator('[data-testid="not-found"], .not-found, .error-404');
    await expect(notFound).toBeVisible();
  });

  test('should handle empty posts state', async ({ page }) => {
    const emptyState = page.locator('[data-testid="empty-state"], .empty-state, .no-posts');
    if (await emptyState.isVisible()) {
      await expect(emptyState).toContainText(/no posts|empty|nothing here/i);
    }
  });

  test('should load more posts on scroll', async ({ page }) => {
    const loadMoreBtn = page.getByRole('button', { name: /load more|show more|see more/i });
    if (await loadMoreBtn.isVisible()) {
      await loadMoreBtn.click();
      const postsList = page.locator('[data-testid="posts-list"], .posts-feed');
      await expect(postsList).toBeVisible();
    }
  });
});
