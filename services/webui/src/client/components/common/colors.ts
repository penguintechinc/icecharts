/**
 * Color scheme constants for IceCharts UI
 * Dark theme with gold accents
 */

export const colors = {
  // Primary (Gold/Amber)
  primary: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },

  // Background (Slate)
  background: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
    950: '#020617',
  },

  // Status Colors
  success: {
    light: '#d1fae5',
    main: '#10b981',
    dark: '#047857',
  },
  warning: {
    light: '#fef3c7',
    main: '#f59e0b',
    dark: '#d97706',
  },
  error: {
    light: '#fee2e2',
    main: '#ef4444',
    dark: '#dc2626',
  },
  info: {
    light: '#dbeafe',
    main: '#3b82f6',
    dark: '#1d4ed8',
  },

  // Role-based Colors
  roles: {
    admin: {
      bg: 'bg-red-900/50',
      text: 'text-red-400',
    },
    maintainer: {
      bg: 'bg-blue-900/50',
      text: 'text-blue-400',
    },
    viewer: {
      bg: 'bg-green-900/50',
      text: 'text-green-400',
    },
  },

  // Semantic
  text: {
    primary: '#f1f5f9',
    secondary: '#cbd5e1',
    muted: '#94a3b8',
    disabled: '#64748b',
  },
  border: '#475569',
  surface: '#1e293b',
  overlay: 'rgba(15, 23, 42, 0.5)',
};

/**
 * Utility function to get role colors
 */
export const getRoleColor = (role: 'admin' | 'maintainer' | 'viewer') => {
  return colors.roles[role];
};

/**
 * Utility function to get status color
 */
export const getStatusColor = (status: 'success' | 'warning' | 'error' | 'info') => {
  const statusColors = {
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
  };
  return statusColors[status];
};
