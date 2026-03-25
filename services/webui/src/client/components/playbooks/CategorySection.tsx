/**
 * CategorySection - Top-level collapsible category for the node palette
 *
 * Groups related nodes/connectors under a single expandable header.
 * Used for General, PenguinTech, and External categories.
 */

import React from 'react';
import { getConnectorLogo } from '../../../assets/logos';

interface CategorySectionProps {
  /** Category name (e.g., "General", "PenguinTech", "External") */
  name: string;
  /** Category icon */
  icon: string;
  /** Category accent color (hex) */
  color: string;
  /** Total count of nodes/items in this category */
  count: number;
  /** Whether the category is expanded */
  expanded: boolean;
  /** Toggle expansion handler */
  onToggle: () => void;
  /** Child content (subsections or ConnectorSections) */
  children: React.ReactNode;
}

/**
 * Chevron icon for expandable sections
 */
const ChevronIcon: React.FC<{ expanded: boolean }> = ({ expanded }) => (
  <svg
    className={`w-4 h-4 flex-shrink-0 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
);

/**
 * CategorySection - Main component
 *
 * Renders a top-level category with a header and expandable content.
 * Visually distinct from ConnectorSection with bolder styling.
 */
export const CategorySection: React.FC<CategorySectionProps> = ({
  name,
  icon,
  color,
  count,
  expanded,
  onToggle,
  children,
}) => {
  return (
    <div className="category-section mb-2">
      {/* Category header - more prominent than connector headers */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg bg-ice-navy-700/80 hover:bg-ice-navy-600 text-white transition-colors font-semibold text-sm"
        style={{
          borderLeftWidth: '4px',
          borderLeftColor: color,
        }}
      >
        <ChevronIcon expanded={expanded} />
        {(() => {
          const logoSrc = getConnectorLogo(icon);
          return logoSrc.startsWith('/') || logoSrc.startsWith('http') || logoSrc.includes('data:') ? (
            <img src={logoSrc} alt={name} className="w-5 h-5 object-contain" />
          ) : (
            <span className="text-lg">{icon}</span>
          );
        })()}
        <span className="flex-1 text-left">{name}</span>
        <span
          className="inline-flex items-center justify-center min-w-6 h-6 px-1.5 text-xs font-bold rounded-full"
          style={{
            backgroundColor: `${color}30`,
            color: color,
          }}
        >
          {count}
        </span>
      </button>

      {/* Category content */}
      {expanded && (
        <div className="mt-2 space-y-1 pl-1">
          {children}
        </div>
      )}
    </div>
  );
};

export default CategorySection;
