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

      const response = await api.get<{ items: Template[] }>(
        `/templates?${params}`
      );

      setTemplates(response.data.items);

      // Extract unique categories
      const uniqueCategories = [
        ...new Set(response.data.items.map((t) => t.category)),
      ];
      setCategories(uniqueCategories);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseTemplate = async (templateId: number) => {
    try {
      const response = await api.post(`/templates/${templateId}/use`);
      const newDrawingId = response.data.drawing_id;
      navigate(`/drawings/${newDrawingId}`);
    } catch (err) {
      console.error('Failed to use template:', err);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gold-400">Templates</h1>
        <p className="text-dark-400 mt-1">
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
                ? 'bg-gold-600 text-white'
                : 'bg-dark-800 text-gold-400 hover:bg-dark-700'
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
                  ? 'bg-gold-600 text-white'
                  : 'bg-dark-800 text-gold-400 hover:bg-dark-700'
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
              <div className="h-40 bg-dark-700 rounded mb-3"></div>
              <div className="h-4 bg-dark-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-dark-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : templates.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <div
              key={template.id}
              className="card hover:bg-dark-850 transition-colors group"
            >
              {/* Template Preview */}
              <div className="h-40 bg-dark-800 rounded mb-3 flex items-center justify-center overflow-hidden relative">
                {template.thumbnail_url ? (
                  <img
                    src={template.thumbnail_url}
                    alt={template.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <svg
                    className="w-16 h-16 text-dark-600"
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
                    className="px-4 py-2 bg-gold-600 hover:bg-gold-700 text-white rounded-lg transition-colors"
                  >
                    Use Template
                  </button>
                </div>
              </div>

              {/* Template Info */}
              <h3 className="font-medium text-gold-400 truncate mb-1">
                {template.name}
              </h3>

              {template.description && (
                <p className="text-xs text-dark-400 line-clamp-2 mb-2">
                  {template.description}
                </p>
              )}

              <div className="flex items-center justify-between text-xs text-dark-500">
                <span className="px-2 py-0.5 rounded bg-dark-800">
                  {template.category}
                </span>
                <span>{template.usage_count} uses</span>
              </div>

              <div className="mt-2 text-xs text-dark-600">
                By {template.created_by_name}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-dark-400">No templates available</p>
        </div>
      )}
    </div>
  );
}
