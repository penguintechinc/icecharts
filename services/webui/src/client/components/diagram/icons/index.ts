/**
 * Main Icon Registry - Combines all icon sources
 */

import type { IconComponent, IconDefinition, IconCategory } from './types';

// Internal icons
import { internalIconMap, internalCategories } from './internal';

// External adapters (import from .tsx files)
import { awsIconMap } from './aws/index';
import awsCategoriesArray from './aws/categories';
import { azureIconMap } from './azure/index';
import azureCategoriesArray from './azure/categories';
import { gcpIconMap } from './gcp/index';
import gcpCategoriesArray from './gcp/categories';
import { ibmIconMap } from './ibm/index';
import ibmCategoriesArray from './ibm/categories';
import { iconoirIconMap } from './iconoir/index';
import iconoirCategoriesArray from './iconoir/categories';

// Re-export types
export * from './types';

// Combined icon map (all sources)
export const iconMap: Record<string, IconComponent> = {
  ...internalIconMap,
  ...awsIconMap,
  ...azureIconMap,
  ...gcpIconMap,
  ...ibmIconMap,
  ...iconoirIconMap,
};

// Provider info with colors and labels
export interface ProviderInfo {
  id: string;
  label: string;
  color: string;
  categories: IconCategory[];
}

// Provider-grouped categories for hierarchical display
export const cloudProviders: ProviderInfo[] = [
  {
    id: 'aws',
    label: 'AWS',
    color: '#FF9900',
    categories: awsCategoriesArray,
  },
  {
    id: 'azure',
    label: 'Azure',
    color: '#0078D4',
    categories: azureCategoriesArray,
  },
  {
    id: 'gcp',
    label: 'GCP',
    color: '#4285F4',
    categories: gcpCategoriesArray,
  },
  {
    id: 'ibm',
    label: 'IBM Cloud',
    color: '#054ADA',
    categories: ibmCategoriesArray,
  },
];

// Other icon sources (non-cloud-provider)
export const otherIconSources: ProviderInfo[] = [
  {
    id: 'internal',
    label: 'Basic Icons',
    color: '#6B7280',
    categories: Object.values(internalCategories),
  },
  {
    id: 'iconoir',
    label: 'Iconoir',
    color: '#6B7280',
    categories: iconoirCategoriesArray,
  },
];

// Combined categories (flat - for backwards compatibility)
export const iconCategories: Record<string, IconCategory> = {
  ...internalCategories,
  ...Object.fromEntries(awsCategoriesArray.map((cat: IconCategory) => [`aws-${cat.label}`, cat])),
  ...Object.fromEntries(azureCategoriesArray.map((cat: IconCategory) => [`azure-${cat.label}`, cat])),
  ...Object.fromEntries(gcpCategoriesArray.map((cat: IconCategory) => [`gcp-${cat.label}`, cat])),
  ...Object.fromEntries(ibmCategoriesArray.map((cat: IconCategory) => [`ibm-${cat.label}`, cat])),
  ...Object.fromEntries(iconoirCategoriesArray.map((cat: IconCategory) => [`iconoir-${cat.label}`, cat])),
};

// Get all icons as flat array
export function getAllIcons(): IconDefinition[] {
  const allCategories = [
    ...awsCategoriesArray,
    ...azureCategoriesArray,
    ...gcpCategoriesArray,
    ...ibmCategoriesArray,
    ...iconoirCategoriesArray,
    ...Object.values(internalCategories),
  ];
  return allCategories.flatMap(cat => cat.icons);
}

// Get icon component by ID
export function getIcon(id: string): IconComponent | undefined {
  return iconMap[id];
}

// Get category keys
export function getCategoryKeys(): string[] {
  return Object.keys(iconCategories);
}

// Search export
export { useIconSearch } from './search/useIconSearch';
export { IconSearch } from './search/IconSearch';
