/**
 * ConnectorSection - Dynamic node palette section for connectors
 *
 * Renders a collapsible section for a connector's nodes (triggers, actions, transforms)
 * in the PlaybookEditor's left palette. Nodes are draggable onto the canvas.
 */

import React, { DragEvent } from 'react';
import type { Connector } from '../../types/connector';
import { getConnectorLogo } from '../../../assets/logos';

interface ConnectorSectionProps {
  /** Connector definition with triggers, actions, transforms */
  connector: Connector;
  /** Drag start handler from PlaybookEditor */
  onDragStart: (e: DragEvent<HTMLDivElement>, nodeType: string, category: string) => void;
  /** Which subsections are expanded */
  expandedSubsections: Record<string, boolean>;
  /** Toggle subsection expansion */
  onToggleSubsection: (key: string) => void;
  /** Whether the main connector section is expanded */
  expanded: boolean;
  /** Toggle main section */
  onToggle: () => void;
}

/**
 * Color mapping for node categories
 */
const categoryColors = {
  triggers: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    hover: 'hover:bg-green-500/20',
    text: 'text-green-400',
    badge: 'bg-green-500/30',
  },
  actions: {
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    hover: 'hover:bg-orange-500/20',
    text: 'text-orange-400',
    badge: 'bg-orange-500/30',
  },
  transforms: {
    bg: 'bg-cyan-500/10',
    border: 'border-cyan-500/30',
    hover: 'hover:bg-cyan-500/20',
    text: 'text-cyan-400',
    badge: 'bg-cyan-500/30',
  },
  conditionals: {
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/30',
    hover: 'hover:bg-purple-500/20',
    text: 'text-purple-400',
    badge: 'bg-purple-500/30',
  },
} as const;

/**
 * Chevron icon for expandable sections
 */
const ChevronIcon: React.FC<{ expanded: boolean; className?: string }> = ({ expanded, className = '' }) => (
  <svg
    className={`w-4 h-4 flex-shrink-0 transition-transform duration-200 ${expanded ? 'rotate-90' : ''} ${className}`}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
);

/**
 * Individual node item in the palette
 */
interface NodeItemProps {
  nodeType: string;
  label: string;
  icon: string;
  description: string;
  category: 'triggers' | 'actions' | 'transforms' | 'conditionals';
  connectorColor: string;
  onDragStart: (e: DragEvent<HTMLDivElement>, nodeType: string, category: string) => void;
}

const NodeItem: React.FC<NodeItemProps> = ({
  nodeType,
  label,
  icon,
  description,
  category,
  connectorColor,
  onDragStart,
}) => {
  const colors = categoryColors[category];

  return (
    <div
      className={`p-3 ${colors.bg} ${colors.border} border rounded-lg cursor-move ${colors.hover} transition-colors group`}
      draggable
      onDragStart={(e) => onDragStart(e, nodeType, category)}
      title={description}
      style={{
        borderLeftWidth: '3px',
        borderLeftColor: connectorColor,
      }}
    >
      <div className="flex items-center gap-2">
        {(() => {
          if (!icon) return <span className="text-lg">•</span>;
          const logoSrc = getConnectorLogo(icon);
          return logoSrc.startsWith('/') || logoSrc.startsWith('http') || logoSrc.includes('data:') ? (
            <img src={logoSrc} alt={label} className="w-5 h-5 object-contain flex-shrink-0" />
          ) : (
            <span className="text-lg">{icon}</span>
          );
        })()}
        <span className={`${colors.text} text-sm flex-1 truncate`}>{label}</span>
      </div>
      <p className="text-ice-navy-400 text-xs mt-1 opacity-0 group-hover:opacity-100 transition-opacity line-clamp-2">
        {description}
      </p>
    </div>
  );
};

/**
 * Subsection for triggers, actions, transforms, or conditionals within a connector
 */
interface SubsectionProps {
  title: string;
  category: 'triggers' | 'actions' | 'transforms' | 'conditionals';
  items: Array<{
    id: string;
    name: string;
    icon?: string;
    description: string;
  }>;
  connectorId: string;
  connectorIcon: string;
  connectorColor: string;
  expanded: boolean;
  onToggle: () => void;
  onDragStart: (e: DragEvent<HTMLDivElement>, nodeType: string, category: string) => void;
}

const Subsection: React.FC<SubsectionProps> = ({
  title,
  category,
  items,
  connectorId,
  connectorIcon,
  connectorColor,
  expanded,
  onToggle,
  onDragStart,
}) => {
  if (items.length === 0) return null;

  const colors = categoryColors[category];

  return (
    <div className="ml-2">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-ice-navy-300 hover:text-white hover:bg-ice-navy-700/50 transition-colors text-xs"
      >
        <ChevronIcon expanded={expanded} className="w-3 h-3" />
        <span className="flex-1 text-left capitalize">{title}</span>
        <span className={`inline-flex items-center justify-center px-1.5 h-4 text-xs ${colors.badge} ${colors.text} rounded-full`}>
          {items.length}
        </span>
      </button>
      {expanded && (
        <div className="mt-1.5 space-y-1.5 pl-2">
          {items.map((item) => {
            // Build node type following the pattern: {category_singular}_{connector}_{id}
            const categorySingularMap: Record<string, string> = {
              triggers: 'trigger',
              actions: 'action',
              transforms: 'transform',
              conditionals: 'conditional',
            };
            const categorySingular = categorySingularMap[category] || category;
            const nodeType = `${categorySingular}_${connectorId}_${item.id}`;

            return (
              <NodeItem
                key={nodeType}
                nodeType={nodeType}
                label={item.name}
                icon={item.icon || connectorIcon}
                description={item.description}
                category={category}
                connectorColor={connectorColor}
                onDragStart={onDragStart}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

/**
 * ConnectorSection - Main component
 *
 * Renders a connector as a collapsible section in the node palette with
 * subsections for triggers, actions, and transforms.
 */
export const ConnectorSection: React.FC<ConnectorSectionProps> = ({
  connector,
  onDragStart,
  expandedSubsections,
  onToggleSubsection,
  expanded,
  onToggle,
}) => {
  const totalNodes = connector.triggers.length + connector.actions.length + connector.transforms.length;

  return (
    <div className="category-section">
      {/* Connector header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-ice-navy-700 hover:bg-ice-navy-600 text-ice-navy-200 hover:text-white transition-colors font-medium text-sm"
        style={{
          borderLeftWidth: '3px',
          borderLeftColor: connector.color,
        }}
      >
        <ChevronIcon expanded={expanded} />
        {(() => {
          const logoSrc = getConnectorLogo(connector.icon);
          return logoSrc.startsWith('/') || logoSrc.startsWith('http') || logoSrc.includes('data:') ? (
            <img src={logoSrc} alt={connector.name} className="w-5 h-5 object-contain" />
          ) : (
            <span className="text-base">{connector.icon}</span>
          );
        })()}
        <span className="flex-1 text-left">{connector.name}</span>
        <span
          className="inline-flex items-center justify-center w-5 h-5 text-xs rounded-full"
          style={{
            backgroundColor: `${connector.color}30`,
            color: connector.color,
          }}
        >
          {totalNodes}
        </span>
      </button>

      {/* Connector content - subsections */}
      {expanded && (
        <div className="mt-2 space-y-1">
          {/* Triggers subsection */}
          <Subsection
            title="Triggers"
            category="triggers"
            items={connector.triggers}
            connectorId={connector.id}
            connectorIcon={connector.icon}
            connectorColor={connector.color}
            expanded={expandedSubsections[`${connector.id}-triggers`] ?? false}
            onToggle={() => onToggleSubsection(`${connector.id}-triggers`)}
            onDragStart={onDragStart}
          />

          {/* Actions subsection */}
          <Subsection
            title="Actions"
            category="actions"
            items={connector.actions}
            connectorId={connector.id}
            connectorIcon={connector.icon}
            connectorColor={connector.color}
            expanded={expandedSubsections[`${connector.id}-actions`] ?? false}
            onToggle={() => onToggleSubsection(`${connector.id}-actions`)}
            onDragStart={onDragStart}
          />

          {/* Transforms subsection */}
          <Subsection
            title="Transforms"
            category="transforms"
            items={connector.transforms}
            connectorId={connector.id}
            connectorIcon={connector.icon}
            connectorColor={connector.color}
            expanded={expandedSubsections[`${connector.id}-transforms`] ?? false}
            onToggle={() => onToggleSubsection(`${connector.id}-transforms`)}
            onDragStart={onDragStart}
          />
        </div>
      )}
    </div>
  );
};

export { Subsection };
export default ConnectorSection;
