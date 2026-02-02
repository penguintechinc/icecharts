#!/usr/bin/env node
/**
 * Generate Iconoir Icon Mappings
 *
 * This script auto-generates the icon map and categories for all Iconoir icons
 * from the iconoir-react package.
 */

import * as IconoirIcons from 'iconoir-react';
import { writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Get all icon names from iconoir-react
const allIconNames = Object.keys(IconoirIcons).filter(
  key => !key.startsWith('_') &&
         key !== 'default' &&
         key !== '__esModule' &&
         typeof IconoirIcons[key] !== 'undefined'
);

console.log(`Found ${allIconNames.length} Iconoir icons`);
console.log(`First 10 icons: ${allIconNames.slice(0, 10).join(', ')}`);

// Helper to convert PascalCase to kebab-case
const toKebabCase = (str) => {
  return str
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .replace(/([A-Z])([A-Z][a-z])/g, '$1-$2')
    .toLowerCase();
};

// Helper to convert PascalCase to readable label
const toLabel = (str) => {
  return str
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/([A-Z])([A-Z][a-z])/g, '$1 $2')
    .replace(/([0-9])([A-Za-z])/g, '$1 $2')
    .trim();
};

// Helper to generate tags from icon name
const generateTags = (name) => {
  const label = toLabel(name);
  const words = label.toLowerCase().split(' ');
  const tags = new Set(words);

  // Add common synonyms
  if (words.includes('arrow')) tags.add('direction');
  if (words.includes('check')) tags.add('success');
  if (words.includes('x') || words.includes('xmark')) tags.add('close');
  if (words.includes('plus')) tags.add('add');
  if (words.includes('minus')) tags.add('remove');
  if (words.includes('user')) tags.add('person');
  if (words.includes('mail')) tags.add('email');
  if (words.includes('folder')) tags.add('directory');
  if (words.includes('file')) tags.add('document');

  return Array.from(tags);
};

// Categorize icons
const categories = {
  'Arrows & Navigation': [],
  'Interface & Actions': [],
  'Files & Folders': [],
  'Communication': [],
  'Media & Content': [],
  'Development & Code': [],
  'Business & Finance': [],
  'Security & Privacy': [],
  'System & Settings': [],
  'Social & Sharing': [],
  'E-commerce & Shopping': [],
  'Transportation': [],
  'Weather & Nature': [],
  'Health & Medical': [],
  'Sports & Activities': [],
  'Food & Dining': [],
  'Education': [],
  'Time & Calendar': [],
  'Location & Maps': [],
  'Shapes & Symbols': [],
  'Miscellaneous': [],
};

// Simple categorization based on icon name
const categorizeIcon = (name) => {
  const lower = name.toLowerCase();

  if (/arrow|nav|direction|expand|collapse|zoom/.test(lower)) return 'Arrows & Navigation';
  if (/file|folder|page|document|note|paper/.test(lower)) return 'Files & Folders';
  if (/mail|message|chat|phone|call|notification|bell/.test(lower)) return 'Communication';
  if (/video|audio|music|play|pause|camera|image|photo|picture/.test(lower)) return 'Media & Content';
  if (/code|terminal|git|github|bug|test|dev|database|server/.test(lower)) return 'Development & Code';
  if (/money|dollar|euro|coin|wallet|credit|card|bank|chart|graph/.test(lower)) return 'Business & Finance';
  if (/lock|unlock|key|shield|security|privacy|eye/.test(lower)) return 'Security & Privacy';
  if (/settings|tool|wrench|gear|cog|power|battery|wifi|network/.test(lower)) return 'System & Settings';
  if (/share|like|heart|star|bookmark|user|profile|people|group/.test(lower)) return 'Social & Sharing';
  if (/cart|shop|bag|store|product|purchase/.test(lower)) return 'E-commerce & Shopping';
  if (/car|bus|train|plane|bike|ship|transport/.test(lower)) return 'Transportation';
  if (/sun|moon|cloud|rain|snow|storm|weather|tree|leaf|plant/.test(lower)) return 'Weather & Nature';
  if (/health|medical|hospital|medicine|doctor|heart|pulse/.test(lower)) return 'Health & Medical';
  if (/sport|ball|game|run|fitness|gym/.test(lower)) return 'Sports & Activities';
  if (/food|drink|coffee|restaurant|pizza|burger/.test(lower)) return 'Food & Dining';
  if (/book|education|school|learn|study|graduation/.test(lower)) return 'Education';
  if (/clock|time|calendar|date|schedule|alarm/.test(lower)) return 'Time & Calendar';
  if (/map|location|pin|marker|gps|compass/.test(lower)) return 'Location & Maps';
  if (/circle|square|triangle|shape|line|cube/.test(lower)) return 'Shapes & Symbols';
  if (/plus|minus|check|x|xmark|info|warning|error|question|help/.test(lower)) return 'Interface & Actions';

  return 'Miscellaneous';
};

// Build icon definitions
allIconNames.forEach(name => {
  const id = `iconoir-${toKebabCase(name)}`;
  const label = toLabel(name);
  const category = categorizeIcon(name);
  const tags = generateTags(name);

  categories[category].push({
    id,
    label,
    importName: name,
    tags,
  });
});

// Generate index.tsx content
const generateIndexFile = () => {
  const imports = `/**
 * Iconoir Icon Adapter - Auto-generated
 *
 * This file is auto-generated from the iconoir-react package.
 * To regenerate, run: npm run generate-icons
 *
 * Total icons: ${allIconNames.length}
 */

import { FC } from 'react';
import * as IconoirIcons from 'iconoir-react';
import type { IconProps, IconComponent, IconMap } from '../types';

/**
 * Wrapper function to create a normalized icon component from iconoir icon
 */
const createIconComponent = (IconComponent: any): IconComponent => {
  const WrappedIcon: FC<IconProps> = ({
    className,
    size = 24,
    color = '#8B5CF6',
  }) => {
    const sizeNum = typeof size === 'string' ? parseInt(size, 10) : size;
    return (
      <IconComponent
        width={sizeNum}
        height={sizeNum}
        color={color}
        strokeWidth={2}
        className={className}
      />
    );
  };
  WrappedIcon.displayName = \`IconoirIcon\`;
  return WrappedIcon;
};

/**
 * Iconoir Icon Map - All ${allIconNames.length} icons from iconoir-react v7.11.0
 * Each icon is wrapped to accept standard IconProps (className, size, color)
 */
export const iconoirIconMap: IconMap = {
`;

  const iconMappings = allIconNames
    .sort()
    .map(name => {
      const id = `iconoir-${toKebabCase(name)}`;
      return `  '${id}': createIconComponent(IconoirIcons.${name}),`;
    })
    .join('\n');

  const exports = `
};

/**
 * Get an icon component by ID
 */
export const getIconoirIcon = (id: string): IconComponent | undefined => {
  return iconoirIconMap[id];
};

/**
 * List all available iconoir icon IDs
 */
export const listIconoirIcons = (): string[] => {
  return Object.keys(iconoirIconMap);
};

/**
 * Total number of available icons
 */
export const ICONOIR_ICON_COUNT = ${allIconNames.length};

export default iconoirIconMap;
`;

  return imports + iconMappings + exports;
};

// Generate categories.ts content
const generateCategoriesFile = () => {
  const header = `/**
 * Iconoir Icon Categories - Auto-generated
 *
 * This file is auto-generated from the iconoir-react package.
 * To regenerate, run: npm run generate-icons
 *
 * Total icons: ${allIconNames.length}
 * Total categories: ${Object.keys(categories).length}
 */

import type { IconCategory } from '../types';

/**
 * Iconoir categories with icon definitions
 * Each icon has: id, label, color (purple), source, and tags for search
 */
const iconoirCategoriesArray: IconCategory[] = [
`;

  const categoryContent = Object.entries(categories)
    .filter(([_, icons]) => icons.length > 0)
    .map(([categoryName, icons]) => {
      const iconsJson = icons.map(icon => `      {
        id: '${icon.id}',
        label: '${icon.label}',
        color: '#8B5CF6',
        source: 'iconoir',
        tags: ${JSON.stringify(icon.tags)},
      }`).join(',\n');

      return `  {
    label: '${categoryName}',
    source: 'iconoir',
    icons: [
${iconsJson}
    ],
  }`;
    })
    .join(',\n');

  const footer = `
];

/**
 * Iconoir categories as a Record (compatible with main icon registry)
 */
export const iconoirCategories: Record<string, IconCategory> = Object.fromEntries(
  iconoirCategoriesArray.map((cat) => [cat.label, cat])
);

/**
 * Iconoir categories map for quick lookup
 */
export const iconoirCategoriesMap = new Map<string, IconCategory>(
  iconoirCategoriesArray.map((cat) => [cat.label, cat])
);

/**
 * Get all Iconoir icons across all categories
 */
export const getAllIconoirIcons = () => {
  return iconoirCategoriesArray.flatMap((cat) => cat.icons);
};

/**
 * Total number of icons
 */
export const TOTAL_ICONOIR_ICONS = ${allIconNames.length};

export default iconoirCategoriesArray;
`;

  return header + categoryContent + footer;
};

// Write files
const iconoirPath = join(__dirname, '../src/client/components/diagram/icons/iconoir');

try {
  const indexContent = generateIndexFile();
  const categoriesContent = generateCategoriesFile();

  writeFileSync(join(iconoirPath, 'index.tsx'), indexContent, 'utf8');
  console.log('✅ Generated index.tsx');

  writeFileSync(join(iconoirPath, 'categories.ts'), categoriesContent, 'utf8');
  console.log('✅ Generated categories.ts');

  // Print summary
  console.log('\n📊 Summary:');
  console.log(`   Total icons: ${allIconNames.length}`);
  console.log(`   Categories: ${Object.keys(categories).length}`);
  console.log('\n📁 Category breakdown:');
  Object.entries(categories)
    .filter(([_, icons]) => icons.length > 0)
    .sort((a, b) => b[1].length - a[1].length)
    .forEach(([name, icons]) => {
      console.log(`   ${name}: ${icons.length} icons`);
    });

  console.log('\n✨ Done! All Iconoir icons are now available.');
} catch (error) {
  console.error('❌ Error generating files:', error);
  process.exit(1);
}
