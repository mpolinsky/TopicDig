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

**This app explores a few ideas:**

* **IR for QA and comprehension**
    * A cheap and quick way to explore area of research dominated by large, end-to-end trained systems such as RAG and MultiSum.
* **News delivery and access**
    * CNN provides summaries but there's a huge difference between being served something and being able to "create" my news. 
    * This method of news consumption gets around the headline as the single lure for an article, which avoids the issue of sensational or inaccurate headlines.
    * Enables empowered information consumption while keeping news production in the hands of professionals.
* **Editorial ideation**
    * Can be used to find implied but uncovered stories by creating news assemblages without knowing eactly what you'll get.  Even though an editor knows what they're currently covering, imagine them writing a sentence describing each article on a piece of paper -- that's not the same as seeing the information in the final articles assembled and juxtaposed as with this.  


* **Cross-article information access**
    * Information that's related and that paints a picture can be broken across multiple articles from different times...There are more stories lying latent in the told stories.
* **Whole news article summarization pitfalls and windfalls.**
    * Doing whole articles...technique and results.
* **Community pantry principle**
    * No free lunch but there is a community pantry.  It only gets you so close.
* **Evaluating summarization**
    * Difficult to objectively evaluate summarization capability beyond a general level.


## The basic interface:
<img width="514" alt="Screen Shot 2022-05-20 at 10 50 46 AM" src="https://user-images.githubusercontent.com/30514239/169554841-15a1db7e-9ef9-4221-ae62-14506da1daf4.png">

## What you see when you begin summarization:
<img width="479" alt="Screen Shot 2022-05-20 at 10 51 11 AM" src="https://user-images.githubusercontent.com/30514239/169554875-734f35e2-66d1-4547-9979-08acc7401124.png">

## What you get: a news digest covering the topics you select!
<img width="511" alt="Screen Shot 2022-05-20 at 10 51 03 AM" src="https://user-images.githubusercontent.com/30514239/169554884-e9992543-09ed-4f76-84a2-338191534117.png">



****

This application was originally created as the culmination of a semester of independent graduate research into NLP and transformers.

Original repo for the earlier version of this app is located at https://github.com/mpolinsky/sju_final_project/


[![scraper: gazpacho](https://img.shields.io/badge/scraper-gazpacho-C6422C)](https://github.com/maxhumber/gazpacho)

