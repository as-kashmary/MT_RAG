# Docker build and deployment instructions

## Quick Start

### Build and run with Docker Compose (recommended)
```bash
docker-compose up --build
```

This starts:
- MongoDB (port 27017)
- MySQL (port 3306)
- Admin Server (port 8000)
- User Server (port 8001)

### Individual Docker Commands

**Build image:**
```bash
docker build -t mt-rag:latest .
```

**Run Admin Server:**
```bash
docker run -d --name mt-rag-admin \
  -p 8000:8000 \
  -e MONGODB_URL=mongodb://admin:password@mongodb:27017/ \
  -e MYSQL_HOST=mysql \
  -e MYSQL_USER=appuser \
  -e MYSQL_PASSWORD=app_password \
  -v ./models:/app/models \
  -v ./documents:/app/documents \
  --network mt_rag_network \
  mt-rag:latest \
  python -m uvicorn src.admin_server:app --host 0.0.0.0 --port 8000
```

**Run User Server:**
```bash
docker run -d --name mt-rag-user \
  -p 8001:8001 \
  -e MONGODB_URL=mongodb://admin:password@mongodb:27017/ \
  --network mt_rag_network \
  mt-rag:latest \
  python -m uvicorn src.user_server:app --host 0.0.0.0 --port 8001
```

## Environment Variables

Create a `.env` file in the project root:
```
MONGODB_URL=mongodb://admin:password@mongodb:27017/
MONGODB_DB=mt_rag_db
MYSQL_HOST=mysql
MYSQL_USER=appuser
MYSQL_PASSWORD=app_password
MYSQL_DATABASE=mt_rag_db
PINECONE_API_KEY=your_pinecone_key
HF_TOKEN=your_huggingface_token (if using)
```

Then load it in docker-compose:
```yaml
env_file:
  - .env
```

## Health Checks

All services include health checks. View status:
```bash
docker-compose ps
```

## Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f admin-server
docker-compose logs -f user-server
```

## Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove built images
docker image rm mt-rag:latest
```

## Notes

- Models are mounted as volumes for development. In production, consider adding them to the image.
- Update environment variables in `docker-compose.yml` with your actual credentials.
- Ensure Pinecone credentials are set via environment variables.
- The `--reload` flag in development enables auto-reload on code changes.
