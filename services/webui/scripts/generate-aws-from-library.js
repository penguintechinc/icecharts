#!/usr/bin/env node
/**
 * Generate AWS icons from the aws-react-icons library
 *
 * This script uses the pre-built aws-react-icons package (awsicons.dev)
 * which has 824+ icons - more comprehensive than manual downloads.
 */

import { writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import * as awsIcons from 'aws-react-icons';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const TARGET_DIR = join(__dirname, '../src/client/components/diagram/icons/aws');

// ============================================================
// CATEGORY KEYWORDS
// ============================================================
const CATEGORY_KEYWORDS = {
  'Compute': [
    'ec2', 'compute', 'lambda', 'batch', 'lightsail', 'elasticbeanstalk',
    'fargate', 'apprunner', 'outposts', 'wavelength', 'vmware', 'parallel',
    'serverless', 'bottlerocket', 'nitro', 'graviton', 'thinkbox',
  ],
  'Containers': [
    'container', 'docker', 'ecs', 'ecr', 'eks', 'copilot',
    'registry', 'redhatopenshiftonaws',
  ],
  'Storage': [
    's3', 'storage', 'ebs', 'efs', 'glacier', 'backup', 'snow', 'fsx',
    'simplestorage', 'elasticblockstore', 'elasticfilesystem', 'file', 'elasticdisaster',
  ],
  'Database': [
    'database', 'rds', 'aurora', 'dynamodb', 'documentdb', 'elasticache',
    'neptune', 'redshift', 'timestream', 'qldb', 'keyspaces', 'memorydb',
    'relational',
  ],
  'Networking': [
    'vpc', 'network', 'route', 'cloudfront', 'apigateway', 'directconnect',
    'globalaccelerator', 'transit', 'privatelink', 'appmesh', 'cloudmap',
    'loadbalancer', 'loadbalancing', 'elasticload', 'nat', 'internetgateway',
    'peering', 'endpoint', 'vpn', 'cloudwan', 'lattice', 'routing', 'accelerator',
  ],
  'Security & Identity': [
    'iam', 'identity', 'cognito', 'directory', 'secrets', 'certificate',
    'acm', 'kms', 'cloudhsm', 'macie', 'inspector', 'detective', 'guardduty',
    'security', 'shield', 'waf', 'access', 'sso', 'verifiedaccess', 'ram',
    'resourceaccess', 'artifact', 'signer', 'paymentcryptography', 'firewall',
  ],
  'Analytics': [
    'analytics', 'athena', 'emr', 'kinesis', 'opensearch', 'quicksight',
    'datapipeline', 'glue', 'lakeformation', 'msk', 'datazone',
    'cleanrooms', 'dataexchange', 'finspace', 'entityresolution',
  ],
  'Machine Learning & AI': [
    'sagemaker', 'machinelearning', 'bedrock', 'comprehend',
    'forecast', 'fraud', 'kendra', 'lex', 'personalize', 'polly', 'rekognition',
    'textract', 'transcribe', 'translate', 'augmented', 'deepracer', 'panorama',
    'healthlake', 'omics', 'neuron', 'deeplens', 'deepcomposer', 'codewhisperer',
    'lookoutfor', 'monitron',
  ],
  'Developer Tools': [
    'codecommit', 'codebuild', 'codedeploy', 'codepipeline', 'codestar',
    'codeguru', 'codeartifact', 'codecatalyst', 'cloud9', 'cloudshell',
    'xray', 'corretto', 'commandline', 'faultinjection', 'toolkit',
    'applicationsignal',
  ],
  'Management & Governance': [
    'cloudwatch', 'cloudtrail', 'config', 'systemsmanager', 'cloudformation',
    'servicecatalog', 'organizations', 'controltower', 'trustedadvisor',
    'proton', 'resilience', 'resource', 'license', 'managedservicesfor',
    'costexplorer', 'costmanagement', 'billing', 'budgets', 'opsworks',
    'managedgrafana', 'managedprometheus', 'launchwizard', 'appconfig',
    'wellarchitected', 'healthdashboard', 'personalhealth', 'chatbot',
  ],
  'Application Integration': [
    'eventbridge', 'sns', 'sqs', 'stepfunctions', 'appflow', 'amazonmq',
    'integration', 'workflow', 'simplequeueservice', 'simplenotification',
    'managedapache', 'expressworkflows', 'appintegrations', 'b2b',
  ],
  'IoT': [
    'iot', 'greengrass', 'things', 'sitewise', 'twinmaker', 'fleetwise',
    'robomaker', 'expresslink', 'devicemanagement', 'devicedefender',
  ],
  'Media': [
    'media', 'elemental', 'ivs', 'nimble', 'elastictranscoder',
    'streaming', 'interactive', 'deadlinecloud',
  ],
  'Migration': [
    'migration', 'dms', 'datasync', 'transfer', 'snowball', 'snowcone',
    'mainframe', 'applicationdiscovery', 'applicationmigration', 'databasemigration',
  ],
  'End User Computing': [
    'workspaces', 'appstream', 'workdocs', 'workmail', 'worklink',
  ],
  'Customer Engagement': [
    'connect', 'pinpoint', 'ses', 'simpleemail', 'chime', 'supplychainmanagement',
    'wickr',
  ],
  'Front-End & Mobile': [
    'amplify', 'devicefarm', 'location', 'appsync', 'mobile',
  ],
  'Blockchain': [
    'blockchain', 'managedblockchain', 'ledger',
  ],
  'Game': [
    'game', 'gamelift', 'gamesparks',
  ],
  'Satellite': [
    'satellite', 'groundstation',
  ],
  'Quantum': [
    'quantum', 'braket',
  ],
};

/**
 * Convert PascalCase component name to readable label
 */
function nameToLabel(name) {
  // Remove prefixes
  let label = name
    .replace(/^ArchitectureService/, '')
    .replace(/^ArchitectureResource/, '')
    .replace(/^ArchitectureCategory/, '')
    .replace(/^ArchitectureGroup/, '');

  // Add spaces between words
  label = label
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
    .replace(/(\d+)/g, ' $1 ')
    .replace(/\s+/g, ' ')
    .trim();

  // Expand common abbreviations
  const expansions = {
    'Ec2': 'EC2',
    'Ec 2': 'EC2',
    'S 3': 'S3',
    'Vpc': 'VPC',
    'Iam': 'IAM',
    'Rds': 'RDS',
    'Sns': 'SNS',
    'Sqs': 'SQS',
    'Kms': 'KMS',
    'Efs': 'EFS',
    'Ebs': 'EBS',
    'Elb': 'ELB',
    'Alb': 'ALB',
    'Nlb': 'NLB',
    'Api': 'API',
    'Cdn': 'CDN',
    'Dns': 'DNS',
    'Waf': 'WAF',
    'Acm': 'ACM',
    'Emr': 'EMR',
    'Ecs': 'ECS',
    'Eks': 'EKS',
    'Ecr': 'ECR',
    'Sso': 'SSO',
    'Mq': 'MQ',
    'Aws': 'AWS',
    'Iot': 'IoT',
    'Ai ': 'AI ',
    'Ml ': 'ML ',
    'Cli': 'CLI',
    'Sdk': 'SDK',
  };

  for (const [short, expanded] of Object.entries(expansions)) {
    label = label.replace(new RegExp(short, 'g'), expanded);
  }

  return label;
}

/**
 * Categorize icon by name
 */
function categorizeIcon(name) {
  const nameLower = name.toLowerCase();

  // Check for Group icons first
  if (nameLower.includes('architecturegroup')) {
    return 'Architecture Groups';
  }

  // Check for Resource icons
  if (nameLower.includes('architectureresource')) {
    return 'Resources';
  }

  // Check for Category icons
  if (nameLower.includes('architecturecategory')) {
    return 'Categories';
  }

  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    for (const keyword of keywords) {
      if (nameLower.includes(keyword.toLowerCase())) {
        return category;
      }
    }
  }

  return 'Other Services';
}

/**
 * Convert name to kebab-case ID
 */
function nameToId(name) {
  return `aws-${name
    .replace(/^ArchitectureService/, '')
    .replace(/^ArchitectureResource/, '')
    .replace(/^ArchitectureCategory/, '')
    .replace(/^ArchitectureGroup/, 'group-')
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1-$2')
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '')
    .replace(/--+/g, '-')
    .replace(/^-|-$/g, '')}`;
}

// Main
console.log('🚀 Generating AWS Icons from aws-react-icons library\n');

const iconNames = Object.keys(awsIcons).filter(name =>
  name.startsWith('Architecture') && !name.includes('Dark')
);

console.log(`Found ${iconNames.length} icons (excluding dark variants)\n`);

// Build icons array
const icons = iconNames.map(name => ({
  componentName: name,
  id: nameToId(name),
  label: nameToLabel(name),
  name: nameToLabel(name),
}));

// Categorize icons
const categories = {};

for (const icon of icons) {
  const category = categorizeIcon(icon.componentName);
  if (!categories[category]) {
    categories[category] = [];
  }
  categories[category].push({
    id: icon.id,
    label: icon.label,
    color: '#FF9900',
    source: 'aws',
    tags: icon.label.toLowerCase().split(' ').filter(t => t.length > 1),
  });
}

// Sort categories
const sortedCategories = Object.entries(categories).sort(([a, iconsA], [b, iconsB]) => {
  // Keep special categories at top
  const order = ['Architecture Groups', 'Categories', 'Resources', 'Other Services'];
  const aIdx = order.indexOf(a);
  const bIdx = order.indexOf(b);

  if (aIdx >= 0 && bIdx >= 0) return aIdx - bIdx;
  if (aIdx >= 0) return 1;
  if (bIdx >= 0) return -1;

  return iconsB.length - iconsA.length;
});

console.log(`Categorized into ${sortedCategories.length} categories:`);
for (const [catName, catIcons] of sortedCategories) {
  console.log(`   - ${catName}: ${catIcons.length} icons`);
}

// Generate categories.ts
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
    source: 'aws',
    icons: [
${iconsJson}
    ],
  }`;
  })
  .join(',\n');

const categoriesContent = `/**
 * AWS Icon Categories - Auto-generated from aws-react-icons
 *
 * This file is auto-generated from the aws-react-icons library (awsicons.dev).
 * To regenerate, run: node scripts/generate-aws-from-library.js
 *
 * Total icons: ${icons.length}
 * Total categories: ${sortedCategories.length}
 */

import type { IconCategory } from '../types';

const awsCategoriesArray: IconCategory[] = [
${categoryContent}
];

export const awsCategories: Record<string, IconCategory> = Object.fromEntries(
  awsCategoriesArray.map((cat) => [cat.label, cat])
);

export const getAllAwsIcons = () => {
  return awsCategoriesArray.flatMap((cat) => cat.icons);
};

export default awsCategoriesArray;
`;

writeFileSync(join(TARGET_DIR, 'categories.ts'), categoriesContent, 'utf8');
console.log(`\n✅ Generated ${TARGET_DIR}/categories.ts`);

// Generate index.tsx
const imports = icons.map(icon =>
  `import { ${icon.componentName} } from 'aws-react-icons';`
).join('\n');

const iconMapEntries = icons.map(icon =>
  `  '${icon.id}': createIconComponent(${icon.componentName}),`
).join('\n');

const indexContent = `/**
 * AWS Icon Adapter - Auto-generated from aws-react-icons
 *
 * This file is auto-generated from the aws-react-icons library (awsicons.dev).
 * To regenerate, run: node scripts/generate-aws-from-library.js
 *
 * Total icons: ${icons.length}
 */

import { FC } from 'react';
import type { IconProps, IconComponent, IconMap } from '../types';

${imports}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const createIconComponent = (IconComponent: any): IconComponent => {
  const WrappedIcon: FC<IconProps> = ({ className, size = 24 }) => {
    const sizeNum = typeof size === 'string' ? parseInt(size, 10) : size;
    return <IconComponent width={sizeNum} height={sizeNum} className={className} />;
  };
  WrappedIcon.displayName = 'AWSIcon';
  return WrappedIcon;
};

export const awsIconMap: IconMap = {
${iconMapEntries}
};

export const getAwsIcon = (id: string): IconComponent | undefined => {
  return awsIconMap[id];
};

export const listAwsIcons = (): string[] => {
  return Object.keys(awsIconMap);
};

export default awsIconMap;
`;

writeFileSync(join(TARGET_DIR, 'index.tsx'), indexContent, 'utf8');
console.log(`✅ Generated ${TARGET_DIR}/index.tsx`);

console.log(`\n✨ Done! Generated ${icons.length} AWS icons in ${sortedCategories.length} categories`);
