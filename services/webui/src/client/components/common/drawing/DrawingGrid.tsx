import React from 'react';
import DrawingCard from './DrawingCard';

export interface Drawing {
  id: string;
  title: string;
  thumbnail?: string;
  lastModified: Date;
  ownerName: string;
  ownerInitials: string;
  ownerAvatar?: string;
}

interface DrawingGridProps {
  drawings: Drawing[];
  onEdit?: (id: string) => void;
  onDuplicate?: (id: string) => void;
  onDelete?: (id: string) => void;
  onShare?: (id: string) => void;
  isLoading?: boolean;
  emptyMessage?: string;
  columns?: 2 | 3 | 4 | 5;
}

export default function DrawingGrid({
  drawings,
  onEdit,
  onDuplicate,
  onDelete,
  onShare,
  isLoading = false,
  emptyMessage = 'No drawings yet. Create one to get started!',
  columns = 3,
}: DrawingGridProps) {
  const gridColsClasses = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
    5: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-5',
  };

  if (isLoading) {
    return (
      <div className="grid gap-4 px-4 py-8">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="aspect-video bg-slate-700 rounded-lg animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (drawings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <svg className="w-12 h-12 text-slate-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <p className="text-slate-400 text-center">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`grid ${gridColsClasses[columns]} gap-4 px-4 py-8`}>
      {drawings.map((drawing) => (
        <DrawingCard
          key={drawing.id}
          {...drawing}
          onEdit={onEdit}
          onDuplicate={onDuplicate}
          onDelete={onDelete}
          onShare={onShare}
        />
      ))}
    </div>
  );
}
