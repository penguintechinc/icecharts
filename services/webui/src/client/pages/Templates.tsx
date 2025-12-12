import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import type { Template } from '../types';

export default function Templates() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [categories, setCategories] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchTemplates();
  }, [selectedCategory]);

  const fetchTemplates = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        ...(selectedCategory !== 'all' && { category: selectedCategory }),
      });

      const response = await api.get<{ success?: boolean; templates?: Template[]; items?: Template[] }>(
        `/templates?${params}`
      );

      const templatesList = response.data.templates || response.data.items || [];
      setTemplates(templatesList);

      // Extract unique categories
      const uniqueCategories = [
        ...new Set(templatesList.map((t) => t.category).filter(Boolean)),
      ];
      setCategories(uniqueCategories);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
      setTemplates([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseTemplate = async (templateId: string | number) => {
    try {
      // Find the template to get its name
      const template = templates.find((t) => t.id === templateId);
      const templateName = template?.name || 'Untitled';

      // Generate a name for the new drawing
      const drawingName = `${templateName} - ${new Date().toLocaleDateString()}`;

      const response = await api.post(`/templates/${templateId}/use`, {
        name: drawingName,
        description: `Drawing created from ${templateName} template`,
      });

      const newDrawingId = response.data.drawing?.id || response.data.drawing_id;
      navigate(`/drawings/${newDrawingId}`);
    } catch (err) {
      console.error('Failed to use template:', err);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-ice-gold-400">Templates</h1>
        <p className="text-ice-navy-400 mt-1">
          Start from a template to speed up your workflow
        </p>
      </div>

      {/* Category Filter */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 overflow-x-auto">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
              selectedCategory === 'all'
                ? 'bg-ice-gold-600 text-white'
                : 'bg-ice-navy-800 text-ice-gold-400 hover:bg-ice-navy-700'
            }`}
          >
            All Templates
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                selectedCategory === category
                  ? 'bg-ice-gold-600 text-white'
                  : 'bg-ice-navy-800 text-ice-gold-400 hover:bg-ice-navy-700'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Templates Gallery */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-40 bg-ice-navy-700 rounded mb-3"></div>
              <div className="h-4 bg-ice-navy-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-ice-navy-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : templates.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <div
              key={template.id}
              className="card hover:bg-ice-navy-850 transition-colors group"
            >
              {/* Template Preview */}
              <div className="h-40 bg-ice-navy-800 rounded mb-3 flex items-center justify-center overflow-hidden relative">
                {template.thumbnail_url ? (
                  <img
                    src={template.thumbnail_url}
                    alt={template.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <svg
                    className="w-16 h-16 text-ice-navy-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
                    />
                  </svg>
                )}

                {/* Overlay on hover */}
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <button
                    onClick={() => handleUseTemplate(template.id)}
                    className="px-4 py-2 bg-ice-gold-600 hover:bg-ice-gold-700 text-white rounded-lg transition-colors"
                  >
                    Use Template
                  </button>
                </div>
              </div>

              {/* Template Info */}
              <h3 className="font-medium text-ice-gold-400 truncate mb-1">
                {template.name}
              </h3>

              {template.description && (
                <p className="text-xs text-ice-navy-400 line-clamp-2 mb-2">
                  {template.description}
                </p>
              )}

              <div className="flex items-center justify-between text-xs text-ice-navy-500">
                <span className="px-2 py-0.5 rounded bg-ice-navy-800">
                  {template.category}
                </span>
                <span>{template.usage_count} uses</span>
              </div>

              <div className="mt-2 text-xs text-ice-navy-600">
                By {template.created_by_name}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-ice-navy-400">No templates available</p>
        </div>
      )}
    </div>
  );
}
