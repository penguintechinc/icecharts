"""Example usage of IceCharts storage abstraction layer.

This file demonstrates how to use the storage providers with various
operations including upload, download, listing, and URL generation.
"""

import asyncio
from typing import List
from datetime import datetime

from . import get_storage_provider, StorageFile, StorageError


async def example_basic_operations():
    """Demonstrate basic storage operations."""
    print("=== Basic Storage Operations ===\n")

    # Initialize storage provider from environment
    storage = get_storage_provider()

    # Upload a file
    print("1. Uploading file...")
    data = b"Hello from IceCharts storage!"
    key = await storage.upload(
        key='examples/hello.txt',
        data=data,
        content_type='text/plain',
        metadata={'author': 'system', 'version': '1.0'}
    )
    print(f"   Uploaded: {key}\n")

    # Check if file exists
    print("2. Checking file existence...")
    exists = await storage.exists('examples/hello.txt')
    print(f"   File exists: {exists}\n")

    # Get file metadata
    print("3. Getting file metadata...")
    metadata = await storage.get_metadata('examples/hello.txt')
    print(f"   Key: {metadata.key}")
    print(f"   Size: {metadata.size} bytes")
    print(f"   Content Type: {metadata.content_type}")
    print(f"   Last Modified: {metadata.last_modified}")
    print(f"   Metadata: {metadata.metadata}\n")

    # Download the file
    print("4. Downloading file...")
    downloaded = await storage.download('examples/hello.txt')
    print(f"   Downloaded {len(downloaded)} bytes")
    print(f"   Content: {downloaded.decode()}\n")

    # Generate presigned/sharing URL
    print("5. Generating access URL...")
    url = await storage.get_url('examples/hello.txt', expires_in=3600)
    print(f"   URL (expires in 1 hour): {url}\n")

    # Copy file
    print("6. Copying file...")
    success = await storage.copy(
        source_key='examples/hello.txt',
        dest_key='examples/hello_copy.txt'
    )
    print(f"   Copy successful: {success}\n")

    # List files
    print("7. Listing files with prefix 'examples/'...")
    files = await storage.list_files(prefix='examples/')
    for file in files:
        print(f"   - {file.key} ({file.size} bytes, {file.content_type})")
    print()

    # Clean up
    print("8. Cleaning up...")
    await storage.delete('examples/hello.txt')
    await storage.delete('examples/hello_copy.txt')
    print("   Files deleted\n")


async def example_batch_operations():
    """Demonstrate batch operations."""
    print("=== Batch Operations ===\n")

    storage = get_storage_provider()

    # Upload multiple files
    print("1. Uploading multiple files...")
    files_to_upload = [
        ('batch/file1.txt', b'Content 1', 'text/plain'),
        ('batch/file2.txt', b'Content 2', 'text/plain'),
        ('batch/file3.txt', b'Content 3', 'text/plain'),
    ]

    for key, data, content_type in files_to_upload:
        await storage.upload(key, data, content_type)
        print(f"   Uploaded: {key}")
    print()

    # List all uploaded files
    print("2. Listing all files in 'batch/' prefix...")
    files = await storage.list_files(prefix='batch/')
    print(f"   Found {len(files)} files\n")

    # Download all files
    print("3. Downloading all files...")
    for file in files:
        data = await storage.download(file.key)
        print(f"   Downloaded {file.key}: {data.decode()}")
    print()

    # Clean up all files
    print("4. Cleaning up all files...")
    for file in files:
        await storage.delete(file.key)
        print(f"   Deleted: {file.key}")
    print()


async def example_error_handling():
    """Demonstrate error handling."""
    print("=== Error Handling ===\n")

    storage = get_storage_provider()

    # Try to download non-existent file
    print("1. Attempting to download non-existent file...")
    try:
        await storage.download('does-not-exist.txt')
    except FileNotFoundError as e:
        print(f"   Caught expected error: {e}\n")

    # Try to copy non-existent file
    print("2. Attempting to copy non-existent file...")
    try:
        await storage.copy('source-missing.txt', 'destination.txt')
    except FileNotFoundError as e:
        print(f"   Caught expected error: {e}\n")

    # Try to get URL for non-existent file
    print("3. Attempting to get URL for non-existent file...")
    try:
        await storage.get_url('missing-file.txt')
    except FileNotFoundError as e:
        print(f"   Caught expected error: {e}\n")


async def example_with_metadata():
    """Demonstrate metadata usage."""
    print("=== Working with Metadata ===\n")

    storage = get_storage_provider()

    # Upload file with rich metadata
    print("1. Uploading file with metadata...")
    metadata = {
        'author': 'John Doe',
        'department': 'Engineering',
        'project': 'IceCharts',
        'classification': 'internal',
        'created_at': datetime.now().isoformat()
    }

    await storage.upload(
        key='documents/report.txt',
        data=b'Quarterly report content',
        content_type='text/plain',
        metadata=metadata
    )
    print("   File uploaded with metadata\n")

    # Retrieve and display metadata
    print("2. Retrieving file metadata...")
    file_info = await storage.get_metadata('documents/report.txt')
    print(f"   File: {file_info.key}")
    print(f"   Size: {file_info.size} bytes")
    print("   Metadata:")
    if file_info.metadata:
        for key, value in file_info.metadata.items():
            print(f"     - {key}: {value}")
    print()

    # Clean up
    print("3. Cleaning up...")
    await storage.delete('documents/report.txt')
    print("   File deleted\n")


async def example_organize_by_prefix():
    """Demonstrate file organization using prefixes."""
    print("=== File Organization with Prefixes ===\n")

    storage = get_storage_provider()

    # Upload files with organizational structure
    print("1. Creating organized file structure...")
    files = [
        'users/john/avatar.jpg',
        'users/john/documents/resume.pdf',
        'users/jane/avatar.jpg',
        'users/jane/documents/cv.pdf',
        'shared/templates/invoice.docx',
        'shared/templates/proposal.docx',
    ]

    for key in files:
        await storage.upload(key, b'dummy content', 'application/octet-stream')
        print(f"   Created: {key}")
    print()

    # List files by prefix
    print("2. Listing John's files...")
    johns_files = await storage.list_files(prefix='users/john/')
    for file in johns_files:
        print(f"   - {file.key}")
    print()

    print("3. Listing all user avatars...")
    # Note: This requires listing all users and filtering
    all_files = await storage.list_files(prefix='users/')
    avatars = [f for f in all_files if f.key.endswith('avatar.jpg')]
    for file in avatars:
        print(f"   - {file.key}")
    print()

    print("4. Listing shared templates...")
    templates = await storage.list_files(prefix='shared/templates/')
    for file in templates:
        print(f"   - {file.key}")
    print()

    # Clean up
    print("5. Cleaning up...")
    for key in files:
        await storage.delete(key)
    print("   All files deleted\n")


async def main():
    """Run all examples."""
    try:
        await example_basic_operations()
        await example_batch_operations()
        await example_error_handling()
        await example_with_metadata()
        await example_organize_by_prefix()

        print("=== All Examples Completed Successfully ===")

    except StorageError as e:
        print(f"\nStorage error occurred: {e}")
    except Exception as e:
        print(f"\nUnexpected error occurred: {e}")


if __name__ == '__main__':
    # Run all examples
    asyncio.run(main())
