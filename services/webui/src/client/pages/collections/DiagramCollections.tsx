/**
 * DiagramCollections - Collections for organizing diagrams
 */

import React from 'react';
import { Link } from 'react-router-dom';

const DiagramCollections: React.FC = () => {
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Diagram Collections</h1>
          <p className="text-ice-navy-300 mt-1">
            Organize your diagrams into collections
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 font-medium rounded-lg transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Collection
        </button>
      </div>

      {/* Empty state */}
      <div className="flex flex-col items-center justify-center min-h-[400px] bg-ice-navy-800/50 rounded-lg border border-ice-navy-700">
        <svg className="w-16 h-16 text-ice-navy-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <h3 className="text-lg font-medium text-white mb-2">No collections yet</h3>
        <p className="text-ice-navy-400 mb-4 text-center max-w-md">
          Collections help you organize diagrams by project, team, or category.
          Diagram collections are separate from playbook collections.
        </p>
        <button className="px-4 py-2 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 font-medium rounded-lg transition-colors">
          Create Collection
        </button>
      </div>

      {/* Info note */}
      <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-blue-400 font-medium">Diagram collections are separate</p>
            <p className="text-ice-navy-300 text-sm mt-1">
              Diagram collections only contain diagrams. For playbook collections, visit the{' '}
              <Link to="/collections/playbooks" className="text-ice-gold-400 hover:underline">
                Playbook Collections
              </Link>{' '}
              page.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiagramCollections;
