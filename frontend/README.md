# Farsight Frontend

Vue 3 + Vite + Tailwind CSS frontend for the Farsight Firewall Analysis System.

## 🚀 Quick Start

### Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Open http://localhost:3000

### Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── assets/          # Static assets (CSS, images)
│   ├── components/       # Vue components
│   │   ├── ui/          # Base UI components
│   │   └── layout/      # Layout components
│   ├── composables/     # Vue composables (hooks)
│   ├── router/          # Vue Router configuration
│   ├── services/        # API services
│   ├── views/           # Page components
│   ├── App.vue          # Root component
│   └── main.js          # Application entry point
├── index.html           # HTML template
├── package.json         # Dependencies
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
└── Dockerfile           # Docker configuration
```

## 🎨 Design System

The application uses a custom design system built on Tailwind CSS:

- **Colors**: Primary, Secondary, Success, Error, Warning
- **Typography**: System font stack with semantic heading sizes
- **Components**: Reusable UI components in `src/components/ui/`

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Farsight
```

### API Configuration

The API base URL is configured in `src/services/api.ts` and can be overridden with the `VITE_API_BASE_URL` environment variable.

## 📦 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🐳 Docker

### Development

The frontend can be run in Docker using the existing `Dockerfile` (for static files) or the new `Dockerfile.new` (for Vite build).

### Production Build

```bash
docker build -f Dockerfile.new -t farsight-frontend .
docker run -p 3000:80 farsight-frontend
```

## 📚 Documentation

See the [Frontend Rebuild Plan](../docs/FRONTEND_REBUILD_PLAN.md) for detailed implementation phases.
