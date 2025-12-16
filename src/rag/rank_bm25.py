#!/usr/bin/env python

import math
import numpy as np
from multiprocessing import Pool, cpu_count

"""
All of these algorithms have been taken from the paper:
Trotmam et al, Improvements to BM25 and Language Models Examined

Here we implement all the BM25 variations mentioned. 
"""


class BM25:
    def __init__(self, corpus, tokenizer=None):
        self.corpus_size = 0
        self.avgdl = 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self.tokenizer = tokenizer

        if tokenizer:
            corpus = self._tokenize_corpus(corpus)

        nd = self._initialize(corpus)
        self._calc_idf(nd)

    def _initialize(self, corpus):
        """
        The main goal of this function is to calculate: 
        create doc_freqs, doc_len, corpus_size and avgdl
        1. doc_freqs: list of dictionaries, each dictionary contains {word: freq} for a document
        2. doc_len: list of document lengths
        3. corpus_size: number of documents in corpus
        4. avgdl: average document length in corpus
        5. nd: dictionary {word: number of documents containing word}
        :param corpus: list of documents, each document is a list of words
        :return: nd: dictionary {word: number of documents containing word}
        """

        nd = {}  # word -> number of documents with word
        # nd will contain {word: num of documents containing word}
        num_doc = 0
        for document in corpus:
            self.doc_len.append(len(document))
            num_doc += len(document)

            frequencies = {}
            # Calculate every frequencies for the words of current document
            for word in document:
                if word not in frequencies:
                    frequencies[word] = 0
                frequencies[word] += 1
            self.doc_freqs.append(frequencies)
            #frequencies contain {word: freq} for current document

            for word, freq in frequencies.items():
                # Update the number of documents containing word
                try:
                    nd[word]+=1
                except KeyError:
                    nd[word] = 1

            self.corpus_size += 1

        self.avgdl = num_doc / self.corpus_size
        return nd

    def _tokenize_corpus(self, corpus):
        pool = Pool(cpu_count())

        """
        results= pool.map(funct, iterable) is equivalent to: results = [funct(x) for x in iterable]
        Here, we use it to tokenize each document in the corpus in parallel.
        If cpu_count() is 4, and corpus has 8 documents, pool.map will distribute the tokenization
        of these 8 documents across 4 processes, each handling 2 documents.
        """
        tokenized_corpus = pool.map(self.tokenizer, corpus)
        return tokenized_corpus

    def _calc_idf(self, nd):
        """
        If the child class does not implement this method, raise error and if implemented, override this method
        So why this method here?
        This is because _calc_idf is called in the __init__ method of the parent class.
        As soon as an object is created _calc_idf is called.
        """
        raise NotImplementedError()

    def get_scores(self, query):
        raise NotImplementedError()

    def get_batch_scores(self, query, doc_ids):
        raise NotImplementedError()

    def get_top_n(self, query, documents, n=5):

        assert self.corpus_size == len(documents), "The documents given don't match the index corpus!"

        scores = self.get_scores(query)
        top_n = np.argsort(scores)[::-1][:n]
        return [documents[i] for i in top_n]
    
    def add_documents(self, new_documents):

        """
        28/11/2025
        Add new documents to the existing corpus and recompute idf values.
        This method will update all the internal states of the BM25 model to include the new documents.
        :param new_documents: list of new documents, each document is a list of words
        :return: None

        So now we no need to recreate the BM25 object from scratch when new documents are added.
        In this method, the required variables are: corpus_size, avgdl, doc_freqs, idf, doc_len
        """
        # Step 1: Tokenize if needed
        if self.tokenizer:
            with Pool(cpu_count()) as pool:
                new_documents = pool.map(self.tokenizer, new_documents)

        # Step 2: Update internal structures and collect new nd values
        new_nd = {}  # track how many new documents contain each word
        new_total_tokens = 0

        for document in new_documents:
            self.doc_len.append(len(document))
            new_total_tokens += len(document)

            frequencies = {}
            for word in document:
                frequencies[word] = frequencies.get(word, 0) + 1

            self.doc_freqs.append(frequencies)

            # update new_nd
            for word in frequencies:
                new_nd[word] = new_nd.get(word, 0) + 1

            self.corpus_size += 1

        # Step 3: Update avgdl
        previous_total_tokens = self.avgdl * (self.corpus_size - len(new_documents))
        new_total_docs = self.corpus_size
        updated_total_tokens = previous_total_tokens + new_total_tokens
        self.avgdl = updated_total_tokens / new_total_docs

        # Step 4: Merge old nd with new_nd
        merged_nd = {}
        # rebuild nd from scratch to avoid drift
        for doc in self.doc_freqs:
            for word in doc.keys():
                merged_nd[word] = merged_nd.get(word, 0) + 1

        # Step 5: Recalculate IDF using subclass method
        self._calc_idf(merged_nd)



class BM25Okapi(BM25):
    def __init__(self, corpus, tokenizer=None, k1=1.5, b=0.75, epsilon=0.25):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        super().__init__(corpus, tokenizer)

    def _calc_idf(self, nd):
        """
        This is the implementation of attire BM25 variant
        This is the child class implementation of the parent class method
        This overrides the NotImplementedError in the parent class
        This will instantly be called when an object of this class is created
        REMEMBER: IT WILL BE CALLED FROM THE CONSTRUCTOR OF THE PARENT CLASS
        """


        """
        Calculates frequencies of terms in documents and in corpus.
        This algorithm sets a floor on the idf values to eps * average_idf
        """
        # collect idf sum to calculate an average idf for epsilon value
        idf_sum = 0
        # collect words with negative idf to set them a special epsilon value.
        # idf can be negative if word is contained in more than half of documents
        negative_idfs = []
        """
        nd is collected from parent class _initialize method
        nd contains {word: number of documents containing word}
        """
        for word, freq in nd.items():
            idf = math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)
            self.idf[word] = idf
            idf_sum += idf
            if idf < 0:
                negative_idfs.append(word)
        self.average_idf = idf_sum / len(self.idf)

        eps = self.epsilon * self.average_idf
        for word in negative_idfs:
            self.idf[word] = eps

    def get_scores(self, query):
        """
        The ATIRE BM25 variant uses an idf function which uses a log(idf) score. To prevent negative idf scores,
        this algorithm also adds a floor to the idf value of epsilon.
        See [Trotman, A., X. Jia, M. Crane, Towards an Efficient and Effective Search Engine] for more info
        :param query:
        :return:
        """
        score = np.zeros(self.corpus_size)
        doc_len = np.array(self.doc_len)
        for q in query:
            q_freq = np.array([(doc.get(q) or 0) for doc in self.doc_freqs])
            score += (self.idf.get(q) or 0) * (q_freq * (self.k1 + 1) /
                                               (q_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
        return score

    def get_batch_scores(self, query, doc_ids):
        """
        Calculate bm25 scores between query and subset of all docs
        """
        assert all(di < len(self.doc_freqs) for di in doc_ids)
        score = np.zeros(len(doc_ids))
        doc_len = np.array(self.doc_len)[doc_ids]
        for q in query:
            q_freq = np.array([(self.doc_freqs[di].get(q) or 0) for di in doc_ids])
            score += (self.idf.get(q) or 0) * (q_freq * (self.k1 + 1) /
                                               (q_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
        return score.tolist()
    

    def return_variables(self):
        """
        28/11/2025
        Return the internal state variables of the BM25 model.
        This can be used to store the state externally if needed.
        :return: dict containing internal state variables
        """
        return {
            'corpus_size': self.corpus_size,
            'avgdl': self.avgdl,
            'doc_freqs': self.doc_freqs,
            'idf': self.idf,
            'doc_len': self.doc_len,
            'average_idf': self.average_idf,
            'k1': self.k1,
            'b': self.b,
            'epsilon': self.epsilon
        }


class BM25Okapi_without_corpus(BM25):
    """
    29/11/2025
    This class allows to create a BM25Okapi object without providing the original corpus.
    Instead, it takes the internal state variables directly as parameters.
    This is useful when you want to reconstruct a BM25 model from stored state variables,
    without needing to have access to the original corpus used to create the model.
    After fetching the stored variables from mongodb , you can create the BM25Okapi object
    29/11/2025
    """

    def __init__(self, corpus_size, avgdl, doc_freqs, idf, doc_len, average_idf,tokenizer=None, k1=1.5, b=0.75, epsilon=0.25):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon

        # Directly set the internal state variables
        self.corpus_size = corpus_size
        self.avgdl = avgdl
        self.doc_freqs = doc_freqs
        self.idf = idf
        self.doc_len = doc_len
        self.tokenizer = tokenizer
        self.average_idf = average_idf
        print(f"doc_len length: {len(self.doc_len)} type: {type(self.doc_len)} and doc_len: {self.doc_len}")


    def _calc_idf(self, nd):
        """
        This is the implementation of attire BM25 variant
        This is the child class implementation of the parent class method
        This overrides the NotImplementedError in the parent class
        This will instantly be called when an object of this class is created
        REMEMBER: IT WILL BE CALLED FROM THE CONSTRUCTOR OF THE PARENT CLASS
        """


        """
        Calculates frequencies of terms in documents and in corpus.
        This algorithm sets a floor on the idf values to eps * average_idf
        """
        # collect idf sum to calculate an average idf for epsilon value
        idf_sum = 0
        # collect words with negative idf to set them a special epsilon value.
        # idf can be negative if word is contained in more than half of documents
        negative_idfs = []
        """
        nd is collected from parent class _initialize method
        nd contains {word: number of documents containing word}
        """
        for word, freq in nd.items():
            idf = math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)
            self.idf[word] = idf
            idf_sum += idf
            if idf < 0:
                negative_idfs.append(word)
        self.average_idf = idf_sum / len(self.idf)

        eps = self.epsilon * self.average_idf
        for word in negative_idfs:
            self.idf[word] = eps

    def get_scores(self, query):
        """
        The ATIRE BM25 variant uses an idf function which uses a log(idf) score. To prevent negative idf scores,
        this algorithm also adds a floor to the idf value of epsilon.
        See [Trotman, A., X. Jia, M. Crane, Towards an Efficient and Effective Search Engine] for more info
        :param query:
        :return:
        """
        score = np.zeros(self.corpus_size)
        doc_len = np.array(self.doc_len)
        for q in query:
            q_freq = np.array([(doc.get(q) or 0) for doc in self.doc_freqs])
            score += (self.idf.get(q) or 0) * (q_freq * (self.k1 + 1) /
                                               (q_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
        return score

    def get_batch_scores(self, query, doc_ids):
        """
        Calculate bm25 scores between query and subset of all docs
        """
        assert all(di < len(self.doc_freqs) for di in doc_ids)
        score = np.zeros(len(doc_ids))
        doc_len = np.array(self.doc_len)[doc_ids]
        for q in query:
            q_freq = np.array([(self.doc_freqs[di].get(q) or 0) for di in doc_ids])
            score += (self.idf.get(q) or 0) * (q_freq * (self.k1 + 1) /
                                               (q_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
        return score.tolist()
    

    def return_variables(self):
        """
        28/11/2025
        Return the internal state variables of the BM25 model.
        This can be used to store the state externally if needed.
        :return: dict containing internal state variables
        """
        return {
            'corpus_size': self.corpus_size,
            'avgdl': self.avgdl,
            'doc_freqs': self.doc_freqs,
            'idf': self.idf,
            'doc_len': self.doc_len,
            'average_idf': self.average_idf,
            'k1': self.k1,
            'b': self.b,
            'epsilon': self.epsilon
        }


class BM25L(BM25):
    def __init__(self, corpus, tokenizer=None, k1=1.5, b=0.75, delta=0.5):
        # Algorithm specific parameters
        self.k1 = k1
        self.b = b
        self.delta = delta
        super().__init__(corpus, tokenizer)

    def _calc_idf(self, nd):
        for word, freq in nd.items():
            idf = math.log(self.corpus_size + 1) - math.log(freq + 0.5)
            self.idf[word] = idf

    def get_scores(self, query):
        score = np.zeros(self.corpus_size)
        doc_len = np.array(self.doc_len)
        for q in query:
            q_freq = np.array([(doc.get(q) or 0) for doc in self.doc_freqs])
            ctd = q_freq / (1 - self.b + self.b * doc_len / self.avgdl)
            score += (self.idf.get(q) or 0) * q_freq * (self.k1 + 1) * (ctd + self.delta) / \
                     (self.k1 + ctd + self.delta)
        return score

    def get_batch_scores(self, query, doc_ids):
        """
        Calculate bm25 scores between query and subset of all docs
        """
        assert all(di < len(self.doc_freqs) for di in doc_ids)
        score = np.zeros(len(doc_ids))
        doc_len = np.array(self.doc_len)[doc_ids]
        for q in query:
            q_freq = np.array([(self.doc_freqs[di].get(q) or 0) for di in doc_ids])
            ctd = q_freq / (1 - self.b + self.b * doc_len / self.avgdl)
            score += (self.idf.get(q) or 0) * q_freq * (self.k1 + 1) * (ctd + self.delta) / \
                     (self.k1 + ctd + self.delta)
        return score.tolist()


class BM25Plus(BM25):
    def __init__(self, corpus, tokenizer=None, k1=1.5, b=0.75, delta=1):
        # Algorithm specific parameters
        self.k1 = k1
        self.b = b
        self.delta = delta
        super().__init__(corpus, tokenizer)

    def _calc_idf(self, nd):
        for word, freq in nd.items():
            idf = math.log((self.corpus_size + 1) / freq)
            self.idf[word] = idf

    def get_scores(self, query):
        score = np.zeros(self.corpus_size)
        doc_len = np.array(self.doc_len)
        for q in query:
            q_freq = np.array([(doc.get(q) or 0) for doc in self.doc_freqs])
            score += (self.idf.get(q) or 0) * (self.delta + (q_freq * (self.k1 + 1)) /
                                               (self.k1 * (1 - self.b + self.b * doc_len / self.avgdl) + q_freq))
        return score

    def get_batch_scores(self, query, doc_ids):
        """
        Calculate bm25 scores between query and subset of all docs
        """
        assert all(di < len(self.doc_freqs) for di in doc_ids)
        score = np.zeros(len(doc_ids))
        doc_len = np.array(self.doc_len)[doc_ids]
        for q in query:
            q_freq = np.array([(self.doc_freqs[di].get(q) or 0) for di in doc_ids])
            score += (self.idf.get(q) or 0) * (self.delta + (q_freq * (self.k1 + 1)) /
                                               (self.k1 * (1 - self.b + self.b * doc_len / self.avgdl) + q_freq))
        return score.tolist()


# BM25Adpt and BM25T are a bit more complicated than the previous algorithms here. Here a term-specific k1
# parameter is calculated before scoring is done

# class BM25Adpt(BM25):
#     def __init__(self, corpus, k1=1.5, b=0.75, delta=1):
#         # Algorithm specific parameters
#         self.k1 = k1
#         self.b = b
#         self.delta = delta
#         super().__init__(corpus)
#
#     def _calc_idf(self, nd):
#         for word, freq in nd.items():
#             idf = math.log((self.corpus_size + 1) / freq)
#             self.idf[word] = idf
#
#     def get_scores(self, query):
#         score = np.zeros(self.corpus_size)
#         doc_len = np.array(self.doc_len)
#         for q in query:
#             q_freq = np.array([(doc.get(q) or 0) for doc in self.doc_freqs])
#             score += (self.idf.get(q) or 0) * (self.delta + (q_freq * (self.k1 + 1)) /
#                                                (self.k1 * (1 - self.b + self.b * doc_len / self.avgdl) + q_freq))
#         return score
#
#
# class BM25T(BM25):
#     def __init__(self, corpus, k1=1.5, b=0.75, delta=1):
#         # Algorithm specific parameters
#         self.k1 = k1
#         self.b = b
#         self.delta = delta
#         super().__init__(corpus)
#
#     def _calc_idf(self, nd):
#         for word, freq in nd.items():
#             idf = math.log((self.corpus_size + 1) / freq)
#             self.idf[word] = idf
#
#     def get_scores(self, query):
#         score = np.zeros(self.corpus_size)
#         doc_len = np.array(self.doc_len)
#         for q in query:
#             q_freq = np.array([(doc.get(q) or 0) for doc in self.doc_freqs])
#             score += (self.idf.get(q) or 0) * (self.delta + (q_freq * (self.k1 + 1)) /
#                                                (self.k1 * (1 - self.b + self.b * doc_len / self.avgdl) + q_freq))
#         return score
