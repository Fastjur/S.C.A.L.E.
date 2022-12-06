"""
This module contains utility functions for interacting with Amazon S3.

S3Error: An exception class for Amazon S3 errors.
S3Resource: A class for interacting with Amazon S3 resources.
It provides methods for uploading, downloading, and managing files on S3.
time_function: A decorator function for measuring the execution time of a
given function.
"""

from .s3_resource import S3Error, S3Resource, S3ResourceInterface
