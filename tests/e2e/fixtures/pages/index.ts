/**
 * Page Object re-exports.
 *
 * Import all page objects from this single entry point:
 *
 *   import { LoginPage, DashboardPage, DrawingEditorPage } from '../fixtures/pages';
 */

export { LoginPage } from './LoginPage';
export { DashboardPage } from './DashboardPage';
export { DrawingEditorPage } from './DrawingEditorPage';
export { SettingsPage } from './SettingsPage';
export { IceFlowsPage } from './IceFlowsPage';
export { IceRunsPage } from './IceRunsPage';
export { PlaybooksPage } from './PlaybooksPage';
export { AdminPage } from './AdminPage';

export type { SettingsTab } from './SettingsPage';
export type { UserRole } from './AdminPage';
