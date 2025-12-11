import React, { useState } from 'react';
import IconSearch from './IconSearch';
import type { IconDefinition } from '../types';
import { iconMap } from '../icons';

/**
 * Example usage of the IconSearch component
 *
 * This demonstrates:
 * - How to set up the component with icon data
 * - How to handle icon selection
 * - How to display the selected icon
 */
export default function IconSearchExample() {
  const [selectedIcon, setSelectedIcon] = useState<IconDefinition | null>(null);

  // Example icon definitions - in a real app, these would come from your icon system
  const exampleIcons: IconDefinition[] = [
    // Cloud Providers
    { id: 'aws', label: 'AWS', source: 'aws', color: '#FF9900', tags: ['amazon', 'cloud', 'provider'] },
    { id: 'azure', label: 'Azure', source: 'azure', color: '#0078D4', tags: ['microsoft', 'cloud', 'provider'] },
    { id: 'gcp', label: 'GCP', source: 'gcp', color: '#4285F4', tags: ['google', 'cloud', 'provider'] },

    // Compute
    { id: 'server', label: 'Server', source: 'internal', color: '#6B7280', tags: ['infrastructure', 'compute'] },
    { id: 'vm', label: 'Virtual Machine', source: 'internal', color: '#6B7280', tags: ['infrastructure', 'compute'] },
    { id: 'container', label: 'Container', source: 'internal', color: '#6B7280', tags: ['docker', 'containerization'] },
    { id: 'lambda', label: 'Lambda/Function', source: 'aws', color: '#FF9900', tags: ['serverless', 'function', 'compute'] },

    // Database
    { id: 'database', label: 'Database', source: 'internal', color: '#6B7280', tags: ['storage', 'data'] },
    { id: 'postgres', label: 'PostgreSQL', source: 'internal', color: '#336791', tags: ['database', 'sql'] },
    { id: 'mysql', label: 'MySQL', source: 'internal', color: '#4479A1', tags: ['database', 'sql'] },
    { id: 'mongodb', label: 'MongoDB', source: 'internal', color: '#47A248', tags: ['database', 'nosql'] },
    { id: 'redis', label: 'Redis', source: 'internal', color: '#DC382D', tags: ['database', 'cache'] },

    // Networking
    { id: 'network', label: 'Network', source: 'internal', color: '#6B7280', tags: ['networking', 'connection'] },
    { id: 'router', label: 'Router', source: 'internal', color: '#6B7280', tags: ['networking', 'device'] },
    { id: 'firewall', label: 'Firewall', source: 'internal', color: '#EF4444', tags: ['security', 'networking'] },
    { id: 'loadbalancer', label: 'Load Balancer', source: 'internal', color: '#8B5CF6', tags: ['networking', 'distribution'] },
    { id: 'dns', label: 'DNS', source: 'internal', color: '#3B82F6', tags: ['networking', 'resolution'] },

    // Security
    { id: 'lock', label: 'Lock', source: 'internal', color: '#6B7280', tags: ['security', 'encryption'] },
    { id: 'key', label: 'Key', source: 'internal', color: '#F59E0B', tags: ['security', 'authentication'] },
    { id: 'certificate', label: 'Certificate', source: 'internal', color: '#3B82F6', tags: ['security', 'ssl'] },

    // Monitoring
    { id: 'monitoring', label: 'Monitoring', source: 'internal', color: '#3B82F6', tags: ['observability', 'metrics'] },
    { id: 'logs', label: 'Logs', source: 'internal', color: '#6B7280', tags: ['observability', 'logging'] },
    { id: 'metrics', label: 'Metrics', source: 'internal', color: '#10B981', tags: ['observability', 'monitoring'] },

    // DevOps
    { id: 'git', label: 'Git', source: 'internal', color: '#F05032', tags: ['version-control', 'scm'] },
    { id: 'jenkins', label: 'Jenkins', source: 'internal', color: '#D24939', tags: ['ci/cd', 'automation'] },

    // Users
    { id: 'user', label: 'User', source: 'internal', color: '#6B7280', tags: ['people', 'person'] },
    { id: 'users', label: 'Users', source: 'internal', color: '#6B7280', tags: ['people', 'team'] },
    { id: 'admin', label: 'Admin', source: 'internal', color: '#EF4444', tags: ['people', 'administration'] },

    // APIs
    { id: 'api', label: 'API', source: 'internal', color: '#6B7280', tags: ['integration', 'interface'] },
    { id: 'restapi', label: 'REST API', source: 'internal', color: '#10B981', tags: ['api', 'integration'] },
    { id: 'graphql', label: 'GraphQL', source: 'internal', color: '#E535AB', tags: ['api', 'query'] },
  ];

  const handleIconSelect = (icon: IconDefinition) => {
    setSelectedIcon(icon);
    console.log('Selected icon:', icon);
  };

  return (
    <div className="p-8 bg-dark-950 min-h-screen">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-2">Icon Search Example</h1>
        <p className="text-dark-400 mb-8">
          Start typing to search through all available icons. Use arrow keys to navigate, Enter to select, or Escape to close.
        </p>

        {/* Icon Search Component */}
        <div className="mb-8">
          <label className="block text-sm font-medium text-dark-300 mb-2">
            Search for an icon
          </label>
          <IconSearch
            onSelect={handleIconSelect}
            allIcons={exampleIcons}
            placeholder="Type to search (e.g., 'database', 'aws', 'security')..."
            iconMap={iconMap}
          />
        </div>

        {/* Selected Icon Display */}
        {selectedIcon && (
          <div className="bg-dark-900 border border-dark-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Selected Icon</h2>
            <div className="flex items-center gap-6">
              {/* Icon Preview */}
              <div className="flex-shrink-0">
                {iconMap[selectedIcon.id] ? (
                  React.createElement(iconMap[selectedIcon.id], {
                    className: 'w-16 h-16 text-gray-300',
                  })
                ) : (
                  <div className="w-16 h-16 bg-dark-700 rounded flex items-center justify-center">
                    <span className="text-xl text-dark-400">?</span>
                  </div>
                )}
              </div>

              {/* Icon Details */}
              <div className="flex-1">
                <p className="text-sm text-dark-400 mb-1">Icon ID</p>
                <p className="text-lg font-medium text-white mb-3">{selectedIcon.id}</p>

                <p className="text-sm text-dark-400 mb-1">Label</p>
                <p className="text-white mb-3">{selectedIcon.label}</p>

                <p className="text-sm text-dark-400 mb-1">Source</p>
                <div className="flex items-center gap-2">
                  <span className="inline-block px-3 py-1 text-sm font-medium rounded border bg-blue-500/20 text-blue-300 border-blue-500/30">
                    {selectedIcon.source.charAt(0).toUpperCase() + selectedIcon.source.slice(1)}
                  </span>
                </div>

                {selectedIcon.tags && selectedIcon.tags.length > 0 && (
                  <>
                    <p className="text-sm text-dark-400 mt-3 mb-2">Tags</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedIcon.tags.map(tag => (
                        <span
                          key={tag}
                          className="px-2 py-1 text-xs rounded bg-dark-700 text-dark-300 border border-dark-600"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {!selectedIcon && (
          <div className="bg-dark-900 border border-dark-700 rounded-lg p-6 text-center">
            <p className="text-dark-400">Select an icon to see its details here</p>
          </div>
        )}

        {/* Usage Instructions */}
        <div className="mt-12 bg-dark-900 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Usage Instructions</h2>
          <ul className="space-y-2 text-dark-300 text-sm">
            <li className="flex gap-2">
              <span className="text-blue-400 font-medium">Type</span>
              <span>to search icons by label, tags, or fuzzy matching</span>
            </li>
            <li className="flex gap-2">
              <span className="text-blue-400 font-medium">↑↓</span>
              <span>navigate through results</span>
            </li>
            <li className="flex gap-2">
              <span className="text-blue-400 font-medium">Enter</span>
              <span>select the highlighted icon</span>
            </li>
            <li className="flex gap-2">
              <span className="text-blue-400 font-medium">Escape</span>
              <span>close the dropdown</span>
            </li>
            <li className="flex gap-2">
              <span className="text-blue-400 font-medium">Click</span>
              <span>on any result to select it</span>
            </li>
          </ul>
        </div>

        {/* Search Tips */}
        <div className="mt-8 bg-dark-900 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Search Tips</h2>
          <div className="grid grid-cols-2 gap-4 text-sm text-dark-400">
            <div>
              <p className="font-medium text-white mb-2">Try searching for:</p>
              <ul className="space-y-1 text-xs">
                <li className="text-blue-300">• "aws" or "azure"</li>
                <li className="text-blue-300">• "database" or "db"</li>
                <li className="text-blue-300">• "security" or "lock"</li>
                <li className="text-blue-300">• "server" or "compute"</li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-white mb-2">Features:</p>
              <ul className="space-y-1 text-xs">
                <li className="text-blue-300">• Fuzzy matching support</li>
                <li className="text-blue-300">• Tag-based search</li>
                <li className="text-blue-300">• Relevance scoring</li>
                <li className="text-blue-300">• Max 30 results</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
