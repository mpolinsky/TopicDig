# digestor.py is an implementation of a digestor that creates news digests.
# the digestor manages the creation of summaries and assembles them into one digest...

import requests, json
from collections import namedtuple
from functools import lru_cache
from typing import List
from dataclasses import dataclass, field
from datetime import datetime as dt
import streamlit as st

from codetiming import Timer
from transformers import AutoTokenizer

from source import Source, Summary
from scrape_sources import stub as stb



@dataclass
class Digestor:
    timer: Timer
    cache: bool = True
    text: str = field(default="no_digest")
    stubs: List = field(default_factory=list)
    # For clarity.
    # Each stub/summary has its entities. 
    user_choices: List =field(default_factory=list)
    # The digest text
    summaries: List = field(default_factory=list)
    #sources:List = field(default_factory=list) # I'm thinking create a string list for easy ref
    # text:str = None

    digest_meta:namedtuple(
        "digestMeta", 
        [
            'digest_time',
            'number_articles',
            'digest_length', 
            'articles_per_cluster'
        ])  = None

    # Summarization params:
    token_limit: int = 512
    word_limit: int = 400
    SUMMARIZATION_PARAMETERS = {
                                "do_sample": False,
                                "use_cache": cache 
                                } 

    # Inference parameters
    API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
    headers = {"Authorization": f"""Bearer {st.secrets['ato']}"""}
    
    # I would like to keep the whole scraped text separate if I can,
    # which I'm not doing here
    # After this runs, the digestor is populated with s
    
    # relevance is a matter of how many chosen clusters this article belongs to.
    # max relevance is the number of unique chosen entities.  min is 1.
    # Allows placing articles that hit more chosen topics to go higher up,
    # mirroring "upside down pyramid" journalism convention, i.e. ordering facts by decreasing information content.
    def relevance(self, summary):
        return len(set(self.user_choices) & set(summary.cluster_list))

    def digest(self):
        """Retrieves all data for user-chosen articles, builds summary object list"""
        # Clear timer from previous digestion
        self.timer.timers.clear()
        # Start digest timer
        with Timer(name=f"digest_time", text="Total digest time: {seconds:.4f} seconds"):
            # Loop through stubs, collecting data and instantiating 
            # and collecting Summary objects.
            for stub in self.stubs:
                # Check to see if we already have access to this summary:
                if not isinstance(stub, stb):
                    self.summaries.append(stub)
                else:
                    # if not:
                    summary_data: List
                    # Get full article data 
                    text, summary_data = stub.source.retrieve_article(stub)
                    # Drop problem scrapes
                    # Log here
                    if text != None and summary_data != None:
                        # Start chunk timer
                        with Timer(name=f"{stub.hed}_chunk_time", logger=None):
                            chunk_list = self.chunk_piece(text, self.word_limit, stub.source.source_summarization_checkpoint)
                        # start totoal summarization timer.  Summarization queries are timed in 'perform_summarzation()'
                        with Timer(name=f"{stub.hed}_summary_time", text="Whole article summarization time: {:.4f} seconds"):
                            summary = self.perform_summarization(
                                stub.hed,
                                chunk_list, 
                                self.API_URL, 
                                self.headers,
                                cache = self.cache,
                                )
                        # return these things and instantiate a Summary object with them, 
                        # add that summary object to a list or somesuch collection.
                        # There is also timer data and data on articles

                        self.summaries.append(
                            Summary(
                                source=summary_data[0], 
                                cluster_list=summary_data[1],
                                link_ext=summary_data[2], 
                                hed=summary_data[3], 
                                dek=summary_data[4], 
                                date=summary_data[5], 
                                authors=summary_data[6], 
                                original_length = summary_data[7], 
                                summary_text=summary, 
                                summary_length=len(' '.join(summary).split(' ')),
                                chunk_time=self.timer.timers[f'{stub.hed}_chunk_time'],
                                query_time=self.timer.timers[f"{stub.hed}_query_time"],
                                mean_query_time=self.timer.timers.mean(f'{stub.hed}_query_time'),
                                summary_time=self.timer.timers[f'{stub.hed}_summary_time'],
                                
                                )
                                   )
                    else:
                        print("Null article")    # looog this.  


            # When finished, order the summaries based on the number of user-selected clusters each article appears in.
            self.summaries.sort(key=self.relevance, reverse=True)

    # Query the HuggingFace Inference engine.  
    def query(self, payload, API_URL, headers):
        """Performs summarization inference API call."""
        data = json.dumps(payload)
        response = requests.request("POST", API_URL, headers=headers, data=data)
        return json.loads(response.content.decode("utf-8"))


    def chunk_piece(self, piece, limit, tokenizer_checkpoint, include_tail=False):
        """Breaks articles into chunks that will fit the desired token length limit"""        
        # Get approximate word count
        words = len(piece.split(' ')) # rough estimate of words.  # words <= number tokens generally.
        # get number of chunks by idividing number of words by chunk size (word limit) 
        # Create list of ints to create rangelist from
        base_range = [i*limit for i in range(words//limit+1)]
        # For articles less than limit in length base_range will only contain zero.
        # For most articles there is a small final chunk less than the limit.  
        # It may make summaries less coherent.
        if include_tail or base_range == [0]: 
            base_range.append(base_range[-1]+words%limit) # add odd part at end of text...maybe remove.
        # list of int ranges 
        range_list = [i for i in zip(base_range,base_range[1:])]
        

        # Setup for chunking/checking tokenized chunk length
        fractured = piece.split(' ')
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_checkpoint)
        chunk_list = []
    
        # Finally, chunk the piece, adjusting the chunks if too long.
        for i, j in range_list:
            if (tokenized_len := len(tokenizer(chunk := ' '.join(fractured[i:j]).replace('\n',' ')))) <= self.token_limit:
                chunk_list.append(chunk)
            else: # if chunks of <limit> words are too long, back them off.
                chunk_list.append(' '.join(chunk.split(' ')[: self.token_limit - tokenized_len ]).replace('\n',' '))
        
        return chunk_list



    # Returns list of summarized chunks instead of concatenating them which loses info about the process.
    def perform_summarization(self, stubhead, chunklist : List[str], API_URL: str, headers: None, cache=True) -> List[str]:
        """For each in chunk_list, appends result of query(chunk) to list collection_bin."""
        collection_bin = []
        repeat = 0
        # loop list and pass each chunk to the summarization API, storing results.
        # API CALLS: consider placing the code from query() into here. * * * *
        for chunk in chunklist:
            safe = False
            summarized_chunk = None
            with Timer(name=f"{stubhead}_query_time", logger=None):
                while not safe and repeat < 4:
                    try: # make these digest params. 
                        summarized_chunk =  self.query(
                            { 
                                "inputs": str(chunk), 
                                "parameters": self.SUMMARIZATION_PARAMETERS
                            },
                        API_URL, 
                        headers,
                        )[0]['summary_text']
                        safe = True
                    except Exception as e:
                        print("Summarization error, repeating...")
                        print(e)
                        repeat+=1
            if summarized_chunk is not None:
                collection_bin.append(summarized_chunk) 
        return collection_bin 
    


    # Order for display, arrange links?
    def build_digest(self) -> str:
        """Called to show the digest.  Also creates data dict for digest and summaries."""
        # builds summaries from pieces in each object
        # orders summaries according to cluster count
        # above done below not
        # Manages data to be presented along with digest.
        # returns all as data to display method either here or in main.
        digest = []
        for each in self.summaries:
            digest.append(' '.join(each.summary_text))
            
        digest_str = '\n'.join(digest)
        
        self.text = digest_str
