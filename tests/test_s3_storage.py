from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile

from app.storage.s3 import S3Storage


# Helper to mock an UploadFile with custom content
def create_upload_file(
    filename: str = "document.txt",
    content: bytes = b"ArcaFS S3 test content",
    content_type: str = "text/plain",
) -> UploadFile:
    file_mock = Mock()
    file_mock.read.return_value = content
    file_mock.tell.return_value = len(content)

    upload_file = UploadFile(
        filename=filename,
        file=file_mock,
    )
    upload_file.headers = {
        "content-type": content_type,
    }
    return upload_file


# Test that saving a file uploads the object to the correct S3 key
@patch("app.storage.s3.boto3.client")
@patch("app.storage.s3.AWS_S3_BUCKET_NAME", "arcafs-test-bucket")
def test_s3_save_file_uploads_object(mock_boto_client):
    s3_client = Mock()
    mock_boto_client.return_value = s3_client

    upload_file = create_upload_file()
    storage = S3Storage()

    stored_filename, object_key, size = storage.save_file(
        upload_file=upload_file,
        user_id=1,
    )

    # Assert correct S3 key structure and file size
    assert stored_filename.endswith(".txt")
    assert object_key.startswith("users/1/files/")
    assert object_key.endswith(".txt")
    assert size == len(b"ArcaFS S3 test content")

    # Verify boto3 call arguments
    s3_client.upload_fileobj.assert_called_once()
    call_kwargs = s3_client.upload_fileobj.call_args.kwargs
    assert call_kwargs["Bucket"] == "arcafs-test-bucket"
    assert call_kwargs["Key"] == object_key
    assert call_kwargs["ExtraArgs"]["ContentType"] == "text/plain"


# Test that exists() returns False when S3 head_object returns a 404 ClientError
@patch("app.storage.s3.boto3.client")
@patch("app.storage.s3.AWS_S3_BUCKET_NAME", "arcafs-test-bucket")
def test_s3_exists_returns_false_when_object_does_not_exists(mock_boto_client):
    s3_client = Mock()
    mock_boto_client.return_value = s3_client

    # Simulate S3 404 Not Found error
    s3_client.head_object.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "404",
                "Message": "Not Found",
            }
        },
        operation_name="HeadObject",
    )

    storage = S3Storage()
    result = storage.exists("users/1/files/missing.txt")

    assert result is False


# Test that delete_file calls S3 delete_object with the correct bucket and key
@patch("app.storage.s3.boto3.client")
@patch("app.storage.s3.AWS_S3_BUCKET_NAME", "arcafs-test-bucket")
def test_s3_delete_file_deletes_object(mock_boto_client):
    s3_client = Mock()
    mock_boto_client.return_value = s3_client

    storage = S3Storage()
    storage.delete_file("users/1/files/file.txt")

    s3_client.delete_object.assert_called_once_with(
        Bucket="arcafs-test-bucket",
        Key="users/1/files/file.txt",
    )


# Test that copy_file retrieves metadata and issues a copy_object command
@patch("app.storage.s3.boto3.client")
@patch("app.storage.s3.AWS_S3_BUCKET_NAME", "arcafs-test-bucket")
def test_s3_copy_file_copies_object(mock_boto_client):
    s3_client = Mock()
    mock_boto_client.return_value = s3_client

    # Mock source object metadata
    s3_client.head_object.return_value = {
        "ContentLength": 123,
        "ContentType": "text/plain",
    }

    storage = S3Storage()
    stored_filename, destination_key, size = storage.copy_file(
        source_path=Path("users/1/files/source.txt"),
        user_id=1,
        original_filename="document.txt",
    )

    assert stored_filename.endswith(".txt")
    assert destination_key.startswith("users/1/files/")
    assert destination_key.endswith(".txt")
    assert size == 123

    # Verify S3 metadata fetch and copy parameters
    s3_client.head_object.assert_called_once_with(
        Bucket="arcafs-test-bucket",
        Key="users/1/files/source.txt",
    )
    s3_client.copy_object.assert_called_once()
    copy_kwargs = s3_client.copy_object.call_args.kwargs
    assert copy_kwargs["Bucket"] == "arcafs-test-bucket"
    assert copy_kwargs["CopySource"] == {
        "Bucket": "arcafs-test-bucket",
        "Key": "users/1/files/source.txt",
    }
    assert copy_kwargs["Key"] == destination_key
    assert copy_kwargs["ContentType"] == "text/plain"
    assert copy_kwargs["MetadataDirective"] == "REPLACE"


# Test that initializing S3Storage without a bucket name raises a 500 error
@patch("app.storage.s3.AWS_S3_BUCKET_NAME", None)
def test_s3_storage_requires_bucket_name():
    with pytest.raises(HTTPException) as exc_info:
        S3Storage()

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "AWS_S3_BUCKET_NAME is not configured."

# Test that AccessDenied on upload converts to a clear 500 error
@patch("app.storage.s3.boto3.client")
@patch("app.storage.s3.AWS_S3_BUCKET_NAME", "arcafs-test-bucket")
def test_s3_upload_access_denied_returns_clear_error(mock_boto_client):
    s3_client = Mock()
    mock_boto_client.return_value = s3_client

    s3_client.upload_fileobj.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied",
            }
        },
        operation_name="PutObject",
    )

    upload_file = create_upload_file()
    storage = S3Storage()

    with pytest.raises(HTTPException) as exc_info:
        storage.save_file(
            upload_file=upload_file,
            user_id=1,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Access denied to S3 bucket or object"


# Test that InvalidAccessKeyId on upload converts to a clear 500 error
@patch("app.storage.s3.boto3.client")
@patch("app.storage.s3.AWS_S3_BUCKET_NAME", "arcafs-test-bucket")
def test_s3_upload_invalid_access_key_returns_clear_error(mock_boto_client):
    s3_client = Mock()
    mock_boto_client.return_value = s3_client

    s3_client.upload_fileobj.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "InvalidAccessKeyId",
                "Message": "The AWS Access Key Id you provided does not exist",
            }
        },
        operation_name="PutObject",
    )

    upload_file = create_upload_file()
    storage = S3Storage()

    with pytest.raises(HTTPException) as exc_info:
        storage.save_file(
            upload_file=upload_file,
            user_id=1,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Invalid AWS access key"


# Test that AccessDenied on head_object propagates as a clear 500 error instead of hiding it
@patch("app.storage.s3.boto3.client")
@patch("app.storage.s3.AWS_S3_BUCKET_NAME", "arcafs-test-bucket")
def test_s3_exists_access_denied_raises_clear_error(mock_boto_client):
    s3_client = Mock()
    mock_boto_client.return_value = s3_client

    s3_client.head_object.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied",
            }
        },
        operation_name="HeadObject",
    )

    storage = S3Storage()

    with pytest.raises(HTTPException) as exc_info:
        storage.exists("users/1/files/file.txt")

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Access denied to S3 bucket or object"