import React from 'react';
import { useParams } from 'react-router-dom';

const DrawingEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-amber-400 mb-4">
          Drawing Editor
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Drawing ID: {id}
        </p>
        <p className="text-gray-500 dark:text-gray-500 mt-4">
          The drawing editor with @xyflow/react will be implemented here.
        </p>
      </div>
    </div>
  );
};

export default DrawingEditor;
