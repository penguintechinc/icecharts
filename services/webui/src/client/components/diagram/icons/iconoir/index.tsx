/**
 * Iconoir Icon Adapter
 * Imports icons from iconoir-react package and wraps them to conform to IconProps
 */

import { FC } from 'react';
import * as IconoirIcons from 'iconoir-react';
import type { IconProps, IconComponent, IconMap } from '../types';

/**
 * Wrapper function to create a normalized icon component from iconoir icon
 */
const createIconComponent = (IconComponent: any): IconComponent => {
  const WrappedIcon: FC<IconProps> = ({
    className,
    size = 24,
    color = '#8B5CF6',
  }) => {
    const sizeNum = typeof size === 'string' ? parseInt(size, 10) : size;
    return (
      <IconComponent
        width={sizeNum}
        height={sizeNum}
        color={color}
        strokeWidth={2}
        className={className}
      />
    );
  };
  WrappedIcon.displayName = `IconoirIcon`;
  return WrappedIcon;
};

/**
 * Iconoir Icon Map - 50+ useful icons categorized by type
 * Each icon is wrapped to accept standard IconProps (className, size, color)
 */
export const iconoirIconMap: IconMap = {
  // 3D & Design Icons
  'iconoir-3d-box': createIconComponent(IconoirIcons.Cube),
  'iconoir-design': createIconComponent(IconoirIcons.DesignNib),
  'iconoir-palette': createIconComponent(IconoirIcons.Palette),
  'iconoir-pen': createIconComponent(IconoirIcons.EditPencil),
  'iconoir-draw': createIconComponent(IconoirIcons.Brush),

  // Navigation Icons
  'iconoir-navigation': createIconComponent(IconoirIcons.Navigator),
  'iconoir-arrow-up': createIconComponent(IconoirIcons.ArrowUp),
  'iconoir-arrow-down': createIconComponent(IconoirIcons.ArrowDown),
  'iconoir-arrow-left': createIconComponent(IconoirIcons.ArrowLeft),
  'iconoir-arrow-right': createIconComponent(IconoirIcons.ArrowRight),
  'iconoir-chevron-up': createIconComponent(IconoirIcons.NavArrowUp),
  'iconoir-chevron-down': createIconComponent(IconoirIcons.NavArrowDown),
  'iconoir-chevron-left': createIconComponent(IconoirIcons.NavArrowLeft),
  'iconoir-chevron-right': createIconComponent(IconoirIcons.NavArrowRight),
  'iconoir-expand': createIconComponent(IconoirIcons.Expand),
  'iconoir-collapse': createIconComponent(IconoirIcons.Collapse),
  'iconoir-zoom-in': createIconComponent(IconoirIcons.ZoomIn),
  'iconoir-zoom-out': createIconComponent(IconoirIcons.ZoomOut),

  // Actions Icons
  'iconoir-copy': createIconComponent(IconoirIcons.Copy),
  'iconoir-paste': createIconComponent(IconoirIcons.Paste),
  'iconoir-delete': createIconComponent(IconoirIcons.Delete),
  'iconoir-trash': createIconComponent(IconoirIcons.Trash),
  'iconoir-download': createIconComponent(IconoirIcons.Download),
  'iconoir-upload': createIconComponent(IconoirIcons.Upload),
  'iconoir-save': createIconComponent(IconoirIcons.Save),
  'iconoir-refresh': createIconComponent(IconoirIcons.Refresh),
  'iconoir-reload': createIconComponent(IconoirIcons.Reload),
  'iconoir-undo': createIconComponent(IconoirIcons.Undo),
  'iconoir-redo': createIconComponent(IconoirIcons.Redo),
  'iconoir-close': createIconComponent(IconoirIcons.Cancel),
  'iconoir-check': createIconComponent(IconoirIcons.Check),
  'iconoir-plus': createIconComponent(IconoirIcons.Plus),
  'iconoir-minus': createIconComponent(IconoirIcons.Minus),

  // Communication Icons
  'iconoir-mail': createIconComponent(IconoirIcons.Mail),
  'iconoir-message': createIconComponent(IconoirIcons.Message),
  'iconoir-chat': createIconComponent(IconoirIcons.Chat),
  'iconoir-comment': createIconComponent(IconoirIcons.Comment),
  'iconoir-phone': createIconComponent(IconoirIcons.Phone),
  'iconoir-bell': createIconComponent(IconoirIcons.Bell),
  'iconoir-notification': createIconComponent(IconoirIcons.Notification),
  'iconoir-share': createIconComponent(IconoirIcons.Share),
  'iconoir-link': createIconComponent(IconoirIcons.Link),

  // Finance Icons
  'iconoir-money': createIconComponent(IconoirIcons.Money),
  'iconoir-wallet': createIconComponent(IconoirIcons.Wallet),
  'iconoir-credit-card': createIconComponent(IconoirIcons.CreditCard),
  'iconoir-currency': createIconComponent(IconoirIcons.Currency),
  'iconoir-dollar': createIconComponent(IconoirIcons.Dollar),

  // System Icons
  'iconoir-server': createIconComponent(IconoirIcons.Server),
  'iconoir-database': createIconComponent(IconoirIcons.Database),
  'iconoir-cloud': createIconComponent(IconoirIcons.Cloud),
  'iconoir-settings': createIconComponent(IconoirIcons.Settings),
  'iconoir-gear': createIconComponent(IconoirIcons.Gear),
  'iconoir-tool': createIconComponent(IconoirIcons.Tool),
  'iconoir-wrench': createIconComponent(IconoirIcons.Wrench),
  'iconoir-config': createIconComponent(IconoirIcons.Cog),
  'iconoir-power': createIconComponent(IconoirIcons.Power),
  'iconoir-battery': createIconComponent(IconoirIcons.Battery),

  // Development Icons
  'iconoir-code': createIconComponent(IconoirIcons.Code),
  'iconoir-git': createIconComponent(IconoirIcons.Git),
  'iconoir-github': createIconComponent(IconoirIcons.Github),
  'iconoir-terminal': createIconComponent(IconoirIcons.Terminal),
  'iconoir-console': createIconComponent(IconoirIcons.Terminal),
  'iconoir-bug': createIconComponent(IconoirIcons.Bug),
  'iconoir-test-tube': createIconComponent(IconoirIcons.TestTube),

  // File & Document Icons
  'iconoir-file': createIconComponent(IconoirIcons.File),
  'iconoir-folder': createIconComponent(IconoirIcons.Folder),
  'iconoir-document': createIconComponent(IconoirIcons.Document),
  'iconoir-pdf': createIconComponent(IconoirIcons.PdfFile),

  // User & Account Icons
  'iconoir-user': createIconComponent(IconoirIcons.User),
  'iconoir-profile': createIconComponent(IconoirIcons.Profile),
  'iconoir-people': createIconComponent(IconoirIcons.People),
  'iconoir-team': createIconComponent(IconoirIcons.People),
  'iconoir-lock': createIconComponent(IconoirIcons.Lock),
  'iconoir-unlock': createIconComponent(IconoirIcons.Unlock),

  // Status & Feedback Icons
  'iconoir-success': createIconComponent(IconoirIcons.CheckCircle),
  'iconoir-error': createIconComponent(IconoirIcons.XmarkCircle),
  'iconoir-warning': createIconComponent(IconoirIcons.WarningTriangle),
  'iconoir-info': createIconComponent(IconoirIcons.InfoEmpty),
  'iconoir-question': createIconComponent(IconoirIcons.HelpCircle),
  'iconoir-spinner': createIconComponent(IconoirIcons.Spinner),

  // Common UI Icons
  'iconoir-home': createIconComponent(IconoirIcons.Home),
  'iconoir-search': createIconComponent(IconoirIcons.Search),
  'iconoir-eye': createIconComponent(IconoirIcons.Eye),
  'iconoir-eye-off': createIconComponent(IconoirIcons.EyeOff),
  'iconoir-star': createIconComponent(IconoirIcons.Star),
  'iconoir-heart': createIconComponent(IconoirIcons.Heart),
  'iconoir-bookmark': createIconComponent(IconoirIcons.Bookmark),
  'iconoir-flag': createIconComponent(IconoirIcons.Flag),
  'iconoir-filter': createIconComponent(IconoirIcons.Filter),
  'iconoir-list': createIconComponent(IconoirIcons.List),
  'iconoir-grid': createIconComponent(IconoirIcons.Grid),
  'iconoir-table': createIconComponent(IconoirIcons.Table),
  'iconoir-menu': createIconComponent(IconoirIcons.Menu),
  'iconoir-more': createIconComponent(IconoirIcons.MoreVert),
  'iconoir-dots': createIconComponent(IconoirIcons.MoreVert),
};

/**
 * Get an icon component by ID
 */
export const getIconoirIcon = (id: string): IconComponent | undefined => {
  return iconoirIconMap[id];
};

/**
 * List all available iconoir icon IDs
 */
export const listIconoirIcons = (): string[] => {
  return Object.keys(iconoirIconMap);
};

export default iconoirIconMap;
