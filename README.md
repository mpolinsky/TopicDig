# TopicDig

### TopicDig uses whole article summarization to create topical digests from current news headlines

#### [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/mpolinsky/topicdig/main)

The app displays topics, the user chooses up to three, and the app spins up a topical digest scraped from the headlines.
This project makes heavy use of HuggingFace for NLP, and Gazpacho for web scraping.

**The pipeline:**

* Current headlines are scraped from two news sites.
* NER is performed on each headline to extract topics, some headlines yield no topics.
* Article links are clustered according to entities in their headlines
* User selects up to three clusters
* Articles from those clusters are scraped, the articles summarized in chunks, and the summaries concatenated to create a digest.

This application was created as the culmination of a semester of independent graduate research into NLP and transformers.

Original repo for the earlier version of this app is located at https://github.com/mpolinsky/sju_final_project/
