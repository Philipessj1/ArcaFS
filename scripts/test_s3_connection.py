from pathlib import Path

from app.storage.s3 import S3Storage


def main() -> None:
    storage = S3Storage()

    test_file = Path("scripts/s3-test-file.txt")
    test_file.write_text("ArcaFS S3 connection test", encoding="utf-8")

    object_key = "tests/s3-test-file.txt"

    with test_file.open("rb") as file_obj:
        storage.s3_client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=storage.bucket_name,
            Key=object_key,
            ExtraArgs={"ContentType": "text/plain"},
        )

    exists = storage.exists(object_key)

    if not exists:
        raise RuntimeError("S3 object was uploaded but could not be found")

    storage.delete_file(object_key)

    test_file.unlink()

    print("S3 connection test passed")


if __name__ == "__main__":
    main()