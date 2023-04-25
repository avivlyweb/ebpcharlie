import os
import openai
import requests
import json
import streamlit as st
from urllib.request import urlopen
from bs4 import BeautifulSoup
import html2text

# Set up OpenAI API credentials
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set up Pubmed API endpoint and query parameters
pubmed_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
params = {
    "db": "pubmed",
    "retmode": "json",
    "retmax": 5,
    "api_key": "5cd7903972b3a715e29b76f1a15001ce9a08"
}

# Define function to generate text using OpenAI API
def generate_text(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=2024,
        n=1,
        stop=None,
        temperature=0.7,
    )

    message = response.choices[0].text
    return message

# Define function to search for articles using Pubmed API
def search_pubmed(query):
    params["term"] = query
    response = requests.get(pubmed_endpoint, params=params)
    data = response.json()
    article_ids = data["esearchresult"]["idlist"]
    articles = [{"id": article_id, "url": f"https://pubmed.ncbi.nlm.nih.gov/{article_id}"} for article_id in article_ids]
    return articles

# Define function to scrape article abstracts
def scrape_abstract(articles):
    abstracts = []
    for article in articles:
        url = article["url"]
        html_page = urlopen(url)
        soup = BeautifulSoup(html_page)
        abstract = soup.find("div", {"class": "abstract-content selected"}).text
        abstracts.append({"id": article["id"], "url": url, "abstract": abstract})
    return abstracts

# Define function to convert html abstracts to text
def convert_to_text(abstracts):
    text_abstracts = []
    for abstract_info in abstracts:
        h = html2text.HTML2Text()
        h.ignore_links = True
        text_abstract = h.handle(abstract_info["abstract"])
        text_abstracts.append({"id": abstract_info["id"], "url": abstract_info["url"], "abstract": text_abstract})
    return text_abstracts

# Get user input
user_input = st.text_input("Hi there, I am EBPcharlie. What is your clinical question?")

# Search for articles using Pubmed API
if st.button("Search with EBPcharlie"):
    if not user_input:
        st.error("Please enter a clinical question to search for articles.")
    else:
        articles = search_pubmed(user_input)
        st.write(f"Found {len(articles)} articles related to your clinical question.")
        abstracts = scrape_abstract(articles)
        text_abstracts = convert_to_text(abstracts)

        # Generate a list of PMIDs and URLs
        pmid_url_list = "\n".join([f"PMID: {abstract_info['id']} URL: {abstract_info['url']}" for abstract_info in text_abstracts])

        # Generate prompt for OpenAI API
        prompt = f"Using your expert knowledge, analyze the following systematic reviews related to '{user_input}' published between 2021-2023:\n{pmid_url_list}\n\nProvide a summary of their findings that accurately reflects the content of these articles. List the most important outcomes in bullet points, and ensure that the PMID and URL mentioned for each outcome correspond to the correct article:"

        # Generate summary using OpenAI API
        summary = generate_text(prompt)
        st.subheader("Summary of Findings")
        st.write(summary)

        # Display article abstracts
        st.subheader("Article Abstracts")
        for abstract_info in text_abstracts:
            st.write(f"PMID: {abstract_info['id']}")
            st.write(f"URL: {abstract_info['url']}")
            st.write(abstract_info["abstract"])
            st.write("\n\n\n")
