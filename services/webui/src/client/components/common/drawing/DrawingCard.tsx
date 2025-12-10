import Card from '../Card';
import Avatar from '../Avatar';
import Dropdown from '../Dropdown';
import Tooltip from '../Tooltip';

interface DrawingCardProps {
  id: string;
  title: string;
  thumbnail?: string;
  lastModified: Date;
  ownerName: string;
  ownerInitials: string;
  ownerAvatar?: string;
  onEdit?: (id: string) => void;
  onDuplicate?: (id: string) => void;
  onDelete?: (id: string) => void;
  onShare?: (id: string) => void;
  className?: string;
}

export default function DrawingCard({
  id,
  title,
  thumbnail,
  lastModified,
  ownerName,
  ownerInitials,
  ownerAvatar,
  onEdit,
  onDuplicate,
  onDelete,
  onShare,
  className = '',
}: DrawingCardProps) {
  const formatDate = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const dropdownItems = [
    ...(onEdit ? [{
      id: 'edit',
      label: 'Edit',
      icon: '✏️',
      onClick: () => onEdit(id),
    }] : []),
    ...(onDuplicate ? [{
      id: 'duplicate',
      label: 'Duplicate',
      icon: '📋',
      onClick: () => onDuplicate(id),
    }] : []),
    ...(onShare ? [{
      id: 'share',
      label: 'Share',
      icon: '🔗',
      onClick: () => onShare(id),
    }] : []),
    ...(onDelete ? [{
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
    }] : []),
  ];

  return (
    <Card className={`cursor-pointer hover:border-ice-gold-400/50 transition-colors ${className}`} padding="sm">
      {/* Thumbnail */}
      <div className="mb-3 aspect-video bg-slate-900 rounded-lg overflow-hidden">
        {thumbnail ? (
          <img
            src={thumbnail}
            alt={title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-500">
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
            </svg>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <Tooltip content={title} position="top">
            <h3 className="font-semibold text-slate-100 truncate">
              {title}
            </h3>
          </Tooltip>
          <p className="text-xs text-slate-500 mt-1">
            {formatDate(lastModified)}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <Avatar
              src={ownerAvatar}
              initials={ownerInitials}
              size="sm"
            />
            <span className="text-xs text-slate-400">{ownerName}</span>
          </div>
        </div>

        {/* Actions */}
        {dropdownItems.length > 0 && (
          <div className="flex-shrink-0">
            <Dropdown
              trigger={
                <button className="p-1 text-slate-400 hover:text-ice-gold-400 transition-colors rounded-md hover:bg-slate-700">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
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
