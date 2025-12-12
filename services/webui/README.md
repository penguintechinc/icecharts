# IceCharts WebUI

Real-time collaborative diagramming and flowchart creation interface built with React, TypeScript, and @xyflow/react.

## Features

- **Real-time Collaboration**: Multiple users can edit diagrams simultaneously via WebSocket
- **Flow Diagram Editor**: Powered by @xyflow/react for interactive node-based diagrams
- **Authentication**: JWT-based authentication with role-based access control
- **Modern UI**: Dark mode with gold/navy color scheme using Tailwind CSS
- **Type Safety**: Full TypeScript support with strict type checking
- **State Management**: Zustand for lightweight and efficient state management

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety and developer experience
- **Vite** - Build tool and dev server
- **@xyflow/react** - Flow diagram and node editor
- **Socket.io-client** - Real-time WebSocket communication
- **Zustand** - State management
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing

## Getting Started

### Prerequisites

- Node.js 20.x or higher
- npm 10.x or higher

### Installation

```bash
# Install dependencies
npm install

# Create .env file from example
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`.

### Development

```bash
# Start dev server
npm run dev

# Type checking
npm run typecheck

# Linting
npm run lint
npm run lint:fix

# Code formatting
npm run format

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── components/      # Reusable React components
├── pages/          # Page components (routes)
├── lib/            # Utility libraries
│   ├── api.ts      # Axios API client
│   └── websocket.ts # Socket.io client
├── store/          # Zustand state stores
│   └── authStore.ts # Authentication state
├── types/          # TypeScript type definitions
├── App.tsx         # Main app component with routing
├── main.tsx        # Application entry point
└── index.css       # Global styles and Tailwind imports
```

## Color Scheme

### Dark Mode (Default)
- Background: Gray-900 (`#111827`)
- Text: Amber-400 (`#fbbf24`) for primary, white for secondary
- Accents: Navy-800 (`#243b53`) for cards and surfaces

### Light Mode
- Background: White
- Text: Gray-900 for primary
- Accents: Ice-blue and navy tones

## API Integration

The WebUI proxies API requests to the Flask backend:

- `/api/*` → `http://localhost:5000/api/*`
- `/socket.io/*` → `http://localhost:5000/socket.io/*`

Configure the backend URL via `VITE_API_URL` environment variable.

## Docker Deployment

Multi-stage Docker build with nginx for production:

```bash
# Build image
docker build -t icecharts-webui .

# Run container
docker run -p 80:80 icecharts-webui
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:5000` |
| `VITE_WS_URL` | WebSocket server URL | `http://localhost:5000` |
| `NODE_ENV` | Environment mode | `development` |

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari 14+

## License

Limited AGPL3 - See LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [IceCharts Issues](https://github.com/penguintechinc/IceCharts/issues)
- Email: support@penguintech.io
