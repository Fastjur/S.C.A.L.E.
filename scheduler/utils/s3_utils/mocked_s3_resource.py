from typing import List

from .s3_resource import S3ResourceInterface, S3File


class S3ResourceMocked(S3ResourceInterface):
    def __init__(
        self,
    ):
        self.mock_files = []

    def set_mocked_result_list_all_files(self, mock_files: List[S3File]):
        self.mock_files = mock_files

    def list_all_files(self, bucket: str) -> List[S3File]:
        return [file for file in self.mock_files if file.bucket_name == bucket]
