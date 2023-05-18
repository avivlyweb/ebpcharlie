import os
import openai
import requests
import json
import streamlit as st
from urllib.request import urlopen
from bs4 import BeautifulSoup
import html2text

# Set up OpenAI API credentials
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up Pubmed API endpoint and query parameters
pubmed_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
params = {
    "db": "pubmed",
    "retmode": "json",
    "retmax": 5,
    "api_key": os.getenv("PUBMED_API_KEY")
}

# Define list of study types
study_types = ["randomized controlled trial", "meta-analysis", "clinical trial", "protocol"]

# Define function to generate text using OpenAI API
def generate_text(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.7,
    )
    message = response.choices[0].text.strip()
    return message

# Define function to search for articles using Pubmed API
def search_pubmed(query):
    params["term"] = query
    response = requests.get(pubmed_endpoint, params=params)
    data = response.json()
    article_ids = data["esearchresult"]["idlist"]
    articles = [{"id": article_id, "url": f"https://pubmed.ncbi.nlm.nih.gov/{article_id}"} for article_id in article_ids]
    return articles

# Define function to scrape article abstracts and MeSH terms
def scrape_articles(articles):
    for article in articles:
        url = article["url"]
        html_page = urlopen(url)
        soup = BeautifulSoup(html_page, features="lxml")
        abstract = soup.find("div", {"class": "abstract-content selected"}).text
        mesh_terms = [mesh.get_text().lower() for mesh in soup.find_all("li", {"class": "mesh-term"})]
        article["abstract"] = abstract
        article["mesh_terms"] = mesh_terms

        # Identify the study type based on MeSH terms
        article["study_type"] = [study_type for study_type in study_types if study_type in mesh_terms]
    return articles

# Get user input
user_input = st.text_input("Hi there, I am EBPcharlie. What is your clinical question?")

# Search for articles using Pubmed API
if st.button("Search with EBPcharlie"):
    if not user_input:
        st.error("Please enter a clinical question to search for articles.")
    else:
        articles = search_pubmed(user_input)
        st.write(f"Found {len(articles)} articles related to your clinical question.")
        articles = scrape_articles(articles)

        # Generate a list of PMIDs, URLs, MeSH terms, and study types
        article_list = "\n".join([f"PMID: {article['id']}\nURL: {article['url']}\nMeSH terms: {', '.join(article['mesh_terms'])}\nStudy type: {', '.join(article['study_type'])}\nAbstract: {article['abstract']}\n" for article in articles])

        # Generate prompt for OpenAI API
        prompt = f"Using your expert knowledge, analyze the following systematic reviews related to '{user_input}' published between 2019-2023:\n{article_list}\n\nPlease provide a focused and efficient analysis with the following sections:\n\n1. Focused Summary of Findings:\n- Provide a concise summary of the main findings of these articles, focusing on the most significant points.\n\n2. Important Outcomes (with PMID, URL, MeSH terms, and Study type):\n- List the most significant outcomes, associating each outcome with its PMID, URL, MeSH terms and study type.\n\n3. Comparisons and Contrasts:\n- Highlight any key differences or similarities between the findings of these articles.\n\n4. Noteworthy Treatments or Methodologies:\n- Mention any remarkable treatments or methodologies presented in these articles that could have substantial impact in the field.\n\n5. Potential Future Research Directions:\n- Suggest any potential future research directions based on the findings of these articles.\n\n6. Key Takeaways:\n- Summarize the most critical points from these articles that will benefit the reader's research."

        # Generate summary using OpenAI API
        summary = generate_text(prompt)
        st.subheader("Summary of Findings")
        st.write(summary)

        # Display article abstracts, MeSH terms, and study types
        st.subheader("Article Details")
        for article in articles:
            st.write(f"PMID: {article['id']}")
            st.write(f"URL: {article['url']}")
            st.write(f"MeSH terms: {', '.join(article['mesh_terms'])}")
            st.write(f"Study type: {', '.join(article['study_type'])}")
            st.write(f"Abstract: {article['abstract']}")
            st.write("\n\n\n") 
