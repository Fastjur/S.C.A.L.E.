from enum import Enum


class ChoicesEnum(Enum):
    def __init__(self, code, description):
        self._code = code
        self._description = description

    @property
    def code(self):
        return self._code

    @property
    def description(self):
        return self._description

    @classmethod
    def choices(cls):
        return [(member.code, member.description) for member in cls]

    @classmethod
    def from_code(cls, code):
        for member in cls:
            if member.code == code:
                return member
        return None


class PipelineProcessor(ChoicesEnum):
    SYNTHETIC_GFC = ("synthetic-gfc", "Synthetic GFC")
    SYNTHETIC_UNZIP = ("synthetic-unzip", "Synthetic UNZIP")
    SYNTHETIC_UNPICKLE = ("synthetic-unpickle", "Synthetic UNPICKLE")


class FileProcessStep(ChoicesEnum):
    NEW = ("new", "new file")
    SCHEDULED = ("scheduled", "scheduled for processing")
    PROCESSING = ("processing", "check the file state for the progress")
    FINISHED = ("finished", "finished processing")


class FileStateCode(ChoicesEnum):
    PENDING = ("0100", "File pending")
    DOWNLOADED = ("0201", "File downloaded")
    UNZIPPED = ("0202", "File unzipped")
    UNPICKLED = ("0203", "File unpickled")
    UNKNOWN = ("unkn", "Unknown")
    ERROR = ("err", "Error")

    def get_accompanying_pipeline_processor(
        self,
    ) -> PipelineProcessor:
        """
        Returns the pipeline processing step that is required to process a file
        that has the given state.
        E.g.: If the file is in the PENDING state, the synthetic-gfc processor
        needs to process the file.
        :return: The pipeline processor that needs to process the file
        """
        if self == FileStateCode.PENDING:
            return PipelineProcessor.SYNTHETIC_GFC
        if self == FileStateCode.DOWNLOADED:
            return PipelineProcessor.SYNTHETIC_UNZIP
        if self == FileStateCode.UNZIPPED:
            return PipelineProcessor.SYNTHETIC_UNPICKLE
        raise ValueError(
            f"No processor found for file state: {self}",
        )
