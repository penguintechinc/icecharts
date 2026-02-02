/**
 * Connector logo imports
 *
 * Maps connector icon identifiers to their imported logo assets.
 */

import elderLogo from './elder-logo.png';
import waddlebotLogo from './waddlebot-logo.svg';

/**
 * Connector logo mapping
 */
export const connectorLogos: Record<string, string> = {
  'elder-logo': elderLogo,
  'waddlebot-logo': waddlebotLogo,
};

/**
 * Get logo URL for a connector icon identifier
 *
 * @param icon - Icon identifier from connector manifest
 * @returns Logo URL or the original icon string (for emojis)
 */
export function getConnectorLogo(icon: string): string {
  return connectorLogos[icon] || icon;
}
