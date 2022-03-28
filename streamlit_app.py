import streamlit as st

from transformers import pipeline, AutoModel, AutoTokenizer

import time

from time import time as t

from gazpacho import Soup, get

import tokenizers

import json

import requests

#############

# FUNCTIONS #

#############

ex = []

# Query the HuggingFace Inference engine.  

def query(payload):

    data = json.dumps(payload)

    response = requests.request("POST", API_URL, headers=headers, data=data)

    return json.loads(response.content.decode("utf-8"))

    

def ner_query(payload):

    data = json.dumps(payload)

    response = requests.request("POST", NER_API_URL, headers=headers, data=data)

    return json.loads(response.content.decode("utf-8"))

# gets links and identifies if they're cnn or npr

def get_articles(user_choices, cnn_dict, npr_dict):

    clustLinks = []

    heds = {}

    

    # Get all headlines from each cluster -- add to dict and record number of clusters of interest the headline appeared in.

    for each in user_choices:

        for beach in clusters[each.lower()]:

            if beach not in heds:

                heds[beach] = 1

            else:

                heds[beach] += 1

                

    # Convert keys (headlines) to list then sort in descending order of prevalence

    sorted_heds = list(heds.keys())

    sorted_heds.sort(key=lambda b: heds[b], reverse=True)

    

    for each in sorted_heds:

        try:

            # look up the headline in cnn

            clustLinks.append(('cnn',cnn_dict[each]))

            # if exception KeyError then lookup in npr

        except KeyError:

            clustLinks.append(('npr',npr_dict[each]))   

    return clustLinks

# gets articles from source via scraping

def retrieve(input_reslist):

    cnn = 'https://lite.cnn.com'

    npr = 'https://text.npr.org'

    articles = []

    

    # Scrapes from npr or cnn.  Should modularize this and use a dict as a switch-case

    for each in input_reslist:

        if each[0] == 'npr':

            container = Soup(get(npr+each[1])).find('div', {'class': "paragraphs-container"}).find('p')

            articles.append(container)

        if each[0] == 'cnn':

            container = Soup(get(cnn+each[1])).find('div', {'class': 'afe4286c'})

            # Extract all text from paragraph tags, each extracted from container

            #story = '\n'.join([x.text for x in container.find('p') if x.text != ''])

            story = container.find('p')

            articles.append(story[4:])

        time.sleep(1)

    return articles

# Returns a list of articles

# Takes list of articles and assigns each articles' text to an int for some reason....

#

## *** Dictionary might shuffle articles?

#

def art_prep(retrieved):

    a = []

    for each in retrieved:

        if type(each) is not list:

            a.append(each.strip())

        else:

            a.append(''.join([art.strip() for art in each]))

    return a

# User choices is the list of user-chosen entities.

def seek_and_sum(user_choices, cnn_dict, npr_dict):

    # If no topics are selected return nothing

    if len(user_choices) == 0:

        return []

    digs = []

    prepped=art_prep(retrieve(get_articles(user_choices, cnn_dict, npr_dict)))

    # Final is the output...the digest.

    for piece in prepped:

        digs.append(create_summaries(piece, 'sshleifer/distilbart-cnn-12-6'))

    # Opportunity for processing here

    

    return digs

# Chunks

def chunk_piece(piece, limit):

    words = len(piece.split(' ')) # rough estimate of words.  # words <= number tokens generally.

    perchunk = words//limit

    base_range = [i*limit for i in range(perchunk+1)]

    range_list = [i for i in zip(base_range,base_range[1:])]

    #range_list.append((range_list[-1][1],words))   try leaving off the end (or pad it?)

    chunked_pieces = [' '.join(piece.split(' ')[i:j]).replace('\n','').replace('.','. ') for i,j in range_list]

    return chunked_pieces

# Summarizes

def create_summaries(piece, chkpnt, lim=400):

    tokenizer = AutoTokenizer.from_pretrained(chkpnt)

    limit = lim

    count = -1

    summary = []

    words = len(piece.split(' '))

    if words >= limit:

        # chunk the piece

        #print(f'Chunking....')

        proceed = False

        while not proceed:

            try: 

                chunked_pieces = chunk_piece(piece, limit)

                for chunk in chunked_pieces:

                    token_length = len(tokenizer(chunk))

                    

                    # Perform summarization

                    if token_length <= 512:

                        data = query({ "inputs": str(chunk), "parameters": {"do_sample": False} }) # The way I'm passing the chunk could be the problem?  In a loop by ref?

                        summary.append(data[0]['summary_text'])

                        proceed = True 

                    else:

                        proceed = False

                        limit -= 2  # Try to back off as little as possible.

                        summary = []  # empty summary we're starting again.

            except IndexError: # Caused when 400 words get tokenized to > 512 tokens.  Rare.

                proceed = False

                # lower the limit

                limit -= 2  # Try to back off as little as possible.

                summary = []  # empty summary we're starting again.

        days_summary = ' '.join(summary) # Concatenate partial summaries

    else: 

        #print(f'Summarizing whole piece')

        proceed = False

        while not proceed:

            try:

                # Perform summarization

                data = query({ "inputs": str(piece), "parameters": {"do_sample": False} })

                days_summary = data[0]['summary_text']

                proceed= True

            except IndexError:

                proceed = False

                piece = piece[:-4]

                days_summary = ''     

    return days_summary

# This function creates a nice output from the dictionary the NER pipeline returns.

# It works for grouped_entities = True or False.

def ner_results(ner_object, indent=False, groups=True, NER_THRESHOLD=0.5):

    # empty lists to collect our entities

    people, places, orgs, misc = [], [], [], []

    # 'ent' and 'designation' handle the difference between dictionary keys 

    # for aggregation strategy grouped vs ungrouped

    ent = 'entity' if not groups else 'entity_group'

    designation = 'I-' if not groups else ''

    # Define actions -- this is a switch-case dictionary.

    actions = {designation+'PER':people.append,

             designation+'LOC':places.append, 

             designation+'ORG':orgs.append,

             designation+'MISC':misc.append}

    # For each dictionary in the ner result list, if it doesn't contain a '#' 

    #   and the confidence is > 90%, add the entity name to the list for its type.

    readable = [ actions[d[ent]](d['word']) for d in ner_object if '#' not in d['word'] and d['score'] > NER_THRESHOLD ]

    # create list of all entities to return

    ner_list = [i for i in set(people) if len(i) > 2] + [i for i in set(places) if len(i) > 2] + [i for i in set(orgs) if len(i) > 2] + [i for i in set(misc) if len(i) > 2]

    return ner_list

    

@st.cache(hash_funcs={tokenizers.Tokenizer: id})

def create_ner_dicts(state=True):

    # Changing this will run the method again, refreshing the topics

    status = state

    

    url1 = 'https://lite.cnn.com/en'

    soup_cnn = Soup(get(url1))

    # extract each headline from the div containing the links.

    cnn_text = [i.text for i in soup_cnn.find('div', {'class': 'afe4286c'}).find('a')]

    cnn_links = [i.attrs['href'] for i in soup_cnn.find('div', {'class': 'afe4286c'}).find('a')]

    cnn = [i for i in cnn_text if 'Analysis:' not in i and 'Opinion:' not in i]

    

    

    # Get current links...in the future you'll have to check for overlaps.

    url2 = 'https://text.npr.org/1001'

    soup = Soup(get(url2))

    # extract each headline

    npr_text = [i.text for i in soup.find('div', {'class': 'topic-container'}).find('ul').find('a')]

    npr_links = [i.attrs['href'] for i in soup.find('div', {'class': 'topic-container'}).find('ul').find('a')]

    npr = [i for i in npr_text if 'Opinion:' not in i]

    

    cnn_dict = {k[0]:k[1] for k in zip(cnn_text,cnn_links)}

    npr_dict = {k[0]:k[1] for k in zip(npr_text,npr_links)}

   

    # START Perform NER

    cnn_ner = {x:ner_results(ner_query(x)) for x in cnn} ###################################################################################################

    npr_ner = {x:ner_results(ner_query(x)) for x in npr} #################################   #################################    #################################

    

    return cnn_dict, npr_dict, cnn_ner, npr_ner

## A function to change a state variable in create_dicts() above

##      that then runs it and creates updated clusters.

def get_news_topics(cnn_ner, npr_ner):

    

    ## END Perform NER 

    

    # Select from articles.

    

    ## Select from articles that are clusterable only. (Entities were recognized.)

    cnn_final = {x:npr_ner[x] for x in npr_ner.keys() if len(npr_ner[x]) != 0} 

    npr_final =  {y:cnn_ner[y] for y in cnn_ner.keys() if len(cnn_ner[y]) != 0 }

    

    # What's in the news?

    # Get entities named in the pool of articles we're drawing from

    e_list = []

    for i in [i for i in cnn_final.values()]:

        for j in i:

            e_list.append(j)

    for k in [k for k in npr_final.values()]:

        for j in k:

            e_list.append(j)

        

    # This is a dictionary with keys: the list items....

    clusters = {k.lower():[] for k in e_list}

    

    ## Perform Clustering

    for hed in cnn_final.keys():

        for item in cnn_final[hed]:

            clusters[item.lower()].append(hed) # placing the headline in the list corresponding to the dictionary key for each entity.

    for hed in npr_final.keys():

        for item in npr_final[hed]:

            clusters[item.lower()].append(hed) 

    

    return clusters

    

    

def update_topics():

    st.legacy_caching.clear_cache()

    dicts = [i for i in create_ner_dicts()]

    clusters = get_news_topics(cnn_ner, npr_ner)

    return clusters, dicts

    

    

#############

#   SETUP   #

#############

# Auth for HF Inference API and URL to the model we're using -- distilbart-cnn-12-6

headers = {"Authorization": f"""Bearer {st.secrets["ato"]}"""}

API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"

NER_API_URL =  "https://api-inference.huggingface.co/models/dbmdz/bert-large-cased-finetuned-conll03-english"

#############

#PROCESSING #

#############

st.write(f"""**Welcome!**\nThis app lets you generate digests of topics currently in the news.  Select up to three current news topics and the digest lets you know what the latest news on those topics is!""") # Can I make this disappear?

cnn_dict, npr_dict, cnn_ner, npr_ner = create_ner_dicts()

clusters = get_news_topics(cnn_ner, npr_ner)

selections = []

choices = [None]

for i in list(clusters.keys()):

    choices.append(i)

# button to refresh topics

if st.button("Refresh topics!"):

    new_data = update_topics()

    clusters = new_data[0]

    cnn_dict, npr_dict, cnn_ner, npr_ner = new_data[1][0], new_data[1][1], new_data[1][2], new_data[1][3]

    

# Form used to take 3 menu inputs

with st.form(key='columns_in_form'):

    cols = st.columns(3)

    for i, col in enumerate(cols):

        selections.append(col.selectbox(f'Make a Selection', choices, key=i))

    submitted = st.form_submit_button('Submit')

    if submitted:

        selections = [i for i in selections if i is not None]

        with st.spinner(text="Digesting...please wait, this may take up to 20 seconds..."):

            digest = seek_and_sum(selections, cnn_dict, npr_dict)

        if len(digest) == 0:

            st.write("You didn't select a topic!")    

        else:

            st.write("Your digest is ready:\n")

      

            count = 0

            for each in digest:

                count += 1

                st.write(each)
