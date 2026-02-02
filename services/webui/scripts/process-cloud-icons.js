#!/usr/bin/env node
/**
 * Process Official Cloud Provider Icons
 *
 * This unified script handles:
 * 1. Downloading official icons from AWS, Azure, GCP
 * 2. Converting SVGs to React components
 * 3. Categorizing icons into logical groups
 *
 * Usage: npm run process-cloud-icons [--skip-download] [--recategorize-only]
 */

import { readdirSync, readFileSync, writeFileSync, mkdirSync, existsSync, rmSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const SOURCE_DIR = '/tmp/cloud-icons';
const TARGET_DIR = join(__dirname, '../src/client/components/diagram/icons');

// Parse command line arguments
const args = process.argv.slice(2);
const SKIP_DOWNLOAD = args.includes('--skip-download');
const RECATEGORIZE_ONLY = args.includes('--recategorize-only');

// ============================================================
// CATEGORY KEYWORDS - Used to categorize icons by their names
// ============================================================
const CATEGORY_KEYWORDS = {
  'Compute': [
    'ec2', 'compute', 'lambda', 'batch', 'lightsail', 'elastic beanstalk',
    'fargate', 'app runner', 'outposts', 'wavelength', 'vmware', 'parallel',
    'serverless', 'virtual machine', 'instance', 'cloud run',
    'app engine', 'cloud functions', 'kubernetes engine', 'gke', 'eks', 'aks',
    'container instances', 'spring apps', 'bottlerocket', 'nitro', 'graviton',
  ],
  'Containers': [
    'container', 'docker', 'kubernetes', 'ecs', 'ecr', 'copilot',
    'registry', 'openshift', 'artifact registry', 'anthos',
  ],
  'Storage': [
    's3', 'storage', 'ebs', 'efs', 'glacier', 'backup', 'snow', 'fsx',
    'blob', 'disk', 'archive', 'data box', 'netapp', 'filestore',
    'persistent disk', 'cloud storage', 'lustre', 'elastic file', 'simple storage',
  ],
  'Database': [
    'database', 'rds', 'aurora', 'dynamodb', 'documentdb', 'elasticache',
    'neptune', 'redshift', 'timestream', 'qldb', 'keyspaces', 'memorydb',
    'cosmos', 'mysql', 'postgres', 'mariadb', 'mongodb', 'redis',
    'cassandra', 'bigtable', 'spanner', 'firestore', 'datastore', 'memcached',
    'alloydb', 'data factory',
  ],
  'Networking': [
    'vpc', 'network', 'route', 'cloudfront', 'api gateway', 'direct connect',
    'global accelerator', 'transit', 'privatelink', 'app mesh', 'cloud map',
    'load balancer', 'elb', 'alb', 'nlb', 'elastic load', 'nat', 'internet gateway',
    'peering', 'endpoint', 'vnet', 'expressroute', 'frontdoor',
    'traffic manager', 'cloud cdn', 'cloud dns', 'cloud nat', 'armor',
    'interconnect', 'cloud router', 'bastion', 'lattice',
  ],
  'Security & Identity': [
    'iam', 'identity', 'cognito', 'directory', 'secrets', 'certificate',
    'acm', 'kms', 'cloudhsm', 'macie', 'inspector', 'detective', 'guardduty',
    'security', 'shield', 'waf', 'firewall', 'access', 'sso', 'key vault',
    'sentinel', 'defender', 'secret manager', 'cloud identity', 'beyondcorp',
    'encryption', 'compliance', 'audit', 'trust', 'policy', 'permission',
    'verified access', 'resource access',
  ],
  'Analytics': [
    'analytics', 'athena', 'emr', 'kinesis', 'opensearch', 'quicksight',
    'data pipeline', 'glue', 'lake formation', 'msk', 'datazone',
    'synapse', 'data lake', 'stream analytics', 'hdinsight', 'databricks',
    'bigquery', 'dataflow', 'dataproc', 'pub/sub', 'pubsub', 'looker',
    'data fusion', 'data catalog', 'composer', 'business intelligence',
    'clean rooms', 'data exchange',
  ],
  'Machine Learning & AI': [
    'sagemaker', 'machine learning', 'bedrock', 'comprehend',
    'forecast', 'fraud', 'kendra', 'lex', 'personalize', 'polly', 'rekognition',
    'textract', 'transcribe', 'translate', 'augmented', 'deepracer', 'panorama',
    'cognitive', 'bot service', 'openai', 'speech', 'vision', 'language',
    'vertex', 'automl', 'tensorflow', 'notebooks', 'ai platform', 'dialogflow',
    'natural language', 'video intelligence', 'translation',
    'inference', 'neural', 'deep learning', 'prediction', 'recommendation',
    'genomics', 'healthlake', 'medical', 'omics', 'neuron',
  ],
  'Developer Tools': [
    'codecommit', 'codebuild', 'codedeploy', 'codepipeline', 'codestar',
    'codeguru', 'codeartifact', 'codecatalyst', 'cloud9', 'cloudshell',
    'x-ray', 'devops', 'repos', 'artifacts', 'pipelines', 'boards',
    'cloud build', 'cloud deploy', 'cloud source',
    'sdk', 'cli', 'toolkit', 'corretto', 'amplify',
  ],
  'Management & Governance': [
    'cloudwatch', 'cloudtrail', 'config', 'systems manager', 'cloudformation',
    'service catalog', 'organizations', 'control tower', 'trusted advisor',
    'proton', 'resilience', 'resource', 'license',
    'monitor', 'automation', 'advisor', 'cost', 'billing',
    'management', 'governance', 'logging', 'operations',
    'deployment manager', 'cloud console', 'cloud shell', 'recommender',
    'launch wizard', 'app config', 'well-architected',
  ],
  'Application Integration': [
    'eventbridge', 'sns', 'sqs', 'step functions', 'appflow', 'amazon mq',
    'integration', 'workflow', 'queue', 'notification',
    'bus', 'service bus', 'logic apps', 'event grid', 'api management',
    'cloud tasks', 'cloud scheduler', 'workflows', 'eventarc', 'apigee',
    'managed apache',
  ],
  'IoT': [
    'iot', 'greengrass', 'things', 'sitewise', 'twinmaker', 'fleetwise',
    'robomaker', 'sensor', 'hub', 'central', 'sphere',
    'digital twins', 'time series',
  ],
  'Media': [
    'media', 'elemental', 'ivs', 'nimble', 'elastic transcoder',
    'streaming', 'broadcast', 'encoder', 'player', 'vod',
    'media services', 'video analyzer', 'video indexer', 'transcoder',
  ],
  'Migration': [
    'migration', 'dms', 'datasync', 'transfer', 'snowball', 'snowcone',
    'mainframe', 'application discovery', 'migrate',
    'transfer appliance',
  ],
  'End User Computing': [
    'workspaces', 'appstream', 'workdocs', 'workmail', 'workspace',
    'virtual desktop', 'remote app',
  ],
  'Customer Engagement': [
    'connect', 'pinpoint', 'simple email', 'chime', 'alexa', 'honeycode',
    'communication', 'voice', 'contact center', 'wickr',
  ],
  'Front-End & Mobile': [
    'amplify', 'device farm', 'location', 'appsync', 'mobile',
  ],
  'Blockchain': [
    'blockchain', 'managed blockchain', 'ledger', 'distributed',
  ],
  'Game': [
    'game', 'gamelift', 'lumberyard', 'playfab', 'gaming',
  ],
  'Satellite': [
    'satellite', 'ground station', 'space',
  ],
  'Quantum': [
    'quantum', 'braket', 'qsharp',
  ],
};

/**
 * Determine category for an icon based on its name
 */
function categorizeIcon(iconName) {
  const nameLower = iconName.toLowerCase();

  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    for (const keyword of keywords) {
      if (nameLower.includes(keyword)) {
        return category;
      }
    }
  }

  return 'Other Services';
}

// ============================================================
// PROVIDER CONFIGURATION
// ============================================================
const PROVIDERS = {
  aws: {
    sourcePath: join(SOURCE_DIR, 'aws-icons'),
    targetPath: join(TARGET_DIR, 'aws'),
    color: '#FF9900',
    pattern: /Arch_(.+?)_48\.svg$/,
    excludePattern: /_Dark_|_16\.svg|_32\.svg|_64\.svg/,
    downloadUrl: 'https://d1.awsstatic.com/webteam/architecture-icons/q3-2024/Asset-Package_07312024.zip',
  },
  azure: {
    sourcePath: join(SOURCE_DIR, 'azure-icons'),
    targetPath: join(TARGET_DIR, 'azure'),
    color: '#0078D4',
    pattern: /\.svg$/,
    excludePattern: null,
    downloadUrl: 'https://arch-center.azureedge.net/icons/Azure_Public_Service_Icons_V21.zip',
  },
  gcp: {
    sourcePath: join(SOURCE_DIR, 'gcp-icons'),
    targetPath: join(TARGET_DIR, 'gcp'),
    color: '#DB4437',
    pattern: /\.svg$/,
    excludePattern: null,
    downloadUrl: null, // GCP doesn't have an official download package
  },
};

// ============================================================
// DOWNLOAD FUNCTIONS
// ============================================================
async function downloadIcons() {
  console.log('\n📥 Downloading official cloud provider icons...\n');

  mkdirSync(SOURCE_DIR, { recursive: true });

  // Download AWS Icons
  console.log('=== AWS Icons ===');
  const awsPath = join(SOURCE_DIR, 'aws-icons');
  if (!existsSync(awsPath)) {
    try {
      console.log('   Downloading from AWS...');
      execSync(`curl -L -o "${SOURCE_DIR}/aws.zip" "${PROVIDERS.aws.downloadUrl}"`, { stdio: 'pipe' });
      execSync(`unzip -q "${SOURCE_DIR}/aws.zip" -d "${SOURCE_DIR}/aws-temp"`, { stdio: 'pipe' });

      // Find the architecture icons folder
      const archDir = readdirSync(join(SOURCE_DIR, 'aws-temp'), { recursive: true, withFileTypes: true })
        .find(f => f.isDirectory() && f.name.includes('Architecture-Service-Icons'));

      if (archDir) {
        execSync(`mv "${join(SOURCE_DIR, 'aws-temp', archDir.name)}" "${awsPath}"`, { stdio: 'pipe' });
      } else {
        // Just use the temp folder
        execSync(`mv "${SOURCE_DIR}/aws-temp" "${awsPath}"`, { stdio: 'pipe' });
      }

      rmSync(join(SOURCE_DIR, 'aws.zip'), { force: true });
      rmSync(join(SOURCE_DIR, 'aws-temp'), { recursive: true, force: true });
      console.log('   ✅ AWS icons downloaded');
    } catch (err) {
      console.log(`   ⚠️ Could not download AWS icons: ${err.message}`);
    }
  } else {
    console.log('   Already exists, skipping');
  }

  // Download Azure Icons
  console.log('\n=== Azure Icons ===');
  const azurePath = join(SOURCE_DIR, 'azure-icons');
  if (!existsSync(azurePath)) {
    try {
      console.log('   Downloading from Azure...');
      execSync(`curl -L -o "${SOURCE_DIR}/azure.zip" "${PROVIDERS.azure.downloadUrl}"`, { stdio: 'pipe' });
      execSync(`unzip -q "${SOURCE_DIR}/azure.zip" -d "${azurePath}"`, { stdio: 'pipe' });
      rmSync(join(SOURCE_DIR, 'azure.zip'), { force: true });
      console.log('   ✅ Azure icons downloaded');
    } catch (err) {
      console.log(`   ⚠️ Could not download Azure icons: ${err.message}`);
    }
  } else {
    console.log('   Already exists, skipping');
  }

  // GCP - Note: No official bulk download available
  console.log('\n=== GCP Icons ===');
  console.log('   GCP icons must be manually obtained from https://cloud.google.com/icons');
  console.log('   Skipping GCP download');
}

// ============================================================
// ICON PROCESSING FUNCTIONS
// ============================================================
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
      return match[1].replace(/-/g, ' ').replace(/\s+/g, ' ').trim();
    }
    // Fallback: just use the filename
    return filename.replace('.svg', '').replace(/[-_]/g, ' ');
  } else if (provider === 'gcp') {
    match = filename.match(/(.+?)-512-color.*\.svg$/);
    if (match) {
      return match[1].replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\s+/g, ' ').trim();
    }
  }

  return filename.replace('.svg', '').replace(/[-_]/g, ' ');
}

function nameToId(name, provider) {
  return `${provider}-${name
    .toLowerCase()
    .replace(/[&()]/g, '')
    .replace(/\s+/g, '-')
    .replace(/--+/g, '-')
    .replace(/^-|-$/g, '')}`;
}

function processProvider(provider, config) {
  console.log(`\n🔍 Processing ${provider.toUpperCase()} icons...`);

  const sourcePaths = Array.isArray(config.sourcePath) ? config.sourcePath : [config.sourcePath];

  let allSvgFiles = [];
  for (const sourcePath of sourcePaths) {
    const svgFiles = findSvgFiles(sourcePath, config.pattern, config.excludePattern);
    allSvgFiles = allSvgFiles.concat(svgFiles);
  }

  console.log(`   Found ${allSvgFiles.length} SVG files`);

  const icons = allSvgFiles.map(svgPath => {
    const filename = basename(svgPath);
    const name = svgToIconName(filename, provider);
    const id = nameToId(name, provider);
    return { id, name, svgPath, filename };
  });

  // Remove duplicates
  const uniqueIcons = {};
  for (const icon of icons) {
    if (!uniqueIcons[icon.id]) {
      uniqueIcons[icon.id] = icon;
    }
  }

  const finalIcons = Object.values(uniqueIcons);
  console.log(`   ${finalIcons.length} unique icons after deduplication`);

  return { provider, icons: finalIcons, color: config.color };
}

// ============================================================
// GENERATION FUNCTIONS
// ============================================================
function convertSvgsToReact(providerData) {
  const { provider, icons } = providerData;
  const svgDir = join(TARGET_DIR, provider, 'svgs');

  mkdirSync(svgDir, { recursive: true });

  console.log(`\n📦 Converting ${icons.length} ${provider.toUpperCase()} SVGs to React components...`);

  for (const icon of icons) {
    const targetPath = join(svgDir, `${icon.id}.svg`);
    const svgContent = readFileSync(icon.svgPath, 'utf8');
    writeFileSync(targetPath, svgContent);
  }

  console.log(`   ✅ Copied ${icons.length} SVG files`);

  const componentsDir = join(TARGET_DIR, provider, 'components');
  mkdirSync(componentsDir, { recursive: true });

  try {
    execSync(`npx @svgr/cli --out-dir "${componentsDir}" --typescript --memo "${svgDir}"`, {
      stdio: 'inherit',
      cwd: join(__dirname, '..'),
    });
    console.log(`   ✅ Generated React components`);

    removeIsolationAttributes(componentsDir);
  } catch (error) {
    console.error(`   ❌ Error converting SVGs:`, error.message);
  }
}

function removeIsolationAttributes(componentsDir) {
  if (!existsSync(componentsDir)) return;

  const files = readdirSync(componentsDir);
  let count = 0;

  for (const file of files) {
    if (!file.endsWith('.tsx')) continue;

    const filePath = join(componentsDir, file);
    const content = readFileSync(filePath, 'utf-8');
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

function generateIconAdapter(providerData) {
  const { provider, icons, color } = providerData;

  console.log(`\n📝 Generating ${provider.toUpperCase()} icon adapter...`);

  const imports = icons.map(icon => {
    const componentName = icon.id
      .split('-')
      .map(word => {
        if (/^(a2i|b2b|3d|5g|2|3|4|5|6|7|8|9|p2p|s3|ec2|i|ii|iii|iv|v|vi|vii|viii|ix|x)$/i.test(word)) {
          return word.toUpperCase();
        }
        return word.charAt(0).toUpperCase() + word.slice(1);
      })
      .join('')
      .replace(/[^a-zA-Z0-9]/g, '');

    return `import ${componentName} from './components/${componentName}';`;
  }).join('\n');

  const iconMapEntries = icons.map(icon => {
    const componentName = icon.id
      .split('-')
      .map(word => {
        if (/^(a2i|b2b|3d|5g|2|3|4|5|6|7|8|9|p2p|s3|ec2|i|ii|iii|iv|v|vi|vii|viii|ix|x)$/i.test(word)) {
          return word.toUpperCase();
        }
        return word.charAt(0).toUpperCase() + word.slice(1);
      })
      .join('')
      .replace(/[^a-zA-Z0-9]/g, '');

    return `  '${icon.id}': createIconComponent(${componentName}),`;
  }).join('\n');

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

const createIconComponent = (IconComponent: any): IconComponent => {
  const WrappedIcon: FC<IconProps> = ({ className, size = 24, color = '${color}' }) => {
    const sizeNum = typeof size === 'string' ? parseInt(size, 10) : size;
    return <IconComponent width={sizeNum} height={sizeNum} fill={color} className={className} />;
  };
  WrappedIcon.displayName = \`${provider.toUpperCase()}Icon\`;
  return WrappedIcon;
};

export const ${provider}IconMap: IconMap = {
${iconMapEntries}
};

export const get${provider.charAt(0).toUpperCase() + provider.slice(1)}Icon = (id: string): IconComponent | undefined => {
  return ${provider}IconMap[id];
};

export const list${provider.charAt(0).toUpperCase() + provider.slice(1)}Icons = (): string[] => {
  return Object.keys(${provider}IconMap);
};

export default ${provider}IconMap;
`;

  const adapterPath = join(TARGET_DIR, provider, 'index.tsx');
  writeFileSync(adapterPath, content, 'utf8');
  console.log(`   ✅ Generated ${adapterPath}`);
}

function generateCategories(providerData) {
  const { provider, icons, color } = providerData;

  console.log(`\n📋 Generating ${provider.toUpperCase()} categories...`);

  // Categorize icons
  const categories = {};

  for (const icon of icons) {
    const category = categorizeIcon(icon.name);
    if (!categories[category]) {
      categories[category] = [];
    }

    categories[category].push({
      id: icon.id,
      label: icon.name,
      color,
      source: provider,
      tags: icon.name.toLowerCase().split(' ').filter(t => t.length > 0),
    });
  }

  // Sort categories: largest first, "Other Services" last
  const sortedCategories = Object.entries(categories).sort(([a, iconsA], [b, iconsB]) => {
    if (a === 'Other Services') return 1;
    if (b === 'Other Services') return -1;
    return iconsB.length - iconsA.length;
  });

  console.log(`   Categorized into ${sortedCategories.length} categories:`);
  for (const [catName, catIcons] of sortedCategories) {
    console.log(`      - ${catName}: ${catIcons.length} icons`);
  }

  const categoryContent = sortedCategories
    .map(([categoryName, categoryIcons]) => {
      const iconsJson = categoryIcons.map(icon => `      {
        id: '${icon.id}',
        label: '${icon.label.replace(/'/g, "\\'")}',
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
 * Total categories: ${sortedCategories.length}
 */

import type { IconCategory } from '../types';

const ${provider}CategoriesArray: IconCategory[] = [
${categoryContent}
];

export const ${provider}Categories: Record<string, IconCategory> = Object.fromEntries(
  ${provider}CategoriesArray.map((cat) => [cat.label, cat])
);

export const getAll${provider.charAt(0).toUpperCase() + provider.slice(1)}Icons = () => {
  return ${provider}CategoriesArray.flatMap((cat) => cat.icons);
};

export default ${provider}CategoriesArray;
`;

  const categoriesPath = join(TARGET_DIR, provider, 'categories.ts');
  writeFileSync(categoriesPath, content, 'utf8');
  console.log(`   ✅ Generated ${categoriesPath}`);
}

// ============================================================
// RECATEGORIZE ONLY MODE
// ============================================================
function extractIconsFromFile(filePath) {
  const content = readFileSync(filePath, 'utf-8');
  const icons = [];

  const iconRegex = /\{\s*id:\s*'([^']+)',\s*label:\s*'([^']+)',\s*color:\s*'([^']+)',\s*source:\s*'([^']+)',\s*tags:\s*(\[[^\]]+\]),?\s*\}/g;

  let match;
  while ((match = iconRegex.exec(content)) !== null) {
    icons.push({
      id: match[1],
      name: match[2],
      label: match[2],
      color: match[3],
      source: match[4],
      tags: JSON.parse(match[5].replace(/'/g, '"')),
    });
  }

  return icons;
}

function recategorizeExisting() {
  console.log('\n🔄 Recategorizing existing cloud provider icons...\n');

  const providers = ['aws', 'azure', 'gcp', 'ibm'];
  const colors = { aws: '#FF9900', azure: '#0078D4', gcp: '#DB4437', ibm: '#054ADA' };

  for (const provider of providers) {
    const catPath = join(TARGET_DIR, provider, 'categories.ts');

    try {
      if (!existsSync(catPath)) {
        console.log(`⚠️ ${provider.toUpperCase()}: categories.ts not found, skipping`);
        continue;
      }

      console.log(`📦 Processing ${provider.toUpperCase()}...`);
      const icons = extractIconsFromFile(catPath);
      console.log(`   Found ${icons.length} icons`);

      if (icons.length > 0) {
        generateCategories({ provider, icons, color: colors[provider] });
      } else {
        console.log(`   ⚠️ No icons found, skipping`);
      }
    } catch (err) {
      console.log(`   ⚠️ Error: ${err.message}`);
    }
  }
}

// ============================================================
// MAIN EXECUTION
// ============================================================
async function main() {
  console.log('🚀 Cloud Provider Icons Processor\n');
  console.log('='.repeat(60));

  if (RECATEGORIZE_ONLY) {
    recategorizeExisting();
    console.log('\n✨ Recategorization complete!');
    return;
  }

  // Download icons
  if (!SKIP_DOWNLOAD) {
    await downloadIcons();
  }

  // Process each provider
  const results = [];

  for (const [provider, config] of Object.entries(PROVIDERS)) {
    if (!existsSync(config.sourcePath)) {
      console.log(`\n⚠️ Skipping ${provider.toUpperCase()}: source not found at ${config.sourcePath}`);
      continue;
    }

    const providerData = processProvider(provider, config);

    if (providerData.icons.length > 0) {
      convertSvgsToReact(providerData);
      generateIconAdapter(providerData);
      generateCategories(providerData);
      results.push(providerData);
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('\n✨ Summary:');
  for (const result of results) {
    console.log(`   ${result.provider.toUpperCase()}: ${result.icons.length} icons`);
  }
  console.log(`   TOTAL: ${results.reduce((sum, r) => sum + r.icons.length, 0)} icons`);
  console.log('\n✅ Done!');
}

main().catch(console.error);
