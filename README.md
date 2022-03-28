# TopicDig

### TopicDig uses whole article summarization to create topical digests from current news headlines

#### [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/mpolinsky/topicdig/main)

The app displays topics, the user chooses up to three, and the app spins up a topical digest scraped from the headlines.
This project makes heavy use of HuggingFace for NLP, and Gazpacho for web scraping.

The method of article selection here is arbitrary.  Pre-assigned article tags could be used to select groups of articles, or semantic-similarity methods could be used to evaluate the article text.  In practice, an enterprise that would institute such a system would have their articles accessible in a database they own, and would be able to perform background processing to have summaries ready on demand.

**The pipeline:**

* Current headlines are scraped from two news sites.
* NER is performed on each headline to extract topics, some headlines yield no topics.
* Article links are clustered according to entities in their headlines
* User selects up to three clusters
* Articles from those clusters are scraped, the articles summarized in chunks, and the summaries concatenated to create a digest.

**This app explores a few ideas:**

* **IR for QA and comprehension**
    * A cheap and quick way to explore area of research dominated by large, end-to-end trained models like RAG and NewsSum or w.e....TK
* **News delivery and access**
    * CNN provides summaries but there's a huge difference between being served something and being able to "create" my news. 
    * Sneaks around headlines...what's in the article?  Headlines can push and pull....
    * removes control over our attention but enables empowered consumption while keeping news production in the hands of pros.
* **Editorial ideation**
    * Can be used to find implied but uncovered stories by creating news assemblages without knowing eactly what you'll get.  Even though an editor knows what they're currently covering, imagine them writing a sentence describing each article on a piece of paper -- that's not the same as seeing the information in the final articles assembled and juxtaposed like this.  
* **Cross-article information access**
    * Information that's related and that paints a picture can be broken across multiple articles from different times...There are more stories lying latent in the told stories.
* **Whole news article summarization pitfalls and windfalls.**
    * Doing whole articles...technique and results.
* **Community pantry principle**
    * No free lunch but there is a community pantry.  It only gets you so close.
* **Evaluating summarization**
    * Difficult to objectively evaluate summarization capability beyond a general level.

****

This application was created as the culmination of a semester of independent graduate research into NLP and transformers.

Original repo for the earlier version of this app is located at https://github.com/mpolinsky/sju_final_project/
