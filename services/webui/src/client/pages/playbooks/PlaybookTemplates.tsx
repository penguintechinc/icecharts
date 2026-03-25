/**
 * PlaybookTemplates - Browse and use playbook templates
 */

import React from 'react';
import { Link } from 'react-router-dom';

const PlaybookTemplates: React.FC = () => {
  // Placeholder templates - will come from API
  const templates = [
    {
      id: '1',
      name: 'Webhook to Slack',
      description: 'Receive webhook events and send notifications to Slack',
      category: 'Notifications',
      nodes: 3,
    },
    {
      id: '2',
      name: 'Scheduled Data Sync',
      description: 'Periodically sync data between two REST APIs',
      category: 'Data Integration',
      nodes: 4,
    },
    {
      id: '3',
      name: 'Form to Email',
      description: 'Process form submissions and send email confirmations',
      category: 'Forms',
      nodes: 3,
    },
    {
      id: '4',
      name: 'GitHub to Discord',
      description: 'Post GitHub events to Discord channels',
      category: 'DevOps',
      nodes: 4,
    },
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Playbook Templates</h1>
          <p className="text-ice-navy-300 mt-1">
            Start with a pre-built workflow template
          </p>
        </div>
        <Link
          to="/playbooks"
          className="text-ice-gold-400 hover:text-ice-gold-300 text-sm"
        >
          Back to Playbooks
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <div
            key={template.id}
            className="p-4 bg-ice-navy-800 rounded-lg border border-ice-navy-700 hover:border-ice-gold-500/50 transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="p-2 bg-ice-gold-500/20 rounded-lg">
                <svg className="w-6 h-6 text-ice-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <span className="text-xs text-ice-navy-400 bg-ice-navy-700 px-2 py-1 rounded">
                {template.category}
              </span>
            </div>

            <h3 className="text-white font-medium mb-1">{template.name}</h3>
            <p className="text-ice-navy-400 text-sm mb-3">{template.description}</p>

            <div className="flex items-center justify-between">
              <span className="text-ice-navy-500 text-xs">{template.nodes} nodes</span>
              <button className="px-3 py-1 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 text-sm font-medium rounded transition-colors">
                Use Template
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Coming soon notice */}
      <div className="mt-8 p-6 bg-ice-navy-800/50 rounded-lg border border-ice-navy-700 text-center">
        <svg className="w-12 h-12 text-ice-navy-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <p className="text-ice-navy-400">
          More templates coming soon! You can also save your playbooks as templates.
        </p>
      </div>
    </div>
  );
};

export default PlaybookTemplates;
