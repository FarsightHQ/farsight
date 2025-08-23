# Farsight Frontend

A simple, clean web interface for the Farsight network policy analysis system.

## Features

- 📁 **File Upload**: Easy CSV file upload with drag-and-drop interface
- 🚀 **Request Management**: Create and manage FAR (Federated Access Request) analysis requests
- 🔄 **Processing Pipeline**: Step-by-step data processing workflow
- 🧮 **Facts Computation**: Both standard and hybrid facts computation
- 📊 **Results Visualization**: Clear display of analysis results and statistics
- 📋 **Rules Viewer**: Detailed view of generated firewall rules

## Quick Start

### Using Docker (Recommended)

1. Build and run the frontend container:
   ```bash
   cd frontend
   docker build -t farsight-frontend .
   docker run -p 3000:80 farsight-frontend
   ```

2. Access the application at `http://localhost:3000`

### Manual Setup

1. Serve the files using any web server:
   ```bash
   # Using Python
   python -m http.server 3000
   
   # Using Node.js
   npx serve -s . -l 3000
   
   # Using PHP
   php -S localhost:3000
   ```

## Usage Workflow

1. **Upload CSV**: Enter a request title and upload your network policy CSV file
2. **Process Data**: Click "Process CSV Data" to normalize and create rules
3. **Compute Facts**: Run standard facts computation for policy analysis
4. **Hybrid Analysis**: Execute hybrid facts computation with selective tuple storage
5. **View Results**: Review the generated rules and analysis statistics

## API Integration

The frontend communicates with the Farsight backend API running on `http://localhost:8000`.

### Required Backend Endpoints:
- `POST /api/v1/requests` - Create new request with file upload
- `POST /api/v1/requests/{id}/ingest` - Process uploaded CSV
- `POST /api/v1/requests/{id}/facts/compute` - Standard facts computation
- `POST /api/v1/requests/{id}/facts/compute-hybrid` - Hybrid facts computation
- `GET /api/v1/requests/{id}/rules` - View generated rules

## CSV File Format

The application expects CSV files with the following columns:
- `sources` - Source IP addresses/ranges
- `destinations` - Destination IP addresses/ranges  
- `services` - Protocols and port ranges (e.g., "TCP/443", "UDP/53")

Example:
```csv
sources,destinations,services
"10.0.1.0/24, 10.0.2.0/24","10.0.3.0/24","TCP/443, TCP/80"
10.0.4.100,10.0.5.0/24,UDP/53
```

## Architecture

- **Frontend**: Pure HTML5, CSS3, and Vanilla JavaScript
- **Web Server**: Nginx (in Docker container)
- **API Communication**: Fetch API for REST calls
- **Styling**: Modern CSS with gradients and animations
- **Responsive**: Mobile-friendly design

## Development

The frontend is intentionally simple with no build process required:

- `index.html` - Main application interface
- `app.js` - JavaScript application logic
- `Dockerfile` - Container configuration
- `nginx.conf` - Web server configuration

## Browser Support

- Chrome/Edge 60+
- Firefox 55+
- Safari 11+

## Security

- CORS handling for API calls
- XSS protection headers
- Content type validation
- Input sanitization
