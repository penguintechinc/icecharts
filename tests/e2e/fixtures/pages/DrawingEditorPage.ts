/**
 * Page Object Model — Drawing Editor (/drawings/:id/edit or /drawings/new)
 *
 * The main canvas editing surface where users create and modify diagrams.
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class DrawingEditorPage {
  readonly urlPattern = /\/drawings\/(new|[^/]+\/edit)/;

  // Locators
  readonly toolbar: Locator;
  readonly shapePanel: Locator;
  readonly canvasArea: Locator;
  readonly saveButton: Locator;
  readonly undoButton: Locator;
  readonly redoButton: Locator;
  readonly drawingTitle: Locator;
  readonly shareButton: Locator;
  readonly exportButton: Locator;
  readonly zoomInButton: Locator;
  readonly zoomOutButton: Locator;
  readonly selectToolButton: Locator;

  constructor(private readonly page: Page) {
    // Toolbar — top or left-hand strip of editing tools
    this.toolbar = page.getByTestId('editor-toolbar').or(
      page.locator('[role="toolbar"]').or(
        page.locator('.editor-toolbar, [class*="Toolbar"]')
      )
    );

    // Shape / element panel (side panel with shape categories)
    this.shapePanel = page.getByTestId('shape-panel').or(
      page.locator('[data-testid="shapes-panel"]').or(
        page.locator('.shape-panel, [class*="ShapePanel"]')
      )
    );

    // Main canvas / drawing surface
    this.canvasArea = page.getByTestId('canvas-area').or(
      page.locator('canvas').or(
        page.locator('[data-testid="drawing-canvas"], .canvas-container, [class*="Canvas"]')
      )
    );

    // Save button
    this.saveButton = page.getByTestId('editor-save').or(
      page.getByRole('button', { name: /save/i })
    );

    // Undo / redo
    this.undoButton = page.getByTestId('editor-undo').or(
      page.getByRole('button', { name: /undo/i }).or(
        page.locator('[title="Undo"], [aria-label="Undo"]')
      )
    );
    this.redoButton = page.getByTestId('editor-redo').or(
      page.getByRole('button', { name: /redo/i }).or(
        page.locator('[title="Redo"], [aria-label="Redo"]')
      )
    );

    // Drawing title (editable)
    this.drawingTitle = page.getByTestId('drawing-title').or(
      page.locator('input[name="title"], input[placeholder*="title" i]')
    );

    this.shareButton = page.getByRole('button', { name: /share/i });
    this.exportButton = page.getByRole('button', { name: /export/i });
    this.zoomInButton = page.getByRole('button', { name: /zoom in/i }).or(
      page.locator('[aria-label="Zoom in"]')
    );
    this.zoomOutButton = page.getByRole('button', { name: /zoom out/i }).or(
      page.locator('[aria-label="Zoom out"]')
    );
    this.selectToolButton = page.getByTestId('tool-select').or(
      page.getByRole('button', { name: /select|pointer/i })
    );
  }

  /**
   * Navigate to the editor for a specific drawing ID.
   * Pass 'new' to open the new-drawing editor.
   */
  async goto(id: string | 'new'): Promise<void> {
    const path = id === 'new' ? '/drawings/new' : `/drawings/${id}/edit`;
    await this.page.goto(path);
    await expect(this.page).toHaveURL(this.urlPattern, { timeout: 15_000 });
  }

  /**
   * Click a toolbar tool by its accessible name or test id.
   * E.g. selectTool('rectangle'), selectTool('line'), selectTool('text')
   */
  async selectTool(name: string): Promise<void> {
    const toolButton = this.page.getByTestId(`tool-${name.toLowerCase()}`).or(
      this.page.getByRole('button', { name: new RegExp(name, 'i') })
    );
    await toolButton.click();
  }

  /**
   * Add a shape to the canvas by clicking the shape in the panel.
   * Supported types mirror the shape library (e.g. 'rectangle', 'circle', 'diamond').
   */
  async addShape(type: string): Promise<void> {
    const shapeItem = this.shapePanel.getByText(new RegExp(type, 'i')).first().or(
      this.page.getByTestId(`shape-${type.toLowerCase()}`)
    );
    await shapeItem.click();
  }

  /**
   * Click Save and wait for the confirmation.
   */
  async save(): Promise<void> {
    await this.saveButton.click();
    // Wait for save to complete — look for a toast or the button returning to idle state
    const saveConfirm = this.page.getByText(/saved|saved successfully/i).or(
      this.page.locator('[data-testid="save-success"]')
    );
    await saveConfirm.waitFor({ state: 'visible', timeout: 10_000 }).catch(() => {
      // Not all implementations show an explicit success message — that is fine
    });
  }

  /**
   * Click Undo.
   */
  async undo(): Promise<void> {
    await this.undoButton.click();
  }

  /**
   * Click Redo.
   */
  async redo(): Promise<void> {
    await this.redoButton.click();
  }

  /**
   * Assert that the drawing editor is currently displayed.
   */
  async expectVisible(): Promise<void> {
    await expect(this.page).toHaveURL(this.urlPattern);
    await expect(this.canvasArea.or(this.toolbar)).toBeVisible();
  }
}
