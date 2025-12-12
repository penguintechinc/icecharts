import Card from '../Card';
import Avatar from '../Avatar';
import Badge from '../Badge';
import Dropdown from '../Dropdown';

interface GroupMember {
  name: string;
  initials: string;
  avatar?: string;
}

interface GroupCardProps {
  id: string;
  name: string;
  description?: string;
  memberCount: number;
  members?: GroupMember[];
  createdDate: Date;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onViewMembers?: (id: string) => void;
  className?: string;
}

export default function GroupCard({
  id,
  name,
  description,
  memberCount,
  members = [],
  createdDate,
  onEdit,
  onDelete,
  onViewMembers,
  className = '',
}: GroupCardProps) {
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const dropdownItems = [
    ...(onViewMembers ? [{
      id: 'view-members',
      label: 'View Members',
      icon: '👥',
      onClick: () => onViewMembers(id),
    }] : []),
    ...(onEdit ? [{
      id: 'edit',
      label: 'Edit',
      icon: '✏️',
      onClick: () => onEdit(id),
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

  const displayMembers = members.slice(0, 3);
  const remainingCount = Math.max(0, memberCount - 3);

  return (
    <Card className={`hover:border-ice-gold-400/50 transition-colors ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="text-lg font-semibold text-ice-gold-400 truncate">
            {name}
          </h3>

          {/* Description */}
          {description && (
            <p className="mt-1 text-sm text-slate-400 line-clamp-2">
              {description}
            </p>
          )}

          {/* Member Info */}
          <div className="mt-3 flex items-center gap-3">
            {/* Member Avatars */}
            <div className="flex -space-x-2">
              {displayMembers.map((member, idx) => (
                <Avatar
                  key={idx}
                  src={member.avatar}
                  initials={member.initials}
                  size="sm"
                  className="ring-2 ring-slate-800"
                />
              ))}
              {remainingCount > 0 && (
                <div className="h-8 w-8 rounded-full bg-slate-700 ring-2 ring-slate-800 flex items-center justify-center text-xs font-semibold text-slate-300">
                  +{remainingCount}
                </div>
              )}
            </div>

            {/* Member Count Badge */}
            <Badge variant="info" size="sm">
              {memberCount} {memberCount === 1 ? 'member' : 'members'}
            </Badge>
          </div>

          {/* Created Date */}
          <p className="mt-2 text-xs text-slate-500">
            Created {formatDate(createdDate)}
          </p>
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
