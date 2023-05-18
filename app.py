import os
import openai
import requests
import json
import streamlit as st
from bs4 import BeautifulSoup

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

# App header
st.title("EBPcharlie")
st.header("Evidence-Based Medicine AI Assistant")
st.write("""
This app uses AI to assist with evidence-based medicine (EBM). 
Input your clinical question or use the PICO (Patient, Intervention, Comparison, Outcome) method to generate a query.
The app will then search PubMed for relevant articles and provide a structured summary.
""")

# Clinical question search
user_input = st.text_input("Hi there, I am EBPcharlie. What is your clinical question?")
if st.button("Search with EBPcharlie"):
    if not user_input:
        st.error("Please enter a clinical question to search for articles.")
    else:
        article_ids = search_pubmed(user_input)
        if not article_ids:
            st.write("No articles found related to your clinical question.")
        else:
            st.write(f"Found {len(article_ids)} articles related to your clinical question.")
            articles_data = fetch_pubmed(article_ids)
            articles = get_mesh_terms(articles_data)
            # Generate prompt for OpenAI API
            article_list = "\n\n".join([f"PMID: {article['id']}, URL: {article['url']}, MeSH terms: {', '.join(article['mesh_terms'])}, Abstract: {article['abstract']}" for article in articles])
            prompt = f"Using your expert knowledge, analyze the following systematic reviews related to '{user_input}' published between 2019-2023:\n{article_list}\n\nPlease provide a structured analysis with the following sections:\n\n1. Summary of Findings:\n- Provide a brief summary of the main findings of these articles.\n\n2. Important Outcomes (with PMID, URL, and MeSH terms):\n- List the most important outcomes in bullet points and ensure that the PMID, URL, and MeSH terms mentioned for each outcome correspond to the correct article.\n\n3. Comparisons and Contrasts:\n- Highlight any key differences or similarities between the findings of these articles.\n\n4. Innovative Treatments or Methodologies:\n- Are there any innovative treatments or methodologies mentioned in these articles that could have significant impact on the field?\n\n5. Future Research and Unanswered Questions:\n- Briefly discuss any potential future research directions or unanswered questions based on the findings of these articles.\n\n6. Conclusion:\n- Sum up the main takeaways from these articles."
            # Generate text using OpenAI API
            text = generate_text(prompt)
            st.write(text)

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
        article_ids = search_pubmed(pico_query)
        if not article_ids:
            st.write("No articles found related to your PICO question.")
        else:
            st.write(f"Found {len(article_ids)} articles related to your PICO question.")
            articles_data = fetch_pubmed(article_ids)
            articles = get_mesh_terms(articles_data)
            # Generate prompt for OpenAI API
            for article in articles:
                prompt = f"Using your expert knowledge, analyze the following systematic review related to '{pico_query}':\n{article['abstract']}\n\nPlease provide a structured analysis with the following sections:\n\n1. Summary of Findings:\n- Provide a brief summary of the main findings of this article.\n\n2. Important Outcomes (with PMID: {article['id']}, URL: {article['url']}, and MeSH terms: {', '.join(article['mesh_terms'])}):\n- List the most important outcomes in bullet points and ensure that the PMID, URL, and MeSH terms mentioned for each outcome correspond to the correct article.\n\n3. Comparisons and Contrasts:\n- Highlight any key differences or similarities with other findings.\n\n4. Innovative Treatments or Methodologies:\n- Are there any innovative treatments or methodologies mentioned in this article that could have significant impact on the field?\n\n5. Future Research and Unanswered Questions:\n- Briefly discuss any potential future research directions or unanswered questions based on the findings of this article.\n\n6. Conclusion:\n- Sum up the main takeaways from this article."
                # Generate text using OpenAI API
                text = generate_text(prompt)
                st.write(text)
