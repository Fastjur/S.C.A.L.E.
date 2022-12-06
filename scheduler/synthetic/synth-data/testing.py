import os

import enlighten
import gensim
import nltk
import pandas as pd
from arrow import now
from nltk import word_tokenize, find
from nltk.corpus import words as nltk_corpus_words
from nltk.sentiment import SentimentIntensityAnalyzer

nltk.download("punkt")
nltk.download("word2vec_sample")
nltk.download("stopwords")
nltk.download("vader_lexicon")
nltk.download("words")

word2vec_sample = str(find("models/word2vec_sample/pruned.word2vec.txt"))
model = gensim.models.KeyedVectors.load_word2vec_format(
    word2vec_sample, binary=False
)

stopwords = nltk.corpus.stopwords.words("english")

sia = SentimentIntensityAnalyzer()

nltk_words = set(nltk_corpus_words.words())

with enlighten.get_manager() as manager:
    start_time = now()

    DATA_DIR = "BY_DAY_CHUNKED/2018-06-11"
    # DATA_DIR = "BY_DAY_CHUNKED/2018-03-01"

    tsv_files = [
        file for file in os.listdir(DATA_DIR) if file.endswith(".tsv")
    ]
    files_pbar = manager.counter(
        total=len(tsv_files),
        unit="files",
    )

    unmatched_words = []
    unmatched_words_errors = 0
    sia_errors = 0
    total_chats = 0

    for file in tsv_files:
        try:
            df = pd.read_csv(os.path.join(DATA_DIR, file), sep="\t")
            for chat in df["body"]:
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
                    except Exception as err:
                        print(err)
                        unmatched_words_errors += 1
                    if does_not_match:
                        unmatched_words.append(does_not_match)
                try:
                    sia.polarity_scores(chat)
                except Exception as err:
                    print(err)
                    sia_errors += 1

        except Exception as err:
            print(err)
        finally:
            files_pbar.update()

    print(unmatched_words)
    print(
        f"Unmatched word errors: {unmatched_words_errors}, "
        f"{round(unmatched_words_errors / total_chats * 100)}%"
    )
    print(f"SIA errors: {sia_errors}")

    end_time = now()

    print(f"Time taken: {end_time - start_time}")
