import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../lib/api';
import Button from '../components/Button';
import type { Drawing, UpdateDrawingData } from '../types';

export default function DrawingEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [drawing, setDrawing] = useState<Drawing | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  const isNewDrawing = id === 'new';

  useEffect(() => {
    if (!isNewDrawing) {
      fetchDrawing();
    } else {
      setIsLoading(false);
    }
  }, [id]);

  const fetchDrawing = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<Drawing>(`/drawings/${id}`);
      setDrawing(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load drawing');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');

    try {
      if (isNewDrawing) {
        const newDrawing: UpdateDrawingData = {
          name: 'Untitled Drawing',
          content: {},
          visibility: 'private',
        };
        const response = await api.post<Drawing>('/drawings', newDrawing);
        navigate(`/drawings/${response.data.id}`, { replace: true });
      } else {
        const updated: UpdateDrawingData = {
          content: drawing?.content || {},
        };
        await api.put(`/drawings/${id}`, updated);
        await fetchDrawing();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save drawing');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gold-400 text-xl">Loading editor...</div>
      </div>
    );
  }

  if (error && !isNewDrawing) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="card max-w-md text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Link to="/drawings">
            <Button>Back to Drawings</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-dark-950">
      {/* Editor Header */}
      <div className="bg-dark-900 border-b border-dark-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/drawings"
            className="text-gold-400 hover:text-gold-300 transition-colors"
            title="Back to Drawings"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
          </Link>
          <div>
            <h1 className="text-lg font-semibold text-gold-400">
              {drawing?.name || 'New Drawing'}
            </h1>
            {drawing && (
              <p className="text-xs text-dark-400">
                Last saved: {new Date(drawing.updated_at).toLocaleString()}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {error && (
            <span className="text-sm text-red-400">{error}</span>
          )}
          <Button onClick={handleSave} isLoading={isSaving}>
            Save
          </Button>
        </div>
      </div>

      {/* Editor Canvas - Placeholder for React Flow */}
      <div className="flex-1 relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center bg-dark-900">
          <div className="text-center">
            <svg
              className="w-20 h-20 text-dark-700 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
              />
            </svg>
            <h2 className="text-xl font-semibold text-gold-400 mb-2">
              React Flow Editor
            </h2>
            <p className="text-dark-400 mb-6 max-w-md">
              This is a placeholder for the React Flow canvas editor.
              <br />
              Integrate React Flow library here to enable diagram editing.
            </p>
            <div className="space-y-2 text-sm text-dark-500">
              <p>Features to implement:</p>
              <ul className="list-disc list-inside">
                <li>Drag and drop nodes</li>
                <li>Connect nodes with edges</li>
                <li>Node customization (colors, shapes, labels)</li>
                <li>Pan and zoom controls</li>
                <li>Export to PNG/SVG</li>
                <li>Undo/Redo functionality</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Editor Toolbar/Sidebar (optional) */}
      <div className="bg-dark-900 border-t border-dark-700 px-6 py-3">
        <div className="flex items-center justify-between text-sm text-dark-400">
          <span>Tools: Select, Pan, Zoom, Add Node, Add Edge</span>
          <span>Grid: On | Snap: Enabled</span>
        </div>
      </div>
    </div>
  );
}
