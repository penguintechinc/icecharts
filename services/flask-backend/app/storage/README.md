# IceCharts Storage Abstraction Layer

A unified storage interface supporting multiple cloud storage providers including MinIO, AWS S3, Google Cloud Storage, OneDrive, and Google Drive.

## Features

- **Unified API**: Single interface for all storage providers
- **Async/Await**: All operations use async patterns for better performance
- **Type Hints**: Full type annotation for better IDE support
- **Error Handling**: Comprehensive exception hierarchy
- **Presigned URLs**: Support for temporary access URLs
- **Metadata Support**: Store and retrieve custom metadata
- **Dataclass Optimization**: Uses slots for memory efficiency

## Supported Providers

| Provider | Status | Features |
|----------|--------|----------|
| MinIO | ✅ Full | Upload, Download, Delete, Presigned URLs, List, Copy, Metadata |
| AWS S3 | ✅ Full | Upload, Download, Delete, Presigned URLs, List, Copy, Metadata |
| Google Cloud Storage | ✅ Full | Upload, Download, Delete, Signed URLs, List, Copy, Metadata |
| OneDrive | ✅ Full | Upload, Download, Delete, Sharing Links, List, Copy, Metadata |
| Google Drive | ✅ Full | Upload, Download, Delete, Sharing Links, List, Copy, Metadata |

## Installation

Install dependencies for the providers you need:

```bash
# MinIO
pip install minio

# AWS S3
pip install boto3

# Google Cloud Storage
pip install google-cloud-storage

# OneDrive
pip install msal requests

# Google Drive
pip install google-auth google-auth-oauthlib google-api-python-client

# Or install all at once
pip install -r storage/requirements.txt
```

## Quick Start

### Basic Usage

```python
from app.storage import get_storage_provider
import asyncio

async def main():
    # Get storage provider (reads from environment variables)
    storage = get_storage_provider()

    # Upload a file
    data = b"Hello, World!"
    await storage.upload('test.txt', data, 'text/plain')

    # Download a file
    downloaded = await storage.download('test.txt')
    print(downloaded.decode())

    # Get presigned/sharing URL
    url = await storage.get_url('test.txt', expires_in=3600)
    print(f"Access URL: {url}")

    # List files
    files = await storage.list_files(prefix='test')
    for file in files:
        print(f"{file.key}: {file.size} bytes")

    # Delete a file
    await storage.delete('test.txt')

# Run async code
asyncio.run(main())
```

### With Flask

```python
from flask import Flask, request, jsonify
from app.storage import get_storage_provider

app = Flask(__name__)
storage = get_storage_provider()

@app.route('/upload', methods=['POST'])
async def upload_file():
    file = request.files['file']
    data = file.read()

    key = await storage.upload(
        file.filename,
        data,
        file.content_type,
        metadata={'uploaded_by': 'user123'}
    )

    return jsonify({'key': key, 'status': 'success'})

@app.route('/download/<path:key>')
async def download_file(key):
    try:
        data = await storage.download(key)
        return data
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
```

## Configuration

### Environment Variables

Set `STORAGE_PROVIDER` to one of: `minio`, `s3`, `gcs`, `onedrive`, `googledrive`

#### MinIO Configuration

```bash
export STORAGE_PROVIDER=minio
export STORAGE_ENDPOINT=minio.example.com:9000
export STORAGE_ACCESS_KEY=your-access-key
export STORAGE_SECRET_KEY=your-secret-key
export STORAGE_BUCKET=your-bucket-name
export STORAGE_SECURE=true  # Use HTTPS (default: true)
```

#### AWS S3 Configuration

```bash
export STORAGE_PROVIDER=s3
export STORAGE_ACCESS_KEY=your-aws-access-key
export STORAGE_SECRET_KEY=your-aws-secret-key
export STORAGE_BUCKET=your-bucket-name
export STORAGE_REGION=us-east-1  # AWS region (default: us-east-1)
```

#### Google Cloud Storage Configuration

```bash
export STORAGE_PROVIDER=gcs
export STORAGE_BUCKET=your-bucket-name
export STORAGE_PROJECT_ID=your-gcp-project-id
export GCS_CREDENTIALS_PATH=/path/to/service-account.json  # Optional
```

#### OneDrive Configuration

```bash
export STORAGE_PROVIDER=onedrive
export ONEDRIVE_CLIENT_ID=your-azure-app-client-id
export ONEDRIVE_CLIENT_SECRET=your-azure-app-client-secret
export ONEDRIVE_TENANT_ID=your-azure-tenant-id
export ONEDRIVE_FOLDER_PATH=/IceCharts  # Optional, default: /
```

#### Google Drive Configuration

```bash
export STORAGE_PROVIDER=googledrive
export GDRIVE_CREDENTIALS_PATH=/path/to/credentials.json
export GDRIVE_TOKEN_PATH=/path/to/token.json  # Optional, default: token.json
export GDRIVE_FOLDER_ID=your-folder-id  # Optional
```

### Programmatic Configuration

```python
from app.storage import get_storage_provider

# MinIO/S3 config
config = {
    'endpoint': 'minio.example.com:9000',
    'access_key': 'your-access-key',
    'secret_key': 'your-secret-key',
    'bucket': 'your-bucket',
    'secure': True
}
storage = get_storage_provider('minio', config)

# GCS config
config = {
    'bucket': 'your-bucket',
    'project_id': 'your-project-id',
    'credentials_path': '/path/to/service-account.json'
}
storage = get_storage_provider('gcs', config)

# OneDrive config
config = {
    'client_id': 'your-client-id',
    'client_secret': 'your-client-secret',
    'tenant_id': 'your-tenant-id',
    'folder_path': '/IceCharts'
}
storage = get_storage_provider('onedrive', config)

# Google Drive config
config = {
    'credentials_path': '/path/to/credentials.json',
    'token_path': '/path/to/token.json',
    'folder_id': 'your-folder-id'
}
storage = get_storage_provider('googledrive', config)
```

## API Reference

### StorageProvider Methods

All methods are async and must be awaited.

#### upload(key, data, content_type, metadata=None)

Upload data to storage.

**Parameters:**
- `key` (str): Unique identifier/path for the file
- `data` (bytes): Binary data to upload
- `content_type` (str): MIME type of the data
- `metadata` (dict, optional): Key-value pairs of metadata

**Returns:** str - The key of the uploaded file

**Raises:**
- `StorageError`: If upload fails
- `StorageAuthenticationError`: If authentication fails

#### download(key)

Download data from storage.

**Parameters:**
- `key` (str): Unique identifier/path for the file

**Returns:** bytes - Binary data of the file

**Raises:**
- `FileNotFoundError`: If file does not exist
- `StorageError`: If download fails

#### delete(key)

Delete a file from storage.

**Parameters:**
- `key` (str): Unique identifier/path for the file

**Returns:** bool - True if deletion was successful

**Raises:**
- `StorageError`: If deletion fails

#### get_url(key, expires_in=3600)

Generate a presigned/sharing URL for file access.

**Parameters:**
- `key` (str): Unique identifier/path for the file
- `expires_in` (int): URL expiration time in seconds (default: 3600)

**Returns:** str - Presigned/sharing URL

**Raises:**
- `FileNotFoundError`: If file does not exist
- `StorageError`: If URL generation fails

#### list_files(prefix=None)

List files in storage with optional prefix filter.

**Parameters:**
- `prefix` (str, optional): Prefix to filter files

**Returns:** List[StorageFile] - List of StorageFile objects

**Raises:**
- `StorageError`: If listing fails

#### copy(source_key, dest_key)

Copy a file within storage.

**Parameters:**
- `source_key` (str): Source file identifier/path
- `dest_key` (str): Destination file identifier/path

**Returns:** bool - True if copy was successful

**Raises:**
- `FileNotFoundError`: If source file does not exist
- `StorageError`: If copy fails

#### exists(key)

Check if a file exists in storage.

**Parameters:**
- `key` (str): Unique identifier/path for the file

**Returns:** bool - True if file exists

**Raises:**
- `StorageError`: If existence check fails

#### get_metadata(key)

Get metadata for a file without downloading it.

**Parameters:**
- `key` (str): Unique identifier/path for the file

**Returns:** StorageFile - Object with file metadata

**Raises:**
- `FileNotFoundError`: If file does not exist
- `StorageError`: If metadata retrieval fails

### StorageFile Dataclass

```python
@dataclass(slots=True, frozen=True)
class StorageFile:
    key: str                           # File key/path
    size: int                          # Size in bytes
    content_type: str                  # MIME type
    last_modified: datetime            # Last modification timestamp
    etag: Optional[str]               # Entity tag
    metadata: Optional[Dict[str, Any]] # Additional metadata
```

## Exception Hierarchy

```
StorageError (base exception)
├── StorageConfigError (configuration errors)
├── StorageConnectionError (connection errors)
└── StorageAuthenticationError (authentication errors)
```

## Examples

### Upload with Metadata

```python
async def upload_with_metadata():
    storage = get_storage_provider()

    data = b"Important data"
    metadata = {
        'uploaded_by': 'admin',
        'department': 'engineering',
        'classification': 'confidential'
    }

    key = await storage.upload(
        'docs/report.pdf',
        data,
        'application/pdf',
        metadata=metadata
    )
    print(f"Uploaded: {key}")
```

### Batch Download

```python
async def download_all_pdfs():
    storage = get_storage_provider()

    # List all PDF files
    files = await storage.list_files(prefix='docs/')
    pdf_files = [f for f in files if f.content_type == 'application/pdf']

    # Download each PDF
    for file in pdf_files:
        data = await storage.download(file.key)
        print(f"Downloaded {file.key}: {len(data)} bytes")
```

### Copy with Versioning

```python
async def create_backup():
    storage = get_storage_provider()

    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    source = 'config/app.yaml'
    backup = f'config/backups/app_{timestamp}.yaml'

    if await storage.copy(source, backup):
        print(f"Backup created: {backup}")
```

### Generate Temporary Access URLs

```python
async def share_file(key: str, expires_in: int = 3600):
    storage = get_storage_provider()

    # Generate URL that expires in 1 hour
    url = await storage.get_url(key, expires_in=expires_in)

    return {
        'url': url,
        'expires_in': expires_in,
        'expires_at': datetime.now() + timedelta(seconds=expires_in)
    }
```

## Testing

```python
import pytest
from app.storage import get_storage_provider

@pytest.mark.asyncio
async def test_upload_download():
    storage = get_storage_provider('minio', {
        'endpoint': 'localhost:9000',
        'access_key': 'minioadmin',
        'secret_key': 'minioadmin',
        'bucket': 'test-bucket',
        'secure': False
    })

    # Upload
    data = b"Test data"
    key = await storage.upload('test.txt', data, 'text/plain')
    assert key == 'test.txt'

    # Download
    downloaded = await storage.download('test.txt')
    assert downloaded == data

    # Cleanup
    await storage.delete('test.txt')
```

## Best Practices

1. **Use Environment Variables**: Keep credentials in environment variables, not code
2. **Handle Exceptions**: Always wrap storage operations in try-except blocks
3. **Async Operations**: Use async/await for better performance
4. **Resource Cleanup**: Delete temporary files when no longer needed
5. **Metadata**: Use metadata for searchability and organization
6. **Prefix Organization**: Use logical prefixes for file organization (e.g., `users/123/avatar.jpg`)
7. **Content Types**: Always specify correct MIME types
8. **URL Expiration**: Use short expiration times for security-sensitive URLs

## Performance Considerations

- All storage operations run blocking I/O in thread executors
- Use batch operations when possible (e.g., list_files instead of multiple exists calls)
- Consider caching frequently accessed files
- Use presigned URLs for direct client access when possible
- Monitor storage provider rate limits and quotas

## Security Considerations

- Never commit credentials to version control
- Use IAM roles/service accounts when possible
- Implement proper access controls at the storage provider level
- Validate file types and sizes before upload
- Use HTTPS/TLS for all storage connections
- Rotate access keys regularly
- Implement audit logging for sensitive operations

## License

Limited AGPL3 with preamble for fair use
Copyright (c) 2025 Penguin Tech Inc
