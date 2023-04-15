import os
import openai
import requests
import json
import streamlit as st
from urllib.request import urlopen
from bs4 import BeautifulSoup
import html2text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI API credentials
openai.api_key = st.secrets["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"]


# Set up Pubmed API endpoint and query parameters
pubmed_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
params = {
    "db": "pubmed",
    "retmode": "json",
    "retmax": 10,
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
    return article_ids

# Define function to scrape article abstracts
def scrape_abstract(article_ids):
    abstracts = []
    for article_id in article_ids:
        url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}"
        html_page = urlopen(url)
        soup = BeautifulSoup(html_page)
        abstract = soup.find("div", {"class": "abstract-content selected"}).text
        abstracts.append(abstract)
    return abstracts

# Define function to convert html abstracts to text
def convert_to_text(abstracts):
    text_abstracts = []
    for abstract in abstracts:
        h = html2text.HTML2Text()
        h.ignore_links = True
        text_abstract = h.handle(abstract)
        text_abstracts.append(text_abstract)
    return text_abstracts

# Get user input
user_input = st.text_input("Hi there, I am EBPcharlie What is your clinical question?")

# Generate prompt for OpenAI API
prompt = f"Find systematic reviews related to '{user_input}'  published between 2021-2023 using Pubmed API and provide a summary of their findings and list in bullet points the most important outcome:"

# Search for articles using Pubmed API
if st.button("Search with EBPcharlie"):
    if not user_input:
        st.error("Please enter a clinical question to search for articles.")
    else:
        article_ids = search_pubmed(user_input)
        st.write(f"Found {len(article_ids)} articles related to your clinical question.")
        abstracts = scrape_abstract(article_ids)
        text_abstracts = convert_to_text(abstracts)

        # Generate summary using OpenAI API
        summary = generate_text(prompt)
        st.subheader("Summary of Findings")
        st.write(summary)

        # Display article abstracts
        st.subheader("Article Abstracts")
        for i in range(len(article_ids)):
            st.write(f"Article {i+1}:")
            st.write(text_abstracts[i])
            st.write("\n\n\n")
