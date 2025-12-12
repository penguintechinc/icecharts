import { useAuthStore } from '../store/authStore';

export type Role = 'global_admin' | 'group_admin' | 'maintainer' | 'editor' | 'viewer';

const ROLE_HIERARCHY: Record<Role, number> = {
  global_admin: 100,
  group_admin: 80,
  maintainer: 60,
  editor: 40,
  viewer: 20,
};

export interface UsePermissionsReturn {
  isAuthenticated: boolean;
  isGlobalAdmin: boolean;
  hasRole: (minRole: Role) => boolean;
  canViewDrawing: (drawing: { owner_id: string; is_public?: boolean }) => boolean;
  canEditDrawing: (drawing: { owner_id: string }) => boolean;
  canDeleteDrawing: (drawing: { owner_id: string }) => boolean;
  canManageGroup: (groupRole?: Role) => boolean;
  canShareDrawing: (drawing: { owner_id: string }) => boolean;
  canAccessAdmin: () => boolean;
}

export function usePermissions(): UsePermissionsReturn {
  const { user, isAuthenticated } = useAuthStore();

  const userRole = (user?.role as Role) || 'viewer';
  const userId = user?.id;

  const isGlobalAdmin = userRole === 'global_admin';

  const hasRole = (minRole: Role): boolean => {
    if (!isAuthenticated) return false;
    return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[minRole];
  };

  const canViewDrawing = (drawing: { owner_id: string; is_public?: boolean }): boolean => {
    if (drawing.is_public) return true;
    if (!isAuthenticated) return false;
    if (isGlobalAdmin) return true;
    if (drawing.owner_id === String(userId)) return true;
    // Additional share-based checks would happen server-side
    return true;
  };

  const canEditDrawing = (drawing: { owner_id: string }): boolean => {
    if (!isAuthenticated) return false;
    if (isGlobalAdmin) return true;
    if (drawing.owner_id === String(userId)) return true;
    return hasRole('editor');
  };

  const canDeleteDrawing = (drawing: { owner_id: string }): boolean => {
    if (!isAuthenticated) return false;
    if (isGlobalAdmin) return true;
    if (drawing.owner_id === String(userId)) return true;
    return false;
  };

  const canManageGroup = (groupRole?: Role): boolean => {
    if (!isAuthenticated) return false;
    if (isGlobalAdmin) return true;
    if (groupRole === 'group_admin') return true;
    return false;
  };

  const canShareDrawing = (drawing: { owner_id: string }): boolean => {
    if (!isAuthenticated) return false;
    if (isGlobalAdmin) return true;
    if (drawing.owner_id === String(userId)) return true;
    return hasRole('editor');
  };

  const canAccessAdmin = (): boolean => {
    return isGlobalAdmin;
  };

  return {
    isAuthenticated,
    isGlobalAdmin,
    hasRole,
    canViewDrawing,
    canEditDrawing,
    canDeleteDrawing,
    canManageGroup,
    canShareDrawing,
    canAccessAdmin,
  };
}

export default usePermissions;
