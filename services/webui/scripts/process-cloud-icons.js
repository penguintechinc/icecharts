#!/usr/bin/env node
/**
 * Process Official Cloud Provider Icons
 *
 * This script processes official SVG icons from AWS, Azure, and GCP
 * and generates React components and icon adapters.
 */

import { readdirSync, readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const SOURCE_DIR = '/tmp/cloud-icons';
const TARGET_DIR = join(__dirname, '../src/client/components/diagram/icons');

// Configuration for each provider
const PROVIDERS = {
  aws: {
    sourcePath: join(SOURCE_DIR, 'Architecture-Service-Icons_07312025'),
    targetPath: join(TARGET_DIR, 'aws'),
    color: '#FF9900',
    pattern: /Arch_(.+?)_(\d+)\.svg$/,  // Match files like "Arch_Amazon-EC2_48.svg"
    excludePattern: /_Dark_|_16\.svg|_32\.svg|_64\.svg/,  // Only use 48px light versions
  },
  azure: {
    sourcePath: join(SOURCE_DIR, 'Azure_Public_Service_Icons/Icons'),
    targetPath: join(TARGET_DIR, 'azure'),
    color: '#0078D4',
    pattern: /icon-service-(.+?)\.svg$/,  // Match files like "icon-service-Virtual-Machines.svg"
    excludePattern: null,
  },
  gcp: {
    sourcePath: [
      join(SOURCE_DIR, 'gcp-category/Category Icons'),
      join(SOURCE_DIR, 'gcp-products/Unique Icons'),
    ],
    targetPath: join(TARGET_DIR, 'gcp'),
    color: '#DB4437',
    pattern: /(.+?)-512-color.*\.svg$/,  // Match files like "Cloud_Storage-512-color.svg"
    excludePattern: null,
  },
};

/**
 * Recursively find all SVG files in a directory
 */
function findSvgFiles(dir, pattern, excludePattern) {
  let results = [];

  if (!existsSync(dir)) return results;

  const files = readdirSync(dir, { withFileTypes: true });

  for (const file of files) {
    const fullPath = join(dir, file.name);

    if (file.isDirectory()) {
      results = results.concat(findSvgFiles(fullPath, pattern, excludePattern));
    } else if (file.name.endsWith('.svg')) {
      if (pattern && !pattern.test(file.name)) continue;
      if (excludePattern && excludePattern.test(file.name)) continue;
      results.push(fullPath);
    }
  }

  return results;
}

/**
 * Convert SVG file name to icon name
 */
function svgToIconName(filename, provider) {
  let match;

  if (provider === 'aws') {
    match = filename.match(/Arch_(.+?)_48\.svg$/);
    if (match) {
      return match[1]
        .replace(/^Amazon-|^AWS-/, '')
        .replace(/-/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    }
  } else if (provider === 'azure') {
    match = filename.match(/icon-service-(.+?)\.svg$/);
    if (match) {
      return match[1]
        .replace(/-/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    }
  } else if (provider === 'gcp') {
    match = filename.match(/(.+?)-512-color.*\.svg$/);
    if (match) {
      return match[1]
        .replace(/_/g, ' ')
        .replace(/([a-z])([A-Z])/g, '$1 $2')
        .replace(/\s+/g, ' ')
        .trim();
    }
  }

  return filename.replace('.svg', '').replace(/[-_]/g, ' ');
}

/**
 * Convert icon name to kebab-case ID (sanitized for use as object keys)
 */
function nameToId(name, provider) {
  return `${provider}-${name
    .toLowerCase()
    .replace(/[&()]/g, '')  // Remove special characters
    .replace(/\s+/g, '-')    // Replace spaces with dashes
    .replace(/--+/g, '-')    // Replace multiple dashes with single dash
    .replace(/^-|-$/g, '')}`;  // Remove leading/trailing dashes
}

/**
 * Process icons for a provider
 */
function processProvider(provider, config) {
  console.log(`\n🔍 Processing ${provider.toUpperCase()} icons...`);

  const sourcePaths = Array.isArray(config.sourcePath)
    ? config.sourcePath
    : [config.sourcePath];

  let allSvgFiles = [];
  for (const sourcePath of sourcePaths) {
    const svgFiles = findSvgFiles(sourcePath, config.pattern, config.excludePattern);
    allSvgFiles = allSvgFiles.concat(svgFiles);
  }

  console.log(`   Found ${allSvgFiles.length} SVG files`);

  // Create icon definitions
  const icons = allSvgFiles.map(svgPath => {
    const filename = basename(svgPath);
    const name = svgToIconName(filename, provider);
    const id = nameToId(name, provider);

    return {
      id,
      name,
      svgPath,
      filename,
    };
  });

  // Remove duplicates by ID
  const uniqueIcons = {};
  for (const icon of icons) {
    if (!uniqueIcons[icon.id]) {
      uniqueIcons[icon.id] = icon;
    }
  }

  const finalIcons = Object.values(uniqueIcons);
  console.log(`   ${finalIcons.length} unique icons after deduplication`);

  return {
    provider,
    icons: finalIcons,
    color: config.color,
  };
}

/**
 * Copy SVGs and convert to React components
 */
function convertSvgsToReact(providerData) {
  const { provider, icons } = providerData;
  const svgDir = join(TARGET_DIR, provider, 'svgs');

  // Create SVG directory
  mkdirSync(svgDir, { recursive: true });

  console.log(`\n📦 Converting ${icons.length} ${provider.toUpperCase()} SVGs to React components...`);

  // Copy SVG files
  for (const icon of icons) {
    const targetPath = join(svgDir, `${icon.id}.svg`);
    const svgContent = readFileSync(icon.svgPath, 'utf8');
    writeFileSync(targetPath, svgContent);
  }

  console.log(`   ✅ Copied ${icons.length} SVG files to ${svgDir}`);

  // Convert using @svgr/cli
  const componentsDir = join(TARGET_DIR, provider, 'components');
  mkdirSync(componentsDir, { recursive: true });

  try {
    execSync(
      `npx @svgr/cli --out-dir "${componentsDir}" --typescript --memo "${svgDir}"`,
      { stdio: 'inherit', cwd: join(__dirname, '..') }
    );
    console.log(`   ✅ Generated React components in ${componentsDir}`);

    // Post-process to remove problematic attributes
    removeIsolationAttributes(componentsDir);
  } catch (error) {
    console.error(`   ❌ Error converting SVGs:`, error.message);
  }
}

/**
 * Remove 'isolation' attributes from generated components
 * These cause TypeScript errors as they're not in SVGProps types
 */
function removeIsolationAttributes(componentsDir) {
  if (!existsSync(componentsDir)) return;

  const files = readdirSync(componentsDir);
  let count = 0;

  for (const file of files) {
    if (!file.endsWith('.tsx')) continue;

    const filePath = join(componentsDir, file);
    const content = readFileSync(filePath, 'utf-8');

    // Remove isolation="..." attributes
    const updatedContent = content.replace(/\s+isolation="[^"]*"/g, '');

    if (content !== updatedContent) {
      writeFileSync(filePath, updatedContent, 'utf-8');
      count++;
    }
  }

  if (count > 0) {
    console.log(`   🔧 Removed isolation attributes from ${count} components`);
  }
}

/**
 * Generate icon adapter (index.tsx)
 */
function generateIconAdapter(providerData) {
  const { provider, icons, color } = providerData;
  const componentsDir = join(TARGET_DIR, provider, 'components');

  console.log(`\n📝 Generating ${provider.toUpperCase()} icon adapter...`);

  const imports = icons
    .map(icon => {
      // Convert kebab-case ID to PascalCase component name, removing invalid chars
      const componentName = icon.id
        .split('-')
        .map(word => {
          // Handle special cases: abbreviations and numbers should be fully uppercase
          if (/^(a2i|b2b|3d|5g|2|3|4|5|6|7|8|9|p2p|s3|ec2|i|ii|iii|iv|v|vi|vii|viii|ix|x)$/i.test(word)) {
            return word.toUpperCase();
          }
          // Normal PascalCase: first letter uppercase, rest lowercase
          return word.charAt(0).toUpperCase() + word.slice(1);
        })
        .join('')
        .replace(/[^a-zA-Z0-9]/g, '');  // Remove any non-alphanumeric chars

      // Import path uses PascalCase filename (as generated by @svgr)
      return `import ${componentName} from './components/${componentName}';`;
    })
    .join('\n');

  const iconMapEntries = icons
    .map(icon => {
      // Convert kebab-case ID to PascalCase component name, removing invalid chars
      const componentName = icon.id
        .split('-')
        .map(word => {
          // Handle special cases: abbreviations and numbers should be fully uppercase
          if (/^(a2i|b2b|3d|5g|2|3|4|5|6|7|8|9|p2p|s3|ec2|i|ii|iii|iv|v|vi|vii|viii|ix|x)$/i.test(word)) {
            return word.toUpperCase();
          }
          // Normal PascalCase: first letter uppercase, rest lowercase
          return word.charAt(0).toUpperCase() + word.slice(1);
        })
        .join('')
        .replace(/[^a-zA-Z0-9]/g, '');  // Remove any non-alphanumeric chars

      return `  '${icon.id}': createIconComponent(${componentName}),`;
    })
    .join('\n');

  const content = `/**
 * ${provider.toUpperCase()} Icon Adapter - Auto-generated
 *
 * This file is auto-generated from official ${provider.toUpperCase()} icons.
 * To regenerate, run: npm run process-cloud-icons
 *
 * Total icons: ${icons.length}
 */

import { FC } from 'react';
import type { IconProps, IconComponent, IconMap } from '../types';

${imports}

/**
 * Wrapper function to create a normalized icon component
 */
const createIconComponent = (IconComponent: any): IconComponent => {
  const WrappedIcon: FC<IconProps> = ({
    className,
    size = 24,
    color = '${color}',
  }) => {
    const sizeNum = typeof size === 'string' ? parseInt(size, 10) : size;
    return (
      <IconComponent
        width={sizeNum}
        height={sizeNum}
        fill={color}
        className={className}
      />
    );
  };
  WrappedIcon.displayName = \`${provider.toUpperCase()}Icon\`;
  return WrappedIcon;
};

/**
 * ${provider.toUpperCase()} Icon Map - All ${icons.length} official icons
 */
export const ${provider}IconMap: IconMap = {
${iconMapEntries}
};

/**
 * Get an icon component by ID
 */
export const get${provider.charAt(0).toUpperCase() + provider.slice(1)}Icon = (id: string): IconComponent | undefined => {
  return ${provider}IconMap[id];
};

/**
 * List all available ${provider.toUpperCase()} icon IDs
 */
export const list${provider.charAt(0).toUpperCase() + provider.slice(1)}Icons = (): string[] => {
  return Object.keys(${provider}IconMap);
};

export default ${provider}IconMap;
`;

  const adapterPath = join(TARGET_DIR, provider, 'index.tsx');
  writeFileSync(adapterPath, content, 'utf8');
  console.log(`   ✅ Generated ${adapterPath}`);
}

/**
 * Generate categories file
 */
function generateCategories(providerData) {
  const { provider, icons, color } = providerData;

  console.log(`\n📋 Generating ${provider.toUpperCase()} categories...`);

  // Simple categorization
  const categories = {};

  for (const icon of icons) {
    const category = 'All Services';  // For now, put all in one category
    if (!categories[category]) {
      categories[category] = [];
    }

    categories[category].push({
      id: icon.id,
      label: icon.name,
      color,
      source: provider,
      tags: icon.name.toLowerCase().split(' '),
    });
  }

  const categoryContent = Object.entries(categories)
    .map(([categoryName, categoryIcons]) => {
      const iconsJson = categoryIcons.map(icon => `      {
        id: '${icon.id}',
        label: '${icon.label}',
        color: '${icon.color}',
        source: '${icon.source}',
        tags: ${JSON.stringify(icon.tags)},
      }`).join(',\n');

      return `  {
    label: '${categoryName}',
    source: '${provider}',
    icons: [
${iconsJson}
    ],
  }`;
    })
    .join(',\n');

  const content = `/**
 * ${provider.toUpperCase()} Icon Categories - Auto-generated
 *
 * This file is auto-generated from official ${provider.toUpperCase()} icons.
 * To regenerate, run: npm run process-cloud-icons
 *
 * Total icons: ${icons.length}
 */

import type { IconCategory } from '../types';

const ${provider}CategoriesArray: IconCategory[] = [
${categoryContent}
];

/**
 * ${provider.toUpperCase()} categories as a Record
 */
export const ${provider}Categories: Record<string, IconCategory> = Object.fromEntries(
  ${provider}CategoriesArray.map((cat) => [cat.label, cat])
);

/**
 * Get all ${provider.toUpperCase()} icons
 */
export const getAll${provider.charAt(0).toUpperCase() + provider.slice(1)}Icons = () => {
  return ${provider}CategoriesArray.flatMap((cat) => cat.icons);
};

export default ${provider}CategoriesArray;
`;

  const categoriesPath = join(TARGET_DIR, provider, 'categories.ts');
  writeFileSync(categoriesPath, content, 'utf8');
  console.log(`   ✅ Generated ${categoriesPath}`);
}

// Main execution
console.log('🚀 Processing Official Cloud Provider Icons\n');
console.log('=' .repeat(60));

const results = [];

for (const [provider, config] of Object.entries(PROVIDERS)) {
  const providerData = processProvider(provider, config);
  convertSvgsToReact(providerData);
  generateIconAdapter(providerData);
  generateCategories(providerData);
  results.push(providerData);
}

console.log('\n' + '='.repeat(60));
console.log('\n✨ Summary:');
for (const result of results) {
  console.log(`   ${result.provider.toUpperCase()}: ${result.icons.length} icons`);
}
console.log(`   TOTAL: ${results.reduce((sum, r) => sum + r.icons.length, 0)} icons`);
console.log('\n✅ Done! All cloud provider icons have been processed.');
