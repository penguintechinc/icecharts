import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import Dropdown from '../common/Dropdown';
import Tooltip from '../common/Tooltip';

interface CollectionCardProps {
  id: string;
  name: string;
  description?: string;
  thumbnail?: string;
  drawingCount: number;
  shareMode: 'private' | 'link_only' | 'registered_users';
  createdDate: Date;
  ownerName: string;
  ownerInitials: string;
  ownerAvatar?: string;
  onView?: (id: string) => void;
  onEdit?: (id: string) => void;
  onShare?: (id: string) => void;
  onDelete?: (id: string) => void;
  className?: string;
}

export default function CollectionCard({
  id,
  name,
  description,
  thumbnail,
  drawingCount,
  shareMode,
  createdDate,
  ownerName,
  ownerInitials,
  ownerAvatar,
  onView,
  onEdit,
  onShare,
  onDelete,
  className = '',
}: CollectionCardProps) {
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getShareModeColor = (): 'default' | 'warning' | 'success' | 'info' => {
    switch (shareMode) {
      case 'private':
        return 'default';
      case 'link_only':
        return 'warning';
      case 'registered_users':
        return 'success';
      default:
        return 'default';
    }
  };

  const getShareModeLabel = (): string => {
    switch (shareMode) {
      case 'private':
        return 'Private';
      case 'link_only':
        return 'Link Only';
      case 'registered_users':
        return 'Public';
      default:
        return 'Unknown';
    }
  };

  const getShareModeIcon = (): string => {
    switch (shareMode) {
      case 'private':
        return '🔒';
      case 'link_only':
        return '🔗';
      case 'registered_users':
        return '🌐';
      default:
        return '?';
    }
  };

  const dropdownItems = [
    ...(onView
      ? [
          {
            id: 'view',
            label: 'View',
            icon: '👁️',
            onClick: () => onView(id),
          },
        ]
      : []),
    ...(onEdit
      ? [
          {
            id: 'edit',
            label: 'Edit',
            icon: '✏️',
            onClick: () => onEdit(id),
          },
        ]
      : []),
    ...(onShare
      ? [
          {
            id: 'share',
            label: 'Share',
            icon: '🔗',
            onClick: () => onShare(id),
          },
        ]
      : []),
    ...(onDelete
      ? [
          {
            id: 'divider',
            label: '',
            divider: true,
            onClick: () => {},
          },
          {
            id: 'delete',
            label: 'Delete',
            icon: '🗑️',
            danger: true,
            onClick: () => onDelete(id),
          },
        ]
      : []),
  ];

  return (
    <Card
      className={`cursor-pointer hover:border-ice-gold-400/50 transition-colors ${className}`}
      padding="sm"
    >
      {/* Thumbnail Container */}
      <div className="mb-3 aspect-video bg-slate-900 rounded-lg overflow-hidden relative">
        {thumbnail ? (
          <img
            src={thumbnail}
            alt={name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 space-y-2">
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
            </svg>
            <span className="text-xs font-medium">
              {drawingCount} drawing{drawingCount !== 1 ? 's' : ''}
            </span>
          </div>
        )}

        {/* Drawing Count Badge - Overlay on thumbnail */}
        <div className="absolute bottom-2 right-2 bg-slate-900/80 backdrop-blur-sm rounded-lg px-2 py-1 text-xs font-medium text-slate-100 border border-slate-700">
          {drawingCount}
        </div>
      </div>

      {/* Content */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {/* Title */}
          <Tooltip content={name} position="top">
            <h3 className="font-semibold text-slate-100 truncate">{name}</h3>
          </Tooltip>

          {/* Description */}
          {description && (
            <p className="text-xs text-slate-400 line-clamp-2 mt-1">
              {description}
            </p>
          )}

          {/* Share Mode and Date */}
          <div className="flex items-center gap-2 mt-2">
            <Badge
              variant={getShareModeColor()}
              size="sm"
              className="flex items-center gap-1"
            >
              <span className="text-xs">{getShareModeIcon()}</span>
              <span>{getShareModeLabel()}</span>
            </Badge>
            <span className="text-xs text-slate-500">
              {formatDate(createdDate)}
            </span>
          </div>
        </div>

        {/* Actions */}
        {dropdownItems.length > 0 && (
          <div className="flex-shrink-0">
            <Dropdown
              trigger={
                <button className="p-1 text-slate-400 hover:text-ice-gold-400 transition-colors rounded-md hover:bg-slate-700">
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M10.5 1.5H9.5V3h1V1.5zM10.5 17h-1v1.5h1V17zM17 9.5v1h1.5v-1H17zM1.5 10.5H3v-1H1.5v1z" />
                    <circle cx="10" cy="10" r="1.5" />
                  </svg>
                </button>
              }
              items={dropdownItems}
              align="right"
            />
          </div>
        )}
      </div>
    </Card>
  );
}
