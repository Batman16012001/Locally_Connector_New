# Locally Data Connector

A FastAPI-based data connector for ingesting data from various sources (currently CSV) into MongoDB.

## Features

- CSV file ingestion with validation
- Batch processing for large files
- Rate limiting
- MongoDB integration
- Async processing
- Error handling and logging
- Swagger UI documentation

## Prerequisites

- Python 3.11+
- MongoDB
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd locally-connector
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=locally_staging
BATCH_SIZE=500
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_PERIOD=60
```

## Running the Application

1. Start MongoDB:
```bash
mongod
```

2. Start the FastAPI application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## API Endpoints

### POST /api/v1/ingest-csv
Upload and process a CSV file.

**Request:**
- Content-Type: multipart/form-data
- Body: CSV file

**Response:**
```json
{
    "message": "CSV processing completed",
    "details": {
        "total_records": 7500,
        "successful_records": 7480,
        "failed_records": 20,
        "errors": [...]
    }
}
```

## Error Handling

The API includes comprehensive error handling for:
- Invalid file formats
- Malformed CSV data
- Database connection issues
- Rate limiting
- Server errors

## Future Enhancements

- Support for additional data sources (APIs, databases, etc.)
- Nested document structure support
- Data transformation capabilities
- Advanced validation rules
- Monitoring and metrics
- Authentication and authorization 