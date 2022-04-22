# streamlit_app.py manages the whole TopicDig process
from typing import List, Set
from collections import namedtuple
import random
import requests
import json
from datetime import datetime as dt
from codetiming import Timer
import streamlit as st

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

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
        #'google/pegasus-multi_news',
        'dbmdz/bert-large-cased-finetuned-conll03-english'
        ))
    sources.append(CNNText(
        'cnn',
        'https://lite.cnn.com', 
        'sshleifer/distilbart-cnn-12-6',
        #'google/pegasus-multi_news',
        'dbmdz/bert-large-cased-finetuned-conll03-english'
    ))


    # initialize list to hold cluster data namedtuples
    cluster_data: List[namedtuple('article', ['link','hed','entities', 'source'])] 
    article_dict : dict[str:namedtuple]
    
    # For all sources retrieve_cluster_data 
    # returns List[namedtuples] with empty entity lists
    
    cluster_data = []
    article_meta = namedtuple('article_meta',['source', 'count'])
    cluster_meta : List[article_meta] = []
    for data_source in sources:
        if limit is not None:
        # c_data is a list of articleTuples and c_meta is the length of that but actually the length of one of the source lists...weird.
            c_data, c_meta = data_source.retrieve_cluster_data(limit//len(sources)) 
        else:
            c_data, c_meta = data_source.retrieve_cluster_data() 
        cluster_data.append(c_data)
        cluster_meta.append(article_meta(data_source.source_name, c_meta))
        st.session_state[data_source.source_name] = f"Number of articles from source: {c_meta}"

    cluster_data = cluster_data[0] + cluster_data[1]
    # NER
    # iterate the list of namedtuples, 
    for tup in cluster_data:
        # pass each hed to the api query method, return the dict 
        # through the ner_results function to the 'entities' list. 
        # Populate stub entities list
        perform_ner(tup, cache=use_cache)
        generate_clusters(clusters, tup)
    st.session_state['num_clusters'] = f"""Total number of clusters: {len(clusters)}"""
    
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
    
def show_length_graph():
    labels = [i for i in range(outdata['article_count'])]
    original_length = [outdata['summaries'][i]['original_length'] for i in outdata['summaries']]
    summarized_length = [outdata['summaries'][i]['summary_length'] for i in outdata['summaries']]       
    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars
     
    fig, ax = plt.subplots(figsize=(14,8))
    rects1 = ax.bar(x - width/2, original_length, width,  color='lightgreen',zorder=0)
    rects2 = ax.bar(x + width/2, summarized_length, width, color='lightblue',zorder=0)
   
    rects3 = ax.bar(x - width/2, original_length, width, color='none',edgecolor='black', lw=1.25,zorder=1)
    rects4 = ax.bar(x + width/2, summarized_length, width, color='none',edgecolor='black', lw=1.25,zorder=1)
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Text Length')
    ax.set_xticks(x)
    ax.set_yticks([i for i in range(0,max(original_length),max(summarized_length))])
    ax.set_xticklabels(labels)
    ax.set_xlabel('Article')
    
    plt.title('Original to Summarized Lengths in Space-Separated Tokens')
    #ax.hist(arr, bins=20)
    st.pyplot(fig)

# These could be passed through the command line
# or read from a config file.
# One of these is needed here for NER and one in Digestor for summarization.
NER_API_URL =  "https://api-inference.huggingface.co/models/dbmdz/bert-large-cased-finetuned-conll03-english"
headers = {"Authorization": f"""Bearer {st.secrets['ato']}"""}

LIMIT = 30 # Controls time and number of clusters.
USE_CACHE = True

if not USE_CACHE:
    print("NOT USING CACHE")
if LIMIT is not None:
    print(f"LIMIT: {LIMIT}")

# digest store am I using this though?  - april 15 2022
digests = dict() # key is cluster, value is digestor object
out_dicts = [] # Am I using this? -dit
# list to accept user choices
# retrieve cluster data and create dict to track each article (articleStubs)
# and create topic clusters by performing ner.
print("Initializing....")
article_dict, clusters = initialize(LIMIT, USE_CACHE)  
# We now have clusters and cluster data.  Redundancy?

# Welcome and explainer
st.title("Welcome to TopicDig!")
st.success(f"You select the topics, we summarize the relevant news and show you a digest, plus some info to help contextualize what the machine did.")
st.write(f"On the left you'll find a list of topics recently gleaned from current news headlines.  TopicDig lets you assemble digests of these stories using transformers!")
st.warning("Enjoy, and remember, these summaries contain a few kinds of issues, from untruths to missing attribution or topic sentences.  For more information on truthfulness in automatic summarization with transformers see https://arxiv.org/abs/2109.07958.")

st.subheader(f"How it works:")
st.write(f"""Select 1 to 3 topics from the drop down menus and click 'submit' to start generating your digest!""")
    
# Provides expandable container for refresh and summarization parameters, currently only chunk size
with st.expander("See extra options"):
    st.subheader("Refresh topics: ")
    st.write("You may want to refresh the topic lists if the app loaded several hours ago or you get no summary.")
    # button to refresh topics
    if st.button("Refresh topics!"):
        article_dict, clusters = initialize(LIMIT, USE_CACHE)      
    st.subheader("Select chunk size: ")
    st.write("Smaller chunks means more of the article included in the summary and a longer digest.")
    chunk_size = st.select_slider(label="Chunk size", options=[i for i in range(50,801,50)], value=400)
 
   
    
selections = []
choices = list(clusters.keys())
choices.insert(0,'None')

# May be desired in sidebar - april 15 2022
# st.write(f"CNN articles: {st.session_state['cnn']}")
# st.write(f"NPR articles: {st.session_state['npr']}")
# st.write(f"Number of clusters {st.session_state['num_clusters']}")


# Display topics to user currently in sidebar - april 15 2022
st.sidebar.subheader("Topics")  
st.sidebar.write("Here are the current news topics and the number of articles whose headlines featured those topics.") 
show_clusters = {i:len(clusters[i]) for i in clusters.keys()}
cdf = pd.DataFrame(data={"Cluster":list(show_clusters.keys()), "Articles":list(show_clusters.values())}  ).sort_values(by='Articles', ascending=False)
styler = cdf.style.hide_index()
st.sidebar.write(styler.to_html(), unsafe_allow_html=True)


# Get session time
st.session_state['dt'] = dt.now()
# Form used to take 3 menu inputs
with st.form(key='columns_in_form'):
    cols = st.columns(3)
    for i, col in enumerate(cols):
        selections.append(col.selectbox(f'Make a Selection', choices, key=i))
    submitted = st.form_submit_button('Submit')
    if submitted:
        selections = [i for i in selections for j in selections if i is not None]
        with st.spinner(text="Creating your digest: this will take a few moments."):
            chosen = []
            
            for i in selections: # i is supposed to be a list of stubs, mostly one
                if i != 'None':
                    for j in clusters[i]:
                        if j not in chosen:
                            chosen.append(j) # j is a stub.
        
            # Digestor uses 'chosen' to create digest.  
            # 'user_choicese' is passed for reference.  
            digestor = Digestor(timer=Timer(), cache = USE_CACHE, stubs=chosen, user_choices=selections, token_limit=1024, word_limit=chunk_size)
            # happens internally but may be used differently so it isn't automatic upon digestor creation.
            # Easily turn caching off for testing.
            st.subheader("What you'll see:")
            st.write("First you'll see a list of links appear below.  These are the links to the original articles being summarized for your digest, so you can get the full story if you're interested, or check the summary against the source.")
            st.write("In a few moments, your machine-generated digest will appear below the links, and below that you'll see an approximate word count of your digest and the time in seconds that the whole process took!")
            st.write("You'll also see a graph showing, for each article and summary, the original and summarized lengths.")
            st.write("Finally, you will see some possible errors detected in the summaries.  This area of NLP is far from perfection and always developing.  Hopefully this is an interesting step in the path!")
            digestor.digest() # creates summaries and stores them associated with the digest



            # Get displayable digest and digest data
            outdata = digestor.build_digest()
           
        if len(digestor.text) == 0:
            st.write("No text to return...huh.")    
        else:
            st.subheader("Your digest:")
            st.info(digestor.text)
    
            st.subheader("Summarization stats:")
            col1, col2, col3 = st.columns(3)
            col1.metric("Digest Time", f"""{digestor.timer.timers['digest_time']:.2f}""", "seconds")
            col2.metric("Digest Length", str(len(digestor.text.split(" "))), 'space-sep tokens' )
            col3.metric("Article Count", str(outdata['article_count']), "articles" )

            st.write("Length reduction:")
            # Summarize the findings for all models
            show_length_graph()
            
             # Issues section: search for known problems with summaries
            
            st.header("Issues: ")
            st.subheader("Repetition:")
            rep_check = check_for_word_and_word(digestor.text)
            if rep_check is not None:
                st.write(f"Following phrases repeat: {rep_check}")
                found_index = digestor.text.find(rep_check)
                st.write("Sample:")
                st.write(f"{text[found_index-40:found_index+40]}")
            else:
                st.write("No repetition detected.")
              
            # Same article from different sources
            st.subheader("Text redundancy: ")
            for each in digestor.summaries:
                # check if two source articles share a cluster and not a source.
                pass
            st.write("If more than one source have their own versions of the same topic from the same perspective, the result may be reptetive, or it may add nuance and the two summaries may complement each other.")
      
