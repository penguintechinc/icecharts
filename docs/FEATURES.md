# IceCharts Features Guide

Comprehensive guide to all features in IceCharts.

## Table of Contents

- [Canvas & Drawing](#canvas--drawing)
- [Real-Time Collaboration](#real-time-collaboration)
- [Comments System](#comments-system)
- [Export & Sharing](#export--sharing)
- [Elder Integration](#elder-integration)
- [Team Management](#team-management)
- [User Roles & Permissions](#user-roles--permissions)

---

## Canvas & Drawing

### Creating Diagrams

**Start a New Diagram**:
1. Click **New Diagram** on Dashboard
2. Enter diagram name and description
3. Choose starting template or blank canvas
4. Click **Create**

**Available Templates**:
- **Blank Canvas** - Empty starting point
- **System Architecture** - Pre-configured for infrastructure diagrams
- **Flowchart** - Shapes and flows pre-configured
- **Organizational Chart** - Hierarchy visualization
- **Entity Relationship** - Database schema diagrams
- **Network Topology** - Network infrastructure diagrams

### Shape Library

**Built-in Shapes**:

| Category | Shapes |
|----------|--------|
| **Basic** | Rectangle, Circle, Triangle, Diamond, Pentagon, Star |
| **Infrastructure** | Server, Database, LoadBalancer, Cache, Storage, Queue |
| **Flowchart** | Process, Decision, Terminator, Input/Output, Document |
| **Org Chart** | Person, Team, Department, Company |
| **Network** | Router, Switch, Firewall, Cloud, Connector |
| **Database** | Table, View, Procedure, Trigger, Index |

### Adding & Editing Shapes

**Add Shape**:
1. Click shape in left palette
2. Click on canvas to place
3. Drag to resize
4. Double-click to edit text

**Edit Shape**:
1. Click to select (shows resize handles)
2. Edit properties in right panel:
   - **Text**: Double-click or edit in properties
   - **Color**: Click color picker
   - **Style**: Line width, fill, opacity
   - **Metadata**: Custom properties (key-value pairs)

**Delete Shape**:
- Select and press Delete key
- Or right-click → Delete

### Connectors & Relationships

**Create Connector**:
1. Click shape to select
2. Drag from connection point to target shape
3. Release to create connector

**Edit Connector**:
1. Click to select connector
2. Adjust in properties panel:
   - **Label**: Add relationship text
   - **Style**: Line color, width, pattern
   - **Endpoints**: Arrow style (none/line/arrow)

**Connector Routing**:
- **Automatic**: System routes around obstacles
- **Straight**: Direct line between shapes
- **Curved**: Smooth bezier curves
- **Orthogonal**: Right-angle routing

### Canvas Controls

**Zoom**:
- Mouse wheel to zoom in/out
- **Ctrl+0** (or **Cmd+0**) to fit all
- Zoom slider in top toolbar
- Double-click shape to zoom to it

**Pan**:
- Middle mouse button drag
- Space + mouse drag
- Arrow keys to nudge view

**Grid & Snap**:
- Toggle grid in View menu
- Enable "Snap to grid" in preferences
- Adjust grid size in settings

**Select Multiple**:
- Click-drag to select area
- Ctrl+Click to add to selection
- Ctrl+A to select all

**Alignment & Distribution**:
1. Select multiple shapes
2. Use Align menu:
   - Align left/center/right
   - Align top/middle/bottom
   - Distribute horizontally/vertically

### Undo & History

- **Undo**: Ctrl+Z (or Cmd+Z)
- **Redo**: Ctrl+Y (or Cmd+Y)
- **History Panel**: View and restore previous versions
- **Auto-save**: Every change automatically saved

---

## Real-Time Collaboration

### Multi-User Editing

**Enable Collaboration**:
1. Open diagram
2. Click **Share** button
3. Enter collaborator emails
4. Set permission level (View/Edit)

**While Collaborating**:
- See live cursors of other users
- View presence indicators (top-right)
- See changes appear instantly
- Chat in sidebar (optional)

### Presence Awareness

**Presence Indicators**:
- **Color-coded cursors** - Each user has unique cursor color
- **User list** - Shows "currently editing" in top-right
- **Hover over name** - See their cursor location
- **Change notifications** - "John is adding a shape..."

### Conflict Resolution

**Concurrent Edits**:
- Last write wins (with timestamp)
- Changes from other users appear instantly
- Your unsaved changes are preserved
- Manual merge if significant conflicts

### Lock Management

**Shape Locks**:
- Locks apply only during active editing
- Automatically release after 5 minutes of inactivity
- You can view locked shapes but not edit them
- Lock indicator shows who's editing

---

## Comments System

The Comments System enables rich feedback and collaborative design review.

### Leaving Comments

**Add Comment**:
1. Click shape or click-drag to select area
2. Click comment icon or Ctrl+M
3. Type comment (up to 5000 characters)
4. Click **Post Comment**

**Reply to Comment**:
1. Click **Reply** on existing comment
2. Type your reply
3. Click **Post Reply**

### Comment Features

**Comment Types**:
- **General**: On the drawing itself
- **Shape-specific**: Attached to specific element
- **Threaded**: Replies create comment threads

**Comment Filters**:
- **All**: Show all comments
- **Open**: Only unresolved comments
- **Resolved**: Only resolved comments
- **By Shape**: Filter by specific element

**Comment Markers**:
- Small badge on shapes with comments
- Red = unresolved comments
- Green = all comments resolved
- Number shows comment count

### Resolution Workflow

**Resolve Comment**:
1. Right-click comment
2. Select **Mark as Resolved**
3. Add optional resolution note
4. Comment marked complete

**Unresolve**:
- Click **Unresolve** to reopen discussion
- Useful if issue reoccurs

**Statistics**:
- View in Comments Summary panel
- Shows:
  - Total comments
  - Resolved vs unresolved count
  - Comments by shape
  - Recently updated items

### Comment Notifications

- **Email notifications** when someone replies to your comment
- **Real-time updates** in comments panel
- **@mentions** to tag specific users
- **Digest emails** summarizing daily activity

---

## Export & Sharing

### Export Formats

**PNG Export**:
- Raster image format
- Best for sharing in documents
- Configurable resolution (72-300 DPI)
- Transparent background option

**SVG Export**:
- Vector format, editable
- Preserves all properties
- Infinitely scalalable
- Can be edited in Illustrator/Inkscape

**PDF Export**:
- Print-ready format
- Single or multi-page
- Embed metadata
- Configure page size and margins

**JSON Export**:
- Full diagram data
- For backup/import
- Includes all comments and metadata
- Version-controlled

### Export Options

**Size Configuration**:
- **Fit to content**: Auto-size to diagram bounds
- **Custom width/height**: Set exact dimensions
- **Scale by percentage**: Scale from current view

**Quality Settings**:
- **Resolution**: 72-300 DPI
- **Compression**: Quality vs file size tradeoff
- **Metadata**: Include or exclude comments

**Export Dialog**:
1. Click **Export** menu
2. Choose format
3. Configure options
4. Click **Export**
5. File downloads automatically

### Sharing Diagrams

**Public Sharing**:
1. Click **Share** button
2. Toggle "Make Public"
3. Copy public link
4. Anyone with link can view

**Team Sharing**:
1. Click **Share** button
2. Enter team member email
3. Set permission level:
   - **View**: Read-only access
   - **Edit**: Can modify diagram
   - **Comment**: Can only add comments
4. Member receives invitation

**Share Permissions**:
| Permission | View | Edit | Comment | Export |
|-----------|------|------|---------|--------|
| **View** | ✓ | - | - | - |
| **Comment** | ✓ | - | ✓ | - |
| **Edit** | ✓ | ✓ | ✓ | ✓ |

**Manage Shares**:
1. Open diagram
2. Click **Share** button
3. See list of people with access
4. Adjust permissions or revoke access

### Version Control

**Version History**:
1. Click **History** in top menu
2. See all saved versions with timestamps
3. Click version to view snapshot
4. Restore to any previous version

**Automatic Snapshots**:
- Created on each save
- Kept for 30 days (or custom duration)
- Labeled with timestamp and author
- Automatic cleanup of old versions

---

## Elder Integration

### What is Elder?

Elder is an infrastructure discovery and documentation system. IceCharts integrates with Elder to import infrastructure entities as diagram shapes.

### Connecting to Elder

**Add Elder Connection**:
1. Go to **Settings** → **Integrations**
2. Click **Connect to Elder**
3. Enter Elder instance URL
4. Provide API key
5. Click **Test Connection**
6. Click **Save**

**Retrieve Credentials**:
- Contact your Elder administrator
- Generate API key in Elder settings
- Store API key securely

### Importing Infrastructure

**Import Entities**:
1. Open diagram
2. Click **Insert** → **Import from Elder**
3. Select Elder connection
4. Choose entities to import:
   - Servers
   - Databases
   - Load balancers
   - Storage systems
   - Custom resources
5. Configure layout
6. Click **Import**

**Entity Mapping**:
Imported entities automatically mapped to shapes:
- **Servers** → Rectangle (blue)
- **Databases** → Database symbol (orange)
- **Load Balancers** → Network shape (green)
- **Cache** → Cache symbol (purple)
- **Custom** → Generic shape

**Properties Imported**:
- Entity name
- Entity type
- Status (active/inactive)
- Location/region
- Owner/team
- Custom metadata

### Import Options

**Layout Algorithms**:
- **Hierarchical**: Top-down dependency flow
- **Force-directed**: Organic clustering
- **Grid**: Organized in grid pattern
- **Circular**: Radial layout

**Include Relationships**:
- Toggle to auto-create connectors
- Shows dependencies between entities
- Color-coded by relationship type

**Refresh Strategy**:
- **One-time import**: Static snapshot
- **Live sync** (pro feature): Periodic updates
- Manual refresh available

### Dependency Visualization

**Dependency Types**:
- **Depends on**: Entity requires another
- **Provides to**: Entity serves another
- **Related to**: Associated entities

**Visual Indicators**:
- Arrow direction shows flow
- Color indicates type
- Labels show relationship details

---

## Team Management

### Creating Teams

**Add Team**:
1. Go to **Settings** → **Teams**
2. Click **Create Team**
3. Enter team name and description
4. Add team members
5. Set member roles (Admin/Member)
6. Click **Create**

**Team Structure**:
- Create teams for departments
- Teams can have sub-teams
- Flexible hierarchy support

### Team Permissions

**Team Admin**:
- Manage team members
- Delete team
- Change team settings
- Assign team roles

**Team Member**:
- Access team diagrams
- Collaborate on shared content
- View team settings (read-only)

**Shared Diagrams**:
- Assign diagrams to teams
- All team members get access
- Set team-wide permissions

### Team Collaboration

**Team Dashboard**:
- View all team diagrams
- See recent activity
- Manage team resources
- Track team members

**Team Comments**:
- Comment threads are team-visible
- Mentions notify team members
- Shared comment resolution status

---

## User Roles & Permissions

### Role Hierarchy

**Admin**:
- Full system access
- Manage all users
- Manage teams and groups
- Configure system settings
- Manage integrations
- View audit logs

**Maintainer**:
- Create and edit diagrams
- Manage own diagrams
- Invite users to diagrams
- Manage own team
- Create comments and replies
- Access API

**Viewer**:
- View shared diagrams (read-only)
- Add comments to diagrams
- Export diagrams
- No editing capabilities
- Cannot manage resources

### Resource Permissions

**Per-Resource Access**:
- Diagram-level permissions
- User-specific access
- Time-based expiration
- Can be revoked anytime

**Permission Levels**:
- **Owner**: Full control (creator)
- **Editor**: Can modify content
- **Commenter**: View and comment only
- **Viewer**: View only
- **None**: No access (revoked)

---

## Advanced Features

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| **New Diagram** | Ctrl+N |
| **Open Diagram** | Ctrl+O |
| **Save** | Ctrl+S |
| **Undo** | Ctrl+Z |
| **Redo** | Ctrl+Y |
| **Copy** | Ctrl+C |
| **Paste** | Ctrl+V |
| **Delete** | Delete |
| **Select All** | Ctrl+A |
| **Search** | Ctrl+F |
| **Export** | Ctrl+E |
| **Zoom In** | Ctrl++ |
| **Zoom Out** | Ctrl+- |
| **Fit All** | Ctrl+0 |

### Performance Tips

1. **Large Diagrams**:
   - Split into multiple diagrams
   - Use references/links between diagrams
   - Archive old versions

2. **Collaboration Performance**:
   - Limit to 5-10 concurrent editors
   - Use comments for feedback (not editing)
   - Establish edit regions

3. **Export Performance**:
   - Export is async (doesn't block editing)
   - Large diagrams may take time
   - Check export status in menu

### Accessibility

**Keyboard Navigation**:
- Tab through elements
- Arrow keys to move selected items
- Enter to edit selected item
- Escape to deselect

**Screen Reader Support**:
- Diagrams have text descriptions
- Comments accessible via keyboard
- Menu structure navigable

**High Contrast Mode**:
- Supported in settings
- Improves visibility
- Recommended for accessibility

---

## Related Documentation

- [Getting Started](GETTING_STARTED.md) - Setup guide
- [API Reference](API_REFERENCE.md) - For developers
- [Comments System](COMMENTS_SYSTEM.md) - Detailed comments documentation
- [Export Functionality](EXPORT_FUNCTIONALITY.md) - Export details
- [Elder Integration](ELDER_INTEGRATION.md) - Elder setup guide
- [Architecture](ARCHITECTURE.md) - System design
