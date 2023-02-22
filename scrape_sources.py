# nprSource.py is an implementation of the abstract Source object.
from dataclasses import dataclass
from collections import namedtuple
from typing import List, Tuple, Any
from gazpacho import Soup, get
from source import Source, Summary
import streamlit as st

stub = namedtuple('npr_stub',[ 'link','hed','entities', 'source'])
stub.__doc__ = f"""
        • A namedtuple to represent an unscraped news article.

        • link is the extension of the article.  Added to the source's source_url
                it is used to retrieve the full article and data.
        • hed is the headline ('hed' is journalism jargon, as is 'dek' for 'subheader')
        • entities is the list of entity names discovered in this headline,
                each entity representing one cluster the article is in.
        • source is a reference to the Source object that created the stub.
        """


@dataclass
class NPRLite(Source):
    """Implementation of abstract Source class that retrieves via webscraping at <removed>"""
    # Creates the initial namedtuple that holds the hed, link,
    # and identified entities for each article.
    # Chosen articles will have their data stored in a Summary object.
    def retrieve_cluster_data(self, limit=None) -> List[namedtuple]:
        print("retrieving NPR article stub")
        """Creates article stubs for articles listed on text.npr.org"""
        # Scrape NPR for headlines and links
        soup = Soup(get(self.source_url))
        # extract each headline
        npr_hed = [i.text for i in soup.find('div', {'class': 'topic-container'}).find('ul').find('a')]
        #npr_hed = [i for i in npr_hed if 'Opinion:' not in i] 
        # links scraped are just the extension to the site's base link.
        npr_links = [i.attrs['href'] for i in soup.find('div', {'class': 'topic-container'}).find('ul').find('a')]
        # limit amount of data being returned for clustering 
        if limit is not None:
            npr_hed = npr_hed[:limit]
            npr_links = npr_links[:limit]
        # Create stubs with heds and links
        # Test: do the headlines and links zipped together lineup correctly?
        article_tuples = [stub(i[0], i[1], [], self) for i in zip(npr_links, npr_hed)]
        print(f"Number of npr articles: {len(npr_hed)}")
        return article_tuples, len(npr_hed)

    # Returns None if article is only 1 line.
    def retrieve_article(self, indata: stub) -> Tuple[str, List[Tuple[str, Any]]]:
        """Retrieves article data from <rmvd> subhead if exists, date, author(s), and whole text"""
        st.write(f"""Retrieving article from:\n\t{self.source_url[:-5] + indata.link}\n""")
        container = Soup(get(self.source_url[:-5] + indata.link))
        text_container = container.find('div', {'class': "paragraphs-container"}).find('p')
        if isinstance(text_container, Soup):
            return None, None
        whole_text = ''.join([art.strip() for art in text_container])
        story_head = container.find('div', {'class':'story-head'})
        auth_and_date = [i.text for i in story_head.find('p')]
        author = auth_and_date[0]
        story_date = auth_and_date[1]
        author = author[3:]
        
        # return whole text and data for summary
        return whole_text, [
            self,
            indata.entities,
            indata.link,
            indata.hed,
            None,
            story_date,
            [author],
            len(whole_text.split(' ')),
        ]
     

@dataclass
class CNNText(Source):
    """Implementation of abstract Source class that retrieves via webscraping at <rmvd>"""

    # Creates the initial namedtuple that holds the hed, link,
    # and identified entities for each article.
    # Chosen articles will have their data stored in a Summary object.
    def retrieve_cluster_data(self, limit=None) -> List[namedtuple]:
        """Creates a stub for each article listed on <rmvd>"""
        print("retrieving CNN article stub")
        soup = Soup(get(self.source_url))
        # Scrape for headlines and links
        cnn_heds = [i.text for i in soup.find('div', {'class': 'afe4286c'}).find('a')]
        cnn_links = [i.attrs['href'] for i in soup.find('div', {'class': 'afe4286c'}).find('a')]
        # limit amount of data returned for clustering
        if limit is not None:
            cnn_heds = cnn_heds[:limit]
            cnn_links = cnn_links[:limit]
        #cnn = [i for i in cnn_heds if 'Analysis:' not in i and 'Opinion:' not in i]
        # Take this next line out of this function and place it where this data is used.
        article_tuples = [stub(i[0], i[1], [], self) for i in zip(cnn_links, cnn_heds) if 'Opinion' not in i[1] and 'Analysis' not in i[1]]
        print(f"Number of cnn articles: {len(cnn_heds)}")
        return article_tuples, len(cnn_heds)

    # Returns None if article is only 1 line.
    def retrieve_article(self, indata: stub) -> Tuple[str, List[Tuple[str, Any]]]:
        """Retrieves article data from <rmvd>: subhead if exists, date, author(s), and whole text"""
        print(f"""Retrieving article from:\n\t{self.source_url + indata.link}\n""")
        st.write(f"""Retrieving article from:\n\t{self.source_url + indata.link}\n""")
        repeat = 0
        good = False
        while repeat < 2 and not good:
            try:
                container = Soup(get(self.source_url + indata.link))
                good = True
            except Exception as e:
                print(f"Error:\n{e}")
                print(f"Problem url: \n\t{self.source_url + indata.link}")
                repeat += 1
        if good:
            story_container = container.find('div', {'class': 'afe4286c'})
            print(story_container)
            author = story_container.find('p',{'id':'byline'}).text
            story_date = story_container.find('p',{'id':'published datetime'}).text[9:]
            #if isinstance(story_container, Soup):
            #    return None, None
            scp = story_container.find('p')[4:]
     
            whole_text = ''.join([i.text for i in scp if i.text is not None])
            article_data = [
            self,
            indata.entities,
            indata.link,
            indata.hed,
            None,
            story_date,
            [author],
            len(whole_text.split(' ')),
        ]
        else:
            whole_text = None
            article_data = None
        # return whole text and data for summary
        return whole_text, article_data
