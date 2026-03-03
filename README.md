# Europapark API Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Unofficial REST API server providing real-time Europapark data including attraction wait times, show schedules, opening hours, and comprehensive POI information.

## Features

- **Real-time Wait Times** — Current queue times for all attractions with status indicators
- **Show Schedules** — Today's and tomorrow's show times with locations
- **Opening Hours** — Park opening times and season information
- **POI Data** — Detailed information for attractions, shows, shops, restaurants, and services
- **Auto-Caching** — Intelligent caching with configurable refresh intervals
- **Interactive Docs** — Built-in Swagger UI at `/docs`

## Quick Start

### Prerequisites

- Python 3.11 or higher
- API credentials (see [Configuration](#configuration))

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/europapark-api-server.git
cd europapark-api-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Run

```bash
uvicorn main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive documentation.

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Database connection string (default: SQLite) |
| `FB_APP_ID` | Firebase App ID |
| `FB_API_KEY` | Firebase API Key |
| `FB_PROJECT_ID` | Firebase Project ID |
| `ENC_KEY` | Encryption key for credential decryption |
| `ENC_IV` | Encryption initialization vector |

## API Endpoints

### Times

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/times/waittimes` | All attraction wait times |
| GET | `/times/waittimes/{id}` | Wait time for specific attraction |
| GET | `/times/showtimes` | All show times |
| GET | `/times/showtimes/{id}` | Show times for specific show |
| GET | `/times/openingtimes` | Current opening hours |
| GET | `/times/seasons` | Season information |

### Info

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/info/attractions` | All attractions |
| GET | `/info/attractions/{id}` | Attraction details |
| GET | `/info/shows` | All shows |
| GET | `/info/shows/{id}` | Show details |
| GET | `/info/shops` | All shops |
| GET | `/info/restaurants` | All restaurants |
| GET | `/info/services` | All service facilities |

### Raw Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/raw/waittimes` | Unprocessed wait times |
| GET | `/raw/pois` | Unprocessed POI data |
| GET | `/raw/seasons` | Unprocessed season data |
| GET | `/raw/openingtimes` | Unprocessed opening times |
| GET | `/raw/showtimes` | Unprocessed show times |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

## Deployment

### Docker

```bash
docker build -t europapark-api .
docker run -p 8000:8000 --env-file .env europapark-api
```

### Nixpacks

```bash
nixpacks build . -o out
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Project Structure

```
├── main.py              # Application entry point
├── config.py            # Configuration management
├── database.py          # Database setup
├── routers/             # API route handlers
│   ├── waittimes.py
│   ├── showtimes.py
│   ├── attractions.py
│   └── ...
└── services/            # Business logic
    ├── auth.py          # OAuth2 authentication
    ├── cache.py         # Data caching
    ├── europapark_api.py
    └── ...
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Disclaimer

**This project is not affiliated with, endorsed by, or connected to Europa-Park GmbH & Co Mack KG in any way.**

This is an unofficial, community-driven project that accesses publicly available data. Use at your own risk. The developers are not responsible for any misuse or any consequences arising from the use of this software.

All trademarks, service marks, and company names are the property of their respective owners.
