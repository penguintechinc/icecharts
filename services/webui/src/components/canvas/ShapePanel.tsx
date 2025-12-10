import React, { useState } from 'react';
import type { CloudProvider } from './nodes/CloudProviderNode';

interface ShapePanelProps {
  onAddNode: (nodeType: string, nodeData: any) => void;
}

interface Category {
  id: string;
  name: string;
  icon: React.ReactNode;
  items: ShapeItem[];
}

interface ShapeItem {
  id: string;
  name: string;
  nodeType: string;
  nodeData: any;
  preview: React.ReactNode;
}

const ShapePanel: React.FC<ShapePanelProps> = ({ onAddNode }) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['basic', 'aws', 'containers'])
  );

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  const handleDragStart = (event: React.DragEvent, nodeType: string, nodeData: any) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify({ nodeType, nodeData }));
    event.dataTransfer.effectAllowed = 'move';
  };

  const categories: Category[] = [
    {
      id: 'basic',
      name: 'Basic Shapes',
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <rect x="3" y="6" width="18" height="12" rx="2" strokeWidth={2} />
        </svg>
      ),
      items: [
        {
          id: 'rectangle',
          name: 'Rectangle',
          nodeType: 'shape',
          nodeData: {
            label: 'Rectangle',
            shapeType: 'rectangle',
            width: 120,
            height: 80,
            fillColor: '#ffffff',
            strokeColor: '#000000',
            strokeWidth: 2,
          },
          preview: (
            <div className="w-full h-12 border-2 border-gray-700 bg-white rounded"></div>
          ),
        },
        {
          id: 'circle',
          name: 'Circle',
          nodeType: 'shape',
          nodeData: {
            label: 'Circle',
            shapeType: 'circle',
            width: 100,
            height: 100,
            fillColor: '#ffffff',
            strokeColor: '#000000',
            strokeWidth: 2,
          },
          preview: (
            <div className="w-12 h-12 border-2 border-gray-700 bg-white rounded-full mx-auto"></div>
          ),
        },
        {
          id: 'diamond',
          name: 'Diamond',
          nodeType: 'shape',
          nodeData: {
            label: 'Diamond',
            shapeType: 'diamond',
            width: 100,
            height: 100,
            fillColor: '#ffffff',
            strokeColor: '#000000',
            strokeWidth: 2,
          },
          preview: (
            <svg className="w-12 h-12 mx-auto" viewBox="0 0 100 100">
              <polygon
                points="50,5 95,50 50,95 5,50"
                fill="white"
                stroke="#374151"
                strokeWidth="3"
              />
            </svg>
          ),
        },
        {
          id: 'triangle',
          name: 'Triangle',
          nodeType: 'shape',
          nodeData: {
            label: 'Triangle',
            shapeType: 'triangle',
            width: 100,
            height: 100,
            fillColor: '#ffffff',
            strokeColor: '#000000',
            strokeWidth: 2,
          },
          preview: (
            <svg className="w-12 h-12 mx-auto" viewBox="0 0 100 100">
              <polygon
                points="50,5 95,95 5,95"
                fill="white"
                stroke="#374151"
                strokeWidth="3"
              />
            </svg>
          ),
        },
        {
          id: 'text',
          name: 'Text',
          nodeType: 'text',
          nodeData: {
            text: 'Text',
            fontSize: 14,
            fontWeight: 'normal',
            textColor: '#000000',
            backgroundColor: 'transparent',
            showBorder: false,
          },
          preview: (
            <div className="text-center text-sm font-medium text-gray-700">Aa</div>
          ),
        },
      ],
    },
    {
      id: 'containers',
      name: 'Containers',
      icon: (
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"
          />
        </svg>
      ),
      items: [
        {
          id: 'container',
          name: 'Container',
          nodeType: 'container',
          nodeData: {
            label: 'VPC / Subnet',
            width: 300,
            height: 200,
            backgroundColor: '#f9fafb',
            borderColor: '#6b7280',
            borderWidth: 2,
            borderStyle: 'dashed',
          },
          preview: (
            <div className="w-full h-12 border-2 border-dashed border-gray-500 bg-gray-50 rounded flex items-center justify-center">
              <span className="text-xs text-gray-600">Container</span>
            </div>
          ),
        },
      ],
    },
    {
      id: 'aws',
      name: 'AWS',
      icon: (
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path
            d="M6.763 10.036c0 .296.032.535.088.71.064.176.144.368.256.576.04.063.056.127.056.183 0 .08-.048.16-.152.24l-.503.335a.383.383 0 0 1-.208.072c-.08 0-.16-.04-.239-.112a2.47 2.47 0 0 1-.287-.375 6.18 6.18 0 0 1-.248-.471c-.622.734-1.405 1.101-2.347 1.101-.67 0-1.205-.191-1.596-.574-.391-.384-.59-.894-.59-1.533 0-.678.239-1.226.726-1.644.487-.417 1.133-.626 1.955-.626.272 0 .551.024.846.064.296.04.6.104.918.176v-.583c0-.607-.127-1.03-.375-1.277-.255-.248-.686-.367-1.3-.367-.28 0-.568.031-.863.103-.295.072-.583.16-.862.272a2.287 2.287 0 0 1-.28.104.488.488 0 0 1-.127.023c-.112 0-.168-.08-.168-.247v-.391c0-.128.016-.224.056-.28a.597.597 0 0 1 .224-.167c.279-.144.614-.264 1.005-.36C2.096 4.015 2.52 3.961 2.968 3.961c1.064 0 1.844.247 2.34.734.495.495.743 1.245.743 2.255v2.958z"
            fill="#FF9900"
          />
        </svg>
      ),
      items: [
        {
          id: 'aws-ec2',
          name: 'EC2',
          nodeType: 'cloudProvider',
          nodeData: { provider: 'aws' as CloudProvider, label: 'EC2', size: 64 },
          preview: (
            <div className="flex items-center justify-center">
              <div className="w-10 h-10 bg-orange-500 rounded flex items-center justify-center text-white text-xs font-bold">
                AWS
              </div>
            </div>
          ),
        },
      ],
    },
    {
      id: 'azure',
      name: 'Azure',
      icon: (
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path
            d="M13.05 16.95L15.2 21.1l5.85-2.2.45-5.4zM5.55 2.9L0 8.75l5.4 2.2L10.5 0z"
            fill="#0078D4"
          />
        </svg>
      ),
      items: [
        {
          id: 'azure-vm',
          name: 'Virtual Machine',
          nodeType: 'cloudProvider',
          nodeData: { provider: 'azure' as CloudProvider, label: 'VM', size: 64 },
          preview: (
            <div className="flex items-center justify-center">
              <div className="w-10 h-10 bg-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">
                AZ
              </div>
            </div>
          ),
        },
      ],
    },
    {
      id: 'gcp',
      name: 'Google Cloud',
      icon: (
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path
            d="M12.19 2.38a9.344 9.344 0 0 1 9.433 9.434 9.344 9.344 0 0 1-9.433 9.433 9.344 9.344 0 0 1-9.433-9.433c0-5.01 3.924-9.122 8.855-9.415"
            fill="#4285F4"
          />
        </svg>
      ),
      items: [
        {
          id: 'gcp-compute',
          name: 'Compute Engine',
          nodeType: 'cloudProvider',
          nodeData: { provider: 'gcp' as CloudProvider, label: 'GCE', size: 64 },
          preview: (
            <div className="flex items-center justify-center">
              <div className="w-10 h-10 bg-blue-500 rounded flex items-center justify-center text-white text-xs font-bold">
                GCP
              </div>
            </div>
          ),
        },
      ],
    },
    {
      id: 'kubernetes',
      name: 'Kubernetes',
      icon: (
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path
            d="M10.204 14.35l.007.01-.999 2.413a5.171 5.171 0 0 1-2.075-2.597l2.578-.437.004.005a.44.44 0 0 1 .484.606z"
            fill="#326CE5"
          />
        </svg>
      ),
      items: [
        {
          id: 'k8s-pod',
          name: 'Pod',
          nodeType: 'cloudProvider',
          nodeData: { provider: 'kubernetes' as CloudProvider, label: 'Pod', size: 64 },
          preview: (
            <div className="flex items-center justify-center">
              <div className="w-10 h-10 bg-blue-700 rounded flex items-center justify-center text-white text-xs font-bold">
                K8s
              </div>
            </div>
          ),
        },
        {
          id: 'docker',
          name: 'Docker',
          nodeType: 'cloudProvider',
          nodeData: { provider: 'docker' as CloudProvider, label: 'Container', size: 64 },
          preview: (
            <div className="flex items-center justify-center">
              <div className="w-10 h-10 bg-blue-400 rounded flex items-center justify-center text-white text-xs font-bold">
                🐳
              </div>
            </div>
          ),
        },
      ],
    },
  ];

  return (
    <div className="w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto flex-shrink-0">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Shapes</h2>

        {categories.map((category) => (
          <div key={category.id} className="mb-2">
            <button
              onClick={() => toggleCategory(category.id)}
              className="w-full flex items-center justify-between p-2 rounded-md hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center gap-2">
                {category.icon}
                <span className="text-sm font-medium text-gray-700">{category.name}</span>
              </div>
              <svg
                className={`h-4 w-4 text-gray-500 transition-transform ${
                  expandedCategories.has(category.id) ? 'rotate-90' : ''
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>

            {expandedCategories.has(category.id) && (
              <div className="mt-2 space-y-2 pl-2">
                {category.items.map((item) => (
                  <div
                    key={item.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, item.nodeType, item.nodeData)}
                    onClick={() => onAddNode(item.nodeType, item.nodeData)}
                    className="p-3 bg-white border border-gray-200 rounded-md cursor-move hover:border-yellow-600 hover:shadow-md transition-all"
                  >
                    <div className="mb-2">{item.preview}</div>
                    <div className="text-xs text-center text-gray-600 font-medium">
                      {item.name}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ShapePanel;
