import logging
import os
from abc import abstractmethod
from dataclasses import dataclass
from typing import List

import boto3
from botocore.exceptions import ClientError

from config import settings
from utils.time_function import time_function

logger = logging.getLogger(__name__)


class S3Error(Exception):
    def __init__(self, message):
        self.message = message


@dataclass(frozen=True)
class S3File:
    bucket_name: str
    key: str
    size: int


class S3ResourceInterface:
    @abstractmethod
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_access_key: str,
    ):
        raise NotImplementedError

    @abstractmethod
    def list_buckets(self):
        raise NotImplementedError

    @abstractmethod
    def create_bucket(self, bucket: str):
        raise NotImplementedError

    @abstractmethod
    def list_all_files(self, bucket: str) -> List[S3File]:
        raise NotImplementedError

    @abstractmethod
    def upload_fileobj(self, fileobj, bucket: str, key: str):
        raise NotImplementedError

    @abstractmethod
    def download_fileobj(self, fileobj, bucket: str, key: str):
        raise NotImplementedError

    @abstractmethod
    def move_file_between_buckets(
        self,
        source_bucket: str,
        destination_bucket: str,
        source_key: str,
        destination_key: str,
    ):
        raise NotImplementedError

    @abstractmethod
    def get_file_size(self, bucket: str, key: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete_all_files_in_bucket(self, bucket: str):
        raise NotImplementedError


class S3Resource(S3ResourceInterface):
    def __init__(
        self,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        access_key=os.environ.get("AWS_ACCESS_KEY_ID"),
        secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    ):
        self.resource = boto3.resource(
            "s3",
            region_name=settings.AWS_REGION_NAME,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_access_key,
            verify=False,
        )
        self.client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION_NAME,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_access_key,
            verify=False,
        )

    def list_buckets(self):
        try:
            return self.client.list_buckets()
        except ClientError as err:
            raise S3Error("List buckets failed") from err

    def create_bucket(self, bucket):
        try:
            self.client.create_bucket(Bucket=bucket)
        except ClientError as err:
            raise S3Error(f"Create bucket failed: {bucket}") from err

    def list_all_files(self, bucket):
        """
        return all the objects in one bucket
        :param bucket: the bucket name, string
        :return: the list of all the objects in that bucket, list
        """
        my_bucket = self.resource.Bucket(bucket)
        return my_bucket.objects.all()

    @time_function
    def upload_fileobj(self, fileobj, bucket, key):
        try:
            self.resource.Object(bucket, key).upload_fileobj(fileobj)
        except ClientError as err:
            raise S3Error(
                f"Upload file object failed into bucket: {bucket}, key: {key}"
            ) from err

    @time_function
    def download_fileobj(self, fileobj, bucket, key):
        logger.info("Downloading file from bucket: %s, key: %s", bucket, key)
        try:
            self.resource.Object(bucket, key).download_fileobj(fileobj)
        except ClientError as err:
            raise S3Error(
                f"Download file object failed from bucket: "
                f"{bucket}, key: {key}"
            ) from err

    @time_function
    def move_file_between_buckets(
        self,
        source_bucket: str,
        destination_bucket: str,
        source_key: str,
        destination_key: str,
    ):
        """
        Move one object from one bucket to the other.
        :param source_bucket: the source bucket name, string
        :param destination_bucket: the destination bucket name, string
        :param source_key: the source object key, string
        :param destination_key: the destination object key,
        """
        try:
            self.resource.Object(
                destination_bucket, destination_key
            ).copy_from(
                CopySource={"Bucket": source_bucket, "Key": source_key}
            )
            self.resource.Object(source_bucket, source_key).delete()
        except ClientError as err:
            raise S3Error(f"Cannot move file {source_key}") from err

    @time_function
    def copy_file_between_buckets(
        self,
        source_bucket: str,
        destination_bucket: str,
        source_key: str,
        destination_key: str,
    ):
        """
        Copy one object from one buckt to the other.
        :param source_bucket:
        :param destination_bucket:
        :param source_key:
        :param destination_key:
        :return:
        """
        try:
            self.resource.Object(
                destination_bucket, destination_key
            ).copy_from(
                CopySource={"Bucket": source_bucket, "Key": source_key}
            )
        except ClientError as err:
            raise S3Error(f"Cannot copy file {source_key}") from err

    @time_function
    def delete_file_in_bucket(self, bucket: str, key: str):
        """
        Delete one object from one bucket.
        :param bucket:
        :param key:
        :return:
        """
        try:
            self.resource.Object(bucket, key).delete()
        except ClientError as err:
            raise S3Error(f"Cannot delete file {key}") from err

    @time_function
    def get_file_size(self, bucket: str, key: str) -> int:
        obj = self.resource.Object(bucket, key)
        response = obj.get()
        return response["ContentLength"]

    def delete_all_files_in_bucket(self, bucket: str):
        """
        Delete all objects in one bucket.
        :param bucket:
        :return:
        """
        try:
            bucket = self.resource.Bucket(bucket)
            bucket.objects.all().delete()
        except ClientError as err:
            raise S3Error(
                f"Cannot delete all files in bucket {bucket}"
            ) from err
