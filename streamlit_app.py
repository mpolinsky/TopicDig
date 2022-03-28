# streamlit_app.py manages the whole TopicDig process
from typing import List, Set
from collections import namedtuple
import random
import requests
import json

from codetiming import Timer
import streamlit as st

from digestor import Digestor
from source import Source
from scrape_sources import NPRLite, CNNText, stub



def initialize(limit, rando, use_cache=True):
    clusters: dict[str:List[namedtuple]] = dict()
    # This is a container for the source classes.
    # Make sure you handle this.  Whats the deal.
    sources:List[Source]= [] # Write them and import? Read a config?
    # FOR NOW ONLY add this explicitly here.  
    # MUST read in final version though.
    sources.append(NPRLite(
        'npr', 
        'https://text.npr.org/1001', 
        'sshleifer/distilbart-cnn-12-6',
        'dbmdz/bert-large-cased-finetuned-conll03-english'
        ))
    sources.append(CNNText(
        'cnn',
        'https://lite.cnn.com', 
        'sshleifer/distilbart-cnn-12-6',
        'dbmdz/bert-large-cased-finetuned-conll03-english'
    ))


    # initialize list to hold cluster data namedtuples
    cluster_data: List[namedtuple('article', ['link','hed','entities', 'source'])] 
    article_dict : dict[str:namedtuple]
    
    # For all sources retrieve_cluster_data 
    # returns List[namedtuples] with empty entity lists
    # TEST THIS ALL V V V
    cluster_data = []
    article_meta = namedtuple('article_meta',['source', 'count'])
    cluster_meta : List[article_meta] = []
    print("Calling data source retrieve cluster data....")
    for data_source in sources:
        if limit is not None:
            c_data, c_meta = data_source.retrieve_cluster_data(limit//len(sources)) 
        else:
            c_data, c_meta = data_source.retrieve_cluster_data() 
        cluster_data.append(c_data)
        cluster_meta.append(article_meta(data_source.source_name, c_meta))
    print("Finished...moving on to clustering...")
    cluster_data = cluster_data[0] + cluster_data[1]
    # NER
    # iterate the list of namedtuples, 
    for tup in cluster_data:
        # pass each hed to the api query method, return the dict 
        # through the ner_results function to the 'entities' list. 
        # Populate stub entities list
        perform_ner(tup, cache=use_cache)
        generate_clusters(clusters, tup)
    st.write(f"""Total number of clusters: {len(clusters)}""")
    
    # Article stubs tracks all stubs
    # If cluster is unsummarized, its hed's value is the namedtuple stub.  
    # Else reference digestor instance so summary can be found.
    article_dict = {stub.hed: stub for stub in cluster_data}
    
    return article_dict, clusters


# Am I going to use this for those two lines?
def perform_ner(tup:namedtuple('article',['link','hed','entities', 'source']), cache=True):
    with Timer(name="ner_query_time", logger=None):
        result = ner_results(ner_query(
                {
                    "inputs":tup.hed,
                    "paramters":
                    {
                        "use_cache": cache,
                    },
                }            
            ))
    for i in result:
        tup.entities.append(i) 



def ner_query(payload):
    print("making a query....")
    data = json.dumps(payload)
    response = requests.request("POST", NER_API_URL, headers=headers, data=data)
    return json.loads(response.content.decode("utf-8"))



def generate_clusters(
    the_dict: dict, 
    tup : namedtuple('article_stub',[ 'link','hed','entities', 'source'])
    ) -> dict:
    for entity in tup.entities: 
        # Add cluster if entity not already in dict
        if entity not in the_dict:
            the_dict[entity] = []
        # Add this article's link to the cluster dict
        the_dict[entity].append(tup)
    

def ner_results(ner_object, groups=True, NER_THRESHOLD=0.5) -> List[str]:
    # empty lists to collect our entities
    people, places, orgs, misc = [], [], [], []

    # 'ent' and 'designation' handle the difference between dictionary keys 
    # for aggregation strategy grouped vs ungrouped
    ent = 'entity' if not groups else 'entity_group'
    designation = 'I-' if not groups else ''

    # Define actions -- this is a switch-case dictionary.
    # keys are the identifiers used inthe return dict from
    # the ner_query.  
    # values are list.append() for each of the lists
    # created at the top of the function.  They hold sorted entities.
    # actions is used to pass entities into the lists.
    # Why I called it actions I have no idea rename it.
    actions = {designation+'PER':people.append,
               designation+'LOC':places.append, 
               designation+'ORG':orgs.append,
               designation+'MISC':misc.append
            } # Is this an antipattern?

    #  For each dictionary in the ner result list, if the entity str doesn't contain a '#' 
    # and the confidence is > 90%, add the entity to the list for its type.
  
    # actions[d[ent]](d['word']) accesses the key of actions that is returned 
    # from d[ent] and then passes the entity name, returned by d['word'] to 
    # the 'list.append' waiting to be called in the dict actions. 
    # Note the ().  We access actions to call its append...
    readable = [ actions[d[ent]](d['word']) for d in ner_object if '#' not in d['word'] and d['score'] > NER_THRESHOLD ]

    # create list of all entities to return
    ner_list = [i for i in set(people) if len(i) > 2] + [i for i in set(places) if len(i) > 2] + [i for i in set(orgs) if len(i) > 2] + [i for i in set(misc) if len(i) > 2]

    return ner_list

# These could be passed through the command line
# or read from a config file.
# One of these is needed here for NER and one in Digestor for summarization.
NER_API_URL =  "https://api-inference.huggingface.co/models/dbmdz/bert-large-cased-finetuned-conll03-english"
headers = {"Authorization": f"""Bearer {st.secrets['ato']}"""}

LIMIT = 20 # Controls time and number of clusters.
USE_CACHE = True

if not USE_CACHE:
    print("NOT USING CACHE--ARE YOU GATHERING DATA?")
if LIMIT is not None:
    print(f"LIMIT: {LIMIT}")

# digest store
digests = dict() # key is cluster, value is digestor object
out_dicts = []
# list to accept user choices
# retrieve cluster data and create dict to track each article (articleStubs)
# and create topic clusters by performing ner.
print("Initializing....")
article_dict, clusters = initialize(LIMIT, USE_CACHE)  
# We now have clusters and cluster data.  Redundancy.
# We call a display function and get the user input.  
# For this its still streamlit.

selections = []
choices = list(clusters.keys())
choices.insert(0,'None')
# Form used to take 3 menu inputs
with st.form(key='columns_in_form'):
    cols = st.columns(3)
    for i, col in enumerate(cols):
        selections.append(col.selectbox(f'Make a Selection', choices, key=i))
    submitted = st.form_submit_button('Submit')
    if submitted:
        selections = [i for i in selections if i is not None]
        with st.spinner(text="Digesting...please wait, this will take a few moments...Maybe check some messages or start reading the latest papers on summarization with transformers...."):
            found = False

            # Check if we already have this digest.
            for i in digests:    
                if set(selections) == set(list(i)):
                    digestor = digests[i]
                    found = True
                    break

            # If we need a new digest
            if not found:
                chosen = []
                # Why not just use answers.values()?
                for i in selections: # i is supposed to be a list of stubs, mostly one
                    if i != 'None':
                        for j in clusters[i]:
                            if j not in chosen:
                                chosen.append(j) # j is supposed to be a stub.

                # Article dict contains stubs for unprocessed articles and lists of summarized chunks for processed ones.
                # Here we put together a list of article stubs and/or summary chunks and let the digestor sort out what it does with them,
                chosen = [i if isinstance(article_dict[i.hed], stub) else article_dict[i.hed] for i in chosen]
                # Digestor uses 'chosen', passed through 'stubs' to create digest.  
                # 'user_choicese' is passed for reference.  
                #    Passing list(answers.values()) includes 'None' choices.
                digestor = Digestor(timer=Timer(), cache = USE_CACHE, stubs=chosen, user_choices=list(selections))
                # happens internally but may be used differently so it isn't automatic upon digestor creation.
                # Easily turn caching off for testing.
                digestor.digest() # creates summaries and stores them associated with the digest



            # Get displayable digest and digest data
            digestor.build_digest()# only returns for data collection
            digests[tuple(digestor.user_choices)] = digestor

        if len(digestor.text) == 0:
            st.write("You didn't select a topic!")    
        else:
            st.write("Your digest is ready:\n")

        st.write(digestor.text)
    
