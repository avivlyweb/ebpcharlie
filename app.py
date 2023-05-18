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

# Set up Pubmed API endpoints and query parameters
pubmed_search_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
pubmed_fetch_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
params = {
    "db": "pubmed",
    "retmode": "json",
    "retmax": 10,
    "api_key": "5cd7903972b3a715e29b76f1a15001ce9a08"  # replace with your actual API key
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
    message = response.choices[0].text.strip()
    return message

# Define function to search for articles using Pubmed API
def search_pubmed(query):
    params["term"] = query
    response = requests.get(pubmed_search_endpoint, params=params)
    data = response.json()
    article_ids = data["esearchresult"]["idlist"]
    return article_ids

# Fetch the full details of the articles using Pubmed API
def fetch_pubmed(article_ids):
    params = {
        "db": "pubmed",
        "retmode": "xml",
        "id": ",".join(article_ids)
    }
    response = requests.get(pubmed_fetch_endpoint, params=params)
    soup = BeautifulSoup(response.text, 'xml')
    articles_data = soup.find_all("PubmedArticle")
    return articles_data

# Extract MeSH terms, study type, and abstract from the articles data
def get_article_info(articles_data):
    articles = []
    for article_data in articles_data:
        article_id = article_data.find("PMID").text
        url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}"
        mesh_terms = [mesh_term.text for mesh_term in article_data.find_all("DescriptorName")]
        study_type = [type.text for type in article_data.find_all("PublicationType")]
        abstract = article_data.find("AbstractText").text if article_data.find("AbstractText") else ""
        articles.append({"id": article_id, "url": url, "mesh_terms": mesh_terms, "study_type": study_type, "abstract": abstract})
    return articles

# Title and intro
st.title("EBPCharlie: Evidence-Based Practice Assistor")
st.write("EBPCharlie uses AI and PubMed API to help you conduct systematic reviews, answer clinical questions, and save time in research. You can search using a clinical question or using the PICO framework.")

# PICO search
st.header("PICO Search")
patient = st.text_input("Patient, Population, or Problem")
intervention = st.text_input("Intervention")
comparison = st.text_input("Comparison")
outcome = st.text_input("Outcome")

if st.button("PICO Search"):
    if not patient or not intervention or not outcome:
        st.error("Please enter Patient/Problem, Intervention, and Outcome for PICO search.")
    else:
        pico_query = f"{patient} AND {intervention} AND {comparison} AND {outcome}"
        pico_articles = search_pubmed(pico_query)
        pico_articles = fetch_pubmed(pico_articles)
        pico_articles = get_article_info(pico_articles)
        st.write(f"Found {len(pico_articles)} articles related to your PICO question.")
        
        for article in pico_articles:
            prompt = f"Analyse this article related to the PICO question '{pico_query}':\nPMID: {article['id']}\nURL: {article['url']}\nMeSH Terms: {', '.join(article['mesh_terms'])}\nStudy Type: {', '.join(article['study_type'])}\nAbstract: {article['abstract']}\n\nPlease provide a brief summary and the main findings of this article."
            summary = generate_text(prompt)
            st.subheader(f"Summary of Findings for PMID: {article['id']}")
            st.write(summary)
            st.write("\n\n\n")

# Clinical question search
st.header("Clinical Question Search")
user_input = st.text_input("Enter your clinical question", key="clinical_question")

if st.button("Search Clinical Question"):
    if not user_input:
        st.error("Please enter a clinical question.")
    else:
        clinical_articles = search_pubmed(user_input)
        clinical_articles = fetch_pubmed(clinical_articles)
        clinical_articles = get_article_info(clinical_articles)
        st.write(f"Found {len(clinical_articles)} articles related to your clinical question.")
        
        for article in clinical_articles:
            prompt = f"Analyse this article related to the clinical question '{user_input}':\nPMID: {article['id']}\nURL: {article['url']}\nMeSH Terms: {', '.join(article['mesh_terms'])}\nStudy Type: {', '.join(article['study_type'])}\nAbstract: {article['abstract']}\n\nPlease provide a brief summary and the main findings of this article."
            summary = generate_text(prompt)
            st.subheader(f"Summary of Findings for PMID: {article['id']}")
            st.write(summary)
            st.write("\n\n\n")
