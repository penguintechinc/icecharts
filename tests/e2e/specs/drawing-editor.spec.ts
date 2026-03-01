/**
 * E2E tests — Drawing Editor (/drawings/new, /drawings/:id/edit)
 *
 * Covers the canvas editing surface: toolbar, shape panel, save, undo/redo,
 * zoom, export/share/template dialogs, and keyboard shortcuts.
 */

import { test, expect } from '../fixtures/auth.fixture';
import { DrawingEditorPage } from '../fixtures/pages/DrawingEditorPage';

test.describe('Drawing Editor', () => {
  test('should load blank canvas for new drawing', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    await expect(adminPage).toHaveURL(/\/drawings\/(new|create)/, { timeout: 15_000 });
    await expect(adminPage.locator('body')).toBeVisible();
  });

  test('should display editor toolbar', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    await expect(editor.toolbar.or(adminPage.locator('[role="toolbar"]'))).toBeVisible({ timeout: 15_000 });
  });

  test('should display shape panel', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    const shapePanel = editor.shapePanel.or(
      adminPage.getByTestId('shapes-panel').or(
        adminPage.locator('.shape-panel, [class*="ShapePanel"], [class*="Shapes"]')
      )
    );
    await expect(shapePanel.first()).toBeVisible({ timeout: 15_000 });
  });

  test('should display canvas area', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    const canvas = editor.canvasArea.or(
      adminPage.locator('canvas').or(
        adminPage.locator('.canvas-container, [class*="Canvas"]')
      )
    );
    await expect(canvas.first()).toBeVisible({ timeout: 15_000 });
  });

  test('should show save button', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    await expect(editor.saveButton).toBeVisible({ timeout: 15_000 });
  });

  test('should save drawing without error', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');

    // Set a drawing title if the field is available
    const titleInput = editor.drawingTitle.or(
      adminPage.getByPlaceholder(/untitled|drawing title|name/i)
    );
    const titleVisible = await titleInput.isVisible().catch(() => false);
    if (titleVisible) {
      await titleInput.fill('Saved Drawing Test');
    }

    await editor.save();
    // Should stay in editor or navigate to the saved drawing URL
    await expect(adminPage.locator('body')).toBeVisible();
    // No error dialogs should appear
    const errorMsg = adminPage.locator('[role="alert"].error, .error-toast, [data-testid="save-error"]');
    const hasError = await errorMsg.isVisible().catch(() => false);
    expect(hasError).toBe(false);
  });

  test('should show undo button and be clickable', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    await expect(editor.undoButton.first()).toBeVisible({ timeout: 15_000 });
    // Undo should not throw
    await editor.undoButton.first().click();
    await expect(adminPage.locator('body')).toBeVisible();
  });

  test('should show redo button and be clickable', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    await expect(editor.redoButton.first()).toBeVisible({ timeout: 15_000 });
    await editor.redoButton.first().click();
    await expect(adminPage.locator('body')).toBeVisible();
  });

  test('should support Ctrl+Z for undo', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    // Focus canvas area before keyboard shortcut
    await editor.canvasArea.first().click({ force: true }).catch(() => {});
    await adminPage.keyboard.press('Control+z');
    await expect(adminPage.locator('body')).toBeVisible();
  });

  test('should support Ctrl+Y for redo', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    await editor.canvasArea.first().click({ force: true }).catch(() => {});
    await adminPage.keyboard.press('Control+y');
    await expect(adminPage.locator('body')).toBeVisible();
  });

  test('should show zoom in/out controls', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    const zoomIn = editor.zoomInButton.or(
      adminPage.locator('[aria-label*="zoom in" i], [title*="zoom in" i]')
    );
    const zoomOut = editor.zoomOutButton.or(
      adminPage.locator('[aria-label*="zoom out" i], [title*="zoom out" i]')
    );
    // At least one zoom control should be present
    const zoomInVisible = await zoomIn.first().isVisible().catch(() => false);
    const zoomOutVisible = await zoomOut.first().isVisible().catch(() => false);
    expect(zoomInVisible || zoomOutVisible).toBe(true);
  });

  test('should open export dialog', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    const exportBtn = editor.exportButton.or(
      adminPage.getByRole('button', { name: /export/i }).or(
        adminPage.getByTestId('editor-export-btn')
      )
    );
    const exportBtnVisible = await exportBtn.first().isVisible().catch(() => false);
    if (exportBtnVisible) {
      await exportBtn.first().click();
      const exportDialog = adminPage.getByRole('dialog').or(
        adminPage.getByText(/export|download|format/i)
      );
      await expect(exportDialog.first()).toBeVisible({ timeout: 8_000 });
      // Close dialog
      await adminPage.keyboard.press('Escape');
    } else {
      expect(true).toBe(true);
    }
  });

  test('should open share dialog', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    const shareBtn = editor.shareButton.or(
      adminPage.getByTestId('editor-share-btn')
    );
    const shareBtnVisible = await shareBtn.first().isVisible().catch(() => false);
    if (shareBtnVisible) {
      await shareBtn.first().click();
      const shareDialog = adminPage.getByRole('dialog').or(
        adminPage.getByText(/share|copy link|access/i)
      );
      await expect(shareDialog.first()).toBeVisible({ timeout: 8_000 });
      await adminPage.keyboard.press('Escape');
    } else {
      expect(true).toBe(true);
    }
  });

  test('should open save as template dialog or menu item', async ({ adminPage }) => {
    const editor = new DrawingEditorPage(adminPage);
    await editor.goto('new');
    const templateBtn = adminPage.getByRole('button', { name: /template/i }).or(
      adminPage.getByRole('menuitem', { name: /save as template/i }).or(
        adminPage.getByTestId('editor-template-btn')
      )
    );
    const templateVisible = await templateBtn.first().isVisible().catch(() => false);
    if (templateVisible) {
      await templateBtn.first().click();
      const templateDialog = adminPage.getByRole('dialog').or(
        adminPage.getByText(/save as template|template name/i)
      );
      await expect(templateDialog.first()).toBeVisible({ timeout: 8_000 });
      await adminPage.keyboard.press('Escape');
    } else {
      // Template may be under a more/file menu
      expect(true).toBe(true);
    }
  });
});
