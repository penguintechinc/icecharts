import { useState, useEffect } from 'react';
import api from '../lib/api';
import Button from '../components/Button';
import Card from '../components/Card';
import type {
  ShapeLibrary,
  LibraryShape,
  CreateLibraryData,
  UpdateLibraryData,
  CreateShapeData,
  UpdateShapeData,
} from '../types';

export default function LibrariesPage() {
  const [libraries, setLibraries] = useState<ShapeLibrary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showShapesModal, setShowShapesModal] = useState(false);
  const [showAddShapeModal, setShowAddShapeModal] = useState(false);
  const [showEditShapeModal, setShowEditShapeModal] = useState(false);
  const [editingLibrary, setEditingLibrary] = useState<ShapeLibrary | null>(null);
  const [selectedLibrary, setSelectedLibrary] = useState<ShapeLibrary | null>(null);
  const [editingShape, setEditingShape] = useState<LibraryShape | null>(null);
  const [libraryShapes, setLibraryShapes] = useState<LibraryShape[]>([]);
  const [isLoadingShapes, setIsLoadingShapes] = useState(false);
  const [formData, setFormData] = useState<CreateLibraryData>({
    name: '',
    description: '',
    is_public: false,
  });
  const [shapeFormData, setShapeFormData] = useState<CreateShapeData>({
    name: '',
    description: '',
    shape_data: {},
    category: 'custom',
  });
  const [shapeDataJson, setShapeDataJson] = useState('{}');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showPublicOnly, setShowPublicOnly] = useState(false);

  useEffect(() => {
    fetchLibraries();
  }, [searchQuery, showPublicOnly]);

  const fetchLibraries = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      params.append('public', showPublicOnly ? 'false' : 'true');

      const response = await api.get<{
        libraries: ShapeLibrary[];
        total: number;
      }>(`/libraries?${params.toString()}`);
      setLibraries(response.data.libraries || []);
    } catch (err) {
      console.error('Failed to fetch libraries:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchLibraryShapes = async (libraryId: number) => {
    setIsLoadingShapes(true);
    try {
      const response = await api.get<{ shapes: LibraryShape[]; total: number }>(
        `/libraries/${libraryId}/shapes`
      );
      setLibraryShapes(response.data.shapes || []);
    } catch (err) {
      console.error('Failed to fetch library shapes:', err);
    } finally {
      setIsLoadingShapes(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError('');

    try {
      await api.post('/libraries', formData);
      setShowCreateModal(false);
      resetForm();
      fetchLibraries();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create library');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingLibrary) return;

    setIsSaving(true);
    setError('');

    try {
      const updateData: UpdateLibraryData = {
        name: formData.name,
        description: formData.description || undefined,
        is_public: formData.is_public,
      };
      await api.put(`/libraries/${editingLibrary.id}`, updateData);
      setShowEditModal(false);
      setEditingLibrary(null);
      resetForm();
      fetchLibraries();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update library');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (libraryId: number) => {
    if (!confirm('Delete this library? All shapes in this library will be removed.')) return;

    try {
      await api.delete(`/libraries/${libraryId}`);
      fetchLibraries();
    } catch (err) {
      console.error('Failed to delete library:', err);
    }
  };

  const handleDuplicate = async (libraryId: number) => {
    try {
      await api.post(`/libraries/${libraryId}/duplicate`);
      fetchLibraries();
    } catch (err) {
      console.error('Failed to duplicate library:', err);
    }
  };

  const handleEdit = (library: ShapeLibrary) => {
    setEditingLibrary(library);
    setFormData({
      name: library.name,
      description: library.description || '',
      is_public: library.is_public,
    });
    setShowEditModal(true);
  };

  const handleViewShapes = (library: ShapeLibrary) => {
    setSelectedLibrary(library);
    setShowShapesModal(true);
    fetchLibraryShapes(library.id);
  };

  const handleAddShape = (library: ShapeLibrary) => {
    setSelectedLibrary(library);
    setShapeFormData({
      name: '',
      description: '',
      shape_data: {},
      category: 'custom',
    });
    setShapeDataJson('{}');
    setShowAddShapeModal(true);
  };

  const handleCreateShape = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLibrary) return;

    setIsSaving(true);
    setError('');

    try {
      // Parse JSON
      const parsedShapeData = JSON.parse(shapeDataJson);
      const shapeData: CreateShapeData = {
        ...shapeFormData,
        shape_data: parsedShapeData,
      };

      await api.post(`/libraries/${selectedLibrary.id}/shapes`, shapeData);
      setShowAddShapeModal(false);
      resetShapeForm();
      if (showShapesModal) {
        fetchLibraryShapes(selectedLibrary.id);
      }
      fetchLibraries();
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format in shape data');
      } else {
        setError(err.response?.data?.error || 'Failed to add shape');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleEditShape = (shape: LibraryShape) => {
    setEditingShape(shape);
    setShapeFormData({
      name: shape.name,
      description: shape.description || '',
      shape_data: shape.shape_data,
      category: shape.category,
    });
    setShapeDataJson(JSON.stringify(shape.shape_data, null, 2));
    setShowEditShapeModal(true);
  };

  const handleUpdateShape = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLibrary || !editingShape) return;

    setIsSaving(true);
    setError('');

    try {
      // Parse JSON
      const parsedShapeData = JSON.parse(shapeDataJson);
      const updateData: UpdateShapeData = {
        name: shapeFormData.name,
        description: shapeFormData.description || undefined,
        shape_data: parsedShapeData,
        category: shapeFormData.category,
      };

      await api.put(`/libraries/${selectedLibrary.id}/shapes/${editingShape.id}`, updateData);
      setShowEditShapeModal(false);
      setEditingShape(null);
      resetShapeForm();
      fetchLibraryShapes(selectedLibrary.id);
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format in shape data');
      } else {
        setError(err.response?.data?.error || 'Failed to update shape');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteShape = async (libraryId: number, shapeId: number) => {
    if (!confirm('Delete this shape from the library?')) return;

    try {
      await api.delete(`/libraries/${libraryId}/shapes/${shapeId}`);
      fetchLibraryShapes(libraryId);
      fetchLibraries();
    } catch (err) {
      console.error('Failed to delete shape:', err);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      is_public: false,
    });
    setError('');
  };

  const resetShapeForm = () => {
    setShapeFormData({
      name: '',
      description: '',
      shape_data: {},
      category: 'custom',
    });
    setShapeDataJson('{}');
    setError('');
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gold-400">Shape Libraries</h1>
          <p className="text-dark-400 mt-1">
            Manage custom shape libraries for your diagrams
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Create Library</Button>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4 mb-6">
        <input
          type="text"
          placeholder="Search libraries..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input flex-1"
        />
        <label className="flex items-center gap-2 text-dark-300">
          <input
            type="checkbox"
            checked={showPublicOnly}
            onChange={(e) => setShowPublicOnly(e.target.checked)}
            className="w-4 h-4"
          />
          <span>My libraries only</span>
        </label>
      </div>

      {/* Libraries List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-6 bg-dark-700 rounded w-1/3 mb-3"></div>
              <div className="h-4 bg-dark-700 rounded w-full mb-2"></div>
              <div className="h-4 bg-dark-700 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : libraries.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {libraries.map((library) => (
            <Card key={library.id}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-medium text-gold-400">{library.name}</h3>
                    {library.is_public && (
                      <span className="text-xs px-2 py-1 rounded bg-blue-900/30 text-blue-400">
                        Public
                      </span>
                    )}
                  </div>
                  {library.description && (
                    <p className="text-dark-300 text-sm mb-3">{library.description}</p>
                  )}
                </div>
              </div>

              <div className="space-y-2 text-sm mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-dark-400 w-24">Shapes:</span>
                  <span className="text-gold-400">{library.shape_count || 0}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-dark-400 w-24">Created:</span>
                  <span className="text-dark-300">
                    {new Date(library.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleViewShapes(library)}
                  className="px-3 py-1.5 text-sm text-blue-400 hover:text-blue-300"
                >
                  View Shapes
                </button>
                <button
                  onClick={() => handleAddShape(library)}
                  className="px-3 py-1.5 text-sm text-green-400 hover:text-green-300"
                >
                  Add Shape
                </button>
                <button
                  onClick={() => handleEdit(library)}
                  className="px-3 py-1.5 text-sm text-gold-400 hover:text-gold-300"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDuplicate(library.id)}
                  className="px-3 py-1.5 text-sm text-purple-400 hover:text-purple-300"
                >
                  Duplicate
                </button>
                <button
                  onClick={() => handleDelete(library.id)}
                  className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300"
                >
                  Delete
                </button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-dark-400 mb-4">No libraries found</p>
          <p className="text-dark-500 text-sm mb-6">
            Create your first library to organize custom shapes for your diagrams.
          </p>
          <Button onClick={() => setShowCreateModal(true)}>Create Your First Library</Button>
        </div>
      )}

      {/* Create Library Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-lg w-full">
            <h2 className="text-xl font-bold text-gold-400 mb-4">Create Shape Library</h2>

            <form onSubmit={handleCreate} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  placeholder="e.g., Network Diagrams, Floor Plans"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input w-full"
                  rows={3}
                  placeholder="Describe the purpose of this library..."
                />
              </div>

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_public}
                    onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-dark-300 text-sm">
                    Make this library public (accessible to all users)
                  </span>
                </label>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" isLoading={isSaving}>
                  Create
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Library Modal */}
      {showEditModal && editingLibrary && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-lg w-full">
            <h2 className="text-xl font-bold text-gold-400 mb-4">Edit Library</h2>

            <form onSubmit={handleUpdate} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input w-full"
                  rows={3}
                />
              </div>

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_public}
                    onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-dark-300 text-sm">Make this library public</span>
                </label>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingLibrary(null);
                    resetForm();
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" isLoading={isSaving}>
                  Update
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Shapes Modal */}
      {showShapesModal && selectedLibrary && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gold-400">
                Shapes in {selectedLibrary.name}
              </h2>
              <button
                onClick={() => {
                  setShowShapesModal(false);
                  setSelectedLibrary(null);
                }}
                className="text-dark-400 hover:text-gold-400"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {isLoadingShapes ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-24 bg-dark-700 rounded animate-pulse"></div>
                ))}
              </div>
            ) : libraryShapes.length > 0 ? (
              <div className="space-y-3">
                {libraryShapes.map((shape) => (
                  <div key={shape.id} className="border border-dark-700 rounded p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-gold-400">{shape.name}</h4>
                          <span className="px-2 py-0.5 text-xs rounded bg-dark-700 text-dark-300">
                            {shape.category}
                          </span>
                        </div>
                        {shape.description && (
                          <p className="text-sm text-dark-300 mb-2">{shape.description}</p>
                        )}
                        <div className="text-xs text-dark-500">
                          Added {new Date(shape.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEditShape(shape)}
                          className="px-3 py-1.5 text-sm text-gold-400 hover:text-gold-300"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteShape(selectedLibrary.id, shape.id)}
                          className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-dark-400">
                No shapes in this library yet
              </div>
            )}

            <div className="mt-6 pt-4 border-t border-dark-700">
              <Button onClick={() => handleAddShape(selectedLibrary)} className="w-full">
                Add New Shape
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Add Shape Modal */}
      {showAddShapeModal && selectedLibrary && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gold-400 mb-4">
              Add Shape to {selectedLibrary.name}
            </h2>

            <form onSubmit={handleCreateShape} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Shape Name</label>
                <input
                  type="text"
                  value={shapeFormData.name}
                  onChange={(e) => setShapeFormData({ ...shapeFormData, name: e.target.value })}
                  className="input w-full"
                  placeholder="e.g., Router Icon, Server Rack"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={shapeFormData.description}
                  onChange={(e) =>
                    setShapeFormData({ ...shapeFormData, description: e.target.value })
                  }
                  className="input w-full"
                  rows={2}
                  placeholder="Describe this shape..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Category</label>
                <input
                  type="text"
                  value={shapeFormData.category}
                  onChange={(e) => setShapeFormData({ ...shapeFormData, category: e.target.value })}
                  className="input w-full"
                  placeholder="e.g., network, infrastructure, custom"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Shape Data (JSON)
                </label>
                <textarea
                  value={shapeDataJson}
                  onChange={(e) => setShapeDataJson(e.target.value)}
                  className="input w-full font-mono text-sm"
                  rows={10}
                  placeholder='{"type": "rect", "width": 100, "height": 60, ...}'
                  required
                />
                <p className="text-xs text-dark-500 mt-1">
                  Enter the shape definition as JSON (SVG path, dimensions, styles, etc.)
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowAddShapeModal(false);
                    resetShapeForm();
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" isLoading={isSaving}>
                  Add Shape
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Shape Modal */}
      {showEditShapeModal && editingShape && selectedLibrary && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gold-400 mb-4">Edit Shape</h2>

            <form onSubmit={handleUpdateShape} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Shape Name</label>
                <input
                  type="text"
                  value={shapeFormData.name}
                  onChange={(e) => setShapeFormData({ ...shapeFormData, name: e.target.value })}
                  className="input w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={shapeFormData.description}
                  onChange={(e) =>
                    setShapeFormData({ ...shapeFormData, description: e.target.value })
                  }
                  className="input w-full"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Category</label>
                <input
                  type="text"
                  value={shapeFormData.category}
                  onChange={(e) => setShapeFormData({ ...shapeFormData, category: e.target.value })}
                  className="input w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Shape Data (JSON)
                </label>
                <textarea
                  value={shapeDataJson}
                  onChange={(e) => setShapeDataJson(e.target.value)}
                  className="input w-full font-mono text-sm"
                  rows={10}
                  required
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowEditShapeModal(false);
                    setEditingShape(null);
                    resetShapeForm();
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" isLoading={isSaving}>
                  Update Shape
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
