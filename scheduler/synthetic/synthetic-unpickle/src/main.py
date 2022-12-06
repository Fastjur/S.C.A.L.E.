import gc
import io
import logging
import os
import signal

import gensim
import nltk
import pandas as pd
from nltk import word_tokenize, find
from nltk.corpus import words as nltk_corpus_words
from nltk.sentiment import SentimentIntensityAnalyzer

from utils import time_function, get_trcs_data, patch_trcs
from utils.FileStates import FileProcessStep
from utils.s3_utils import S3Resource

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s -- %(message)s",
)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("s3transfer").setLevel(logging.INFO)
logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


def _process_file(file, model, nltk_words, stopwords, sia):
    logger.info("Processing file: %s", file)
    # Mark file as processing
    patch_trcs(
        "files",
        file["id"],
        data={"process_step": FileProcessStep.PROCESSING.code},
    )

    s3_resource = S3Resource()
    with io.BytesIO() as file_obj:
        bucket = file["file_path"].split("/")[0]
        key = file["file_path"].split("/")[1]
        s3_resource.download_fileobj(file_obj, bucket, key)
        file_obj.seek(0)
        logger.info("Downloaded file: %s", key)

        logger.info("Reading pickle (may take a while)")
        df = pd.read_csv(file_obj, sep="\t")
        logger.debug(df.head())

        unmatched_words = []
        unmatched_words_errors = 0
        sia_errors = 0
        total_chats = 0

        for chat in df["body"]:
            try:
                total_chats += 1
                words = word_tokenize(chat)
                words = [
                    w.lower()
                    for w in words
                    if w.lower() not in stopwords and w.lower() in nltk_words
                ]
                if len(words) > 0:
                    try:
                        does_not_match = model.doesnt_match(words)
                        if does_not_match:
                            unmatched_words.append(does_not_match)
                    except Exception as err:
                        print(err)
                        unmatched_words_errors += 1
                try:
                    sia.polarity_scores(chat)
                except Exception as err:
                    print(err)
                    sia_errors += 1
            except Exception as err:
                print(err)

        # Delete dataframe to free up memory
        del df
        gc.collect()

    # Remove, just to save space during big tests TODO: remove for final
    s3_resource.delete_file_in_bucket(bucket, key)
    # Mark old file as finished
    patch_trcs(
        "files",
        file["id"],
        data={
            "process_step": FileProcessStep.FINISHED.code,
        },
    )


@time_function
def run_once():
    pod_identifier = os.environ.get("POD_IDENTIFIER")
    files = get_trcs_data(endpoint=f"unpickle/{pod_identifier}")["data"]

    if not files:
        logger.error(
            "No files found to process, this container should not be running"
        )
        return

    nltk.download("punkt")
    nltk.download("word2vec_sample")
    nltk.download("stopwords")
    nltk.download("words")
    nltk.download("vader_lexicon")

    word2vec_sample = str(find("models/word2vec_sample/pruned.word2vec.txt"))
    model = gensim.models.KeyedVectors.load_word2vec_format(
        word2vec_sample, binary=False
    )

    nltk_words = set(nltk_corpus_words.words())
    stopwords = nltk.corpus.stopwords.words("english")
    sia = SentimentIntensityAnalyzer()

    for file in files:
        _process_file(file, model, nltk_words, stopwords, sia)


def sigterm_handler(signo, _stack_frame):
    logger.info("Received signal to terminate: %s, exiting", signo)
    raise SystemExit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    run_once()
