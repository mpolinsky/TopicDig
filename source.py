# source.py provides an abstract dataclass for a data source
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import namedtuple
from typing import List, Optional

Summary = namedtuple('Summary',['source','cluster_list','link_ext','hed','dek','date','authors','original_length','summary_text','summary_length','chunk_time', 'query_time', 'mean_query_time', 'summary_time'])
Summary.__doc__ = f"""
                Summary: a namedtuple for storing Summaries and relevant metadata.
                
                • Source: A Source object for the source of the summarized document. 
                • cluster_list: A list of the NER entities detected in this article's hed (headline).
                • link_ext: The link extension of the article (on the base url, source's source_url)
                • hed, dek: headline and subheader. These are standard industry terms. 
                            Dek is None if not applicable.
                • date: Date of publication/update listed in article.
                • authors: list of authors, currently a string containing the byline.
                • original_length: length of the original article
                • cluster_num: Number of clusters the source article appears in
                • summary_text: List of summarized chunks.
                • summary_length: Length of summary text
                • stats for stats
                """

@dataclass
class Source(ABC):
    source_name: Optional[str] = ""
    source_url: Optional[str] = ""
    # Checkpoint str encourages use of source-appropriate models.
    source_summarization_checkpoint: Optional[str] = "" 
    source_ner_checkpoint: Optional[str] = ""

    """
    User must implement a source-dependent method
    to retrieve data used to create clusters.  

    This gets called when clustering is performed.
    """
    @abstractmethod
    def retrieve_cluster_data(self) -> List[namedtuple]:
        pass

    """
    User must implement a source-dependent method 
    to retrieve texts for summarization.

    This gets called once topics for digestion have been selected.  
    """
    @abstractmethod
    def retrieve_article(self) -> List[namedtuple]:
        pass
