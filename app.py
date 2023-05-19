import os
import openai
import requests
import json
import streamlit as st
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# Set up OpenAI API credentials
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set up Pubmed API endpoints and query parameters
pubmed_search_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
pubmed_fetch_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
params = {
    "db": "pubmed",
    "retmode": "json",
    "retmax": 10,
    "api_key": "5cd7903972b3a715e29b76f1a15001ce9a08"
}

# PEDro Search URL
pedro_search_url = "https://search.pedro.org.au/search-results?query={}"

# Define function to generate text using OpenAI API
def generate_text(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1000,
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

# Extract MeSH terms and abstract from the articles data
def get_mesh_terms(articles_data):
    articles = []
    for article_data in articles_data:
        article_id = article_data.find("PMID").text
        url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}"
        mesh_terms = [mesh_term.text for mesh_term in article_data.find_all("DescriptorName")]
        abstract = article_data.find("AbstractText").text if article_data.find("AbstractText") else ""
        articles.append({"id": article_id, "url": url, "mesh_terms": mesh_terms, "abstract": abstract})
    return articles

# Search PEDro and extract data
def search_pedro(query):
    response = requests.get(pedro_search_url.format(quote_plus(query)))
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all('div', {'class': 'search-result'})
    pedro_results = []
    for result in results:
        title = result.find('h2').text.strip()
        link = "https://search.pedro.org.au" + result.find('a')['href']
        description = result.find('div', {'class': 'description'}).text.strip()
        pedro_results.append({"title": title, "link": link, "description": description})
    return pedro_results

# App header
st.title("EBPcharlie")
st.header("Evidence-Based Medicine AI Assistant")
st.write("""
This app uses AI to assist with evidence-based medicine (EBM). 
Input your clinical question or use the PICO (Patient, Intervention, Comparison, Outcome) method to generate a query.
The app will then search PubMed and PEDro for relevant articles and provide a structured summary.
""")

# Clinical question search
user_input = st.text_input("Hi there, I am EBPcharlie. What is your clinical question?")
if st.button("Search with EBPcharlie"):
    if not user_input:
        st.error("Please enter a clinical question to search for articles.")
    else:
        # PubMed Search
        article_ids = search_pubmed(user_input)
        if not article_ids:
            st.write("No articles found in PubMed related to your clinical question.")
        else:
            st.write(f"Found {len(article_ids)} articles in PubMed related to your clinical question.")
            articles_data = fetch_pubmed(article_ids)
            articles = get_mesh_terms(articles_data)
            article_list = "\n\n".join([f"PMID: {article['id']}, URL: {article['url']}, MeSH terms: {', '.join(article['mesh_terms'])}, Abstract: {article['abstract']}" for article in articles])
            prompt = f"Clinical question: {user_input}\n\nArticles:\n{article_list}\n\nPlease provide a brief outcome."
            text = generate_text(prompt)
            st.markdown(f"**Outcome related to your clinical question**:\n{text}\n---")

        # PEDro Search
        pedro_results = search_pedro(user_input)
        if not pedro_results:
            st.write("No articles found in PEDro related to your clinical question.")
        else:
            st.write(f"Found {len(pedro_results)} articles in PEDro related to your clinical question.")
            for result in pedro_results:
                st.write(f"[{result['title']}]({result['link']})")
                st.write(result['description'])
                st.write("---")

# PICO query
st.header("Or, generate a PICO Query")
p = st.text_input("Patient, Population, or Problem")
i = st.text_input("Intervention")
c = st.text_input("Comparison")
o = st.text_input("Outcome")

# Generate PICO query and search for articles
if st.button("Generate PICO Query"):
    if not all([p, i, c, o]):
        st.error("Please fill in all the PICO fields to generate a query.")
    else:
        pico_query = f"{p} AND {i} AND {c} AND {o}"
        st.markdown(f"**Generated PICO question**: In patients with {p}, how does {i} compare to {c} for {o}?")
        article_ids = search_pubmed(pico_query)
        if not article_ids:
            st.write("No articles found related to your PICO question.")
        else:
            st.write(f"Found {len(article_ids)} articles related to your PICO question.")
            articles_data = fetch_pubmed(article_ids)
            articles = get_mesh_terms(articles_data)
            for article in articles:
                prompt = f"PICO question: {pico_query}\n\nArticle:\nPMID: {article['id']}, URL: {article['url']}, MeSH terms: {', '.join(article['mesh_terms'])}, Abstract: {article['abstract']}\n\nPlease provide a brief outcome."
                text = generate_text(prompt)
                st.markdown(f"**Outcome related to your PICO question**:\n{text}\n---")
