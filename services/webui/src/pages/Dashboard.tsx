import React from 'react';

const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-amber-400 mb-4">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Welcome to IceCharts - Real-time collaborative diagramming
        </p>
      </div>
    </div>
  );
};

export default Dashboard;
