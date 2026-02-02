/**
 * GCP Icon Adapter - Auto-generated
 *
 * This file is auto-generated from official GCP icons.
 * To regenerate, run: npm run process-cloud-icons
 *
 * Total icons: 45
 */

import { FC } from 'react';
import type { IconProps, IconComponent, IconMap } from '../types';

import GcpAimachineLearning from './components/GcpAimachineLearning';
import GcpAgents from './components/GcpAgents';
import GcpBusinessIntelligence from './components/GcpBusinessIntelligence';
import GcpCollaboration from './components/GcpCollaboration';
import GcpCompute from './components/GcpCompute';
import GcpContainers from './components/GcpContainers';
import GcpDataAnalytics from './components/GcpDataAnalytics';
import GcpDatabases from './components/GcpDatabases';
import GcpDevOps from './components/GcpDevOps';
import GcpDeveloperTools from './components/GcpDeveloperTools';
import GcpHybridMulticloud from './components/GcpHybridMulticloud';
import GcpIntegrationServices from './components/GcpIntegrationServices';
import GcpManagementTools from './components/GcpManagementTools';
import GcpMapsGeospatial from './components/GcpMapsGeospatial';
import GcpMarketplace from './components/GcpMarketplace';
import GcpMediaServices from './components/GcpMediaServices';
import GcpMigration from './components/GcpMigration';
import GcpMixedReality from './components/GcpMixedReality';
import GcpNetworking from './components/GcpNetworking';
import GcpObservability from './components/GcpObservability';
import GcpOperations from './components/GcpOperations';
import GcpSecurityIdentity from './components/GcpSecurityIdentity';
import GcpServerlessComputing from './components/GcpServerlessComputing';
import GcpStorage from './components/GcpStorage';
import GcpWebMobile from './components/GcpWebMobile';
import GcpWeb3 from './components/GcpWeb3';
import GcpAihypercomputer from './components/GcpAihypercomputer';
import GcpAlloyDb from './components/GcpAlloyDb';
import GcpAnthos from './components/GcpAnthos';
import GcpApigee from './components/GcpApigee';
import GcpBigQuery from './components/GcpBigQuery';
import GcpCloudRun from './components/GcpCloudRun';
import GcpCloudSql from './components/GcpCloudSql';
import GcpCloudSpanner from './components/GcpCloudSpanner';
import GcpCloudStorage from './components/GcpCloudStorage';
import GcpComputeEngine from './components/GcpComputeEngine';
import GcpDistributedCloud from './components/GcpDistributedCloud';
import GcpGke from './components/GcpGke';
import GcpHyperdisk from './components/GcpHyperdisk';
import GcpLooker from './components/GcpLooker';
import GcpMandiant from './components/GcpMandiant';
import GcpSecurityCommandCenter from './components/GcpSecurityCommandCenter';
import GcpSecOps from './components/GcpSecOps';
import GcpThreatIntelligence from './components/GcpThreatIntelligence';
import GcpVertexAi from './components/GcpVertexAi';

/**
 * Wrapper function to create a normalized icon component
 */
const createIconComponent = (IconComponent: any): IconComponent => {
  const WrappedIcon: FC<IconProps> = ({
    className,
    size = 24,
    color = '#DB4437',
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
  WrappedIcon.displayName = `GCPIcon`;
  return WrappedIcon;
};

/**
 * GCP Icon Map - All 45 official icons
 */
export const gcpIconMap: IconMap = {
  'gcp-aimachine-learning': createIconComponent(GcpAimachineLearning),
  'gcp-agents': createIconComponent(GcpAgents),
  'gcp-business-intelligence': createIconComponent(GcpBusinessIntelligence),
  'gcp-collaboration': createIconComponent(GcpCollaboration),
  'gcp-compute': createIconComponent(GcpCompute),
  'gcp-containers': createIconComponent(GcpContainers),
  'gcp-data-analytics': createIconComponent(GcpDataAnalytics),
  'gcp-databases': createIconComponent(GcpDatabases),
  'gcp-dev-ops': createIconComponent(GcpDevOps),
  'gcp-developer-tools': createIconComponent(GcpDeveloperTools),
  'gcp-hybrid-multicloud': createIconComponent(GcpHybridMulticloud),
  'gcp-integration-services': createIconComponent(GcpIntegrationServices),
  'gcp-management-tools': createIconComponent(GcpManagementTools),
  'gcp-maps-geospatial': createIconComponent(GcpMapsGeospatial),
  'gcp-marketplace': createIconComponent(GcpMarketplace),
  'gcp-media-services': createIconComponent(GcpMediaServices),
  'gcp-migration': createIconComponent(GcpMigration),
  'gcp-mixed-reality': createIconComponent(GcpMixedReality),
  'gcp-networking': createIconComponent(GcpNetworking),
  'gcp-observability': createIconComponent(GcpObservability),
  'gcp-operations': createIconComponent(GcpOperations),
  'gcp-security-identity': createIconComponent(GcpSecurityIdentity),
  'gcp-serverless-computing': createIconComponent(GcpServerlessComputing),
  'gcp-storage': createIconComponent(GcpStorage),
  'gcp-web-mobile': createIconComponent(GcpWebMobile),
  'gcp-web3': createIconComponent(GcpWeb3),
  'gcp-aihypercomputer': createIconComponent(GcpAihypercomputer),
  'gcp-alloy-db': createIconComponent(GcpAlloyDb),
  'gcp-anthos': createIconComponent(GcpAnthos),
  'gcp-apigee': createIconComponent(GcpApigee),
  'gcp-big-query': createIconComponent(GcpBigQuery),
  'gcp-cloud-run': createIconComponent(GcpCloudRun),
  'gcp-cloud-sql': createIconComponent(GcpCloudSql),
  'gcp-cloud-spanner': createIconComponent(GcpCloudSpanner),
  'gcp-cloud-storage': createIconComponent(GcpCloudStorage),
  'gcp-compute-engine': createIconComponent(GcpComputeEngine),
  'gcp-distributed-cloud': createIconComponent(GcpDistributedCloud),
  'gcp-gke': createIconComponent(GcpGke),
  'gcp-hyperdisk': createIconComponent(GcpHyperdisk),
  'gcp-looker': createIconComponent(GcpLooker),
  'gcp-mandiant': createIconComponent(GcpMandiant),
  'gcp-security-command-center': createIconComponent(GcpSecurityCommandCenter),
  'gcp-sec-ops': createIconComponent(GcpSecOps),
  'gcp-threat-intelligence': createIconComponent(GcpThreatIntelligence),
  'gcp-vertex-ai': createIconComponent(GcpVertexAi),
};

/**
 * Get an icon component by ID
 */
export const getGcpIcon = (id: string): IconComponent | undefined => {
  return gcpIconMap[id];
};

/**
 * List all available GCP icon IDs
 */
export const listGcpIcons = (): string[] => {
  return Object.keys(gcpIconMap);
};

export default gcpIconMap;
