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
patient = st.text_input("Patient, Population, or Problem", key="patient")
intervention = st.text_input("Intervention", key="intervention")
comparison = st.text_input("Comparison", key="comparison")
outcome = st.text_input("Outcome", key="outcome")

pico_query = f"{patient} AND {intervention} AND {comparison} AND {outcome}"

if st.button("Search PICO"):
    if not all([patient, intervention, comparison, outcome]):
        st.error("Please fill in all PICO components.")
    else:
        pico_articles = search_pubmed(pico_query)
        pico_articles = fetch_pubmed(pico_articles)
        pico_articles = get_article_info(pico_articles)
        st.write(f"Found {len(pico_articles)} articles related to your PICO question.")
        
        for article in pico_articles:
            prompt = f"Analyse the following article related to the clinical question '{user_input}' with PICO components (Patient: '{patient}', Intervention: '{intervention}', Comparison: '{comparison}', Outcome: '{outcome}') :\n\nPMID: {article['id']}\nURL: {article['url']}\nMeSH Terms: {', '.join(article['mesh_terms'])}\nStudy Type: {', '.join(article['study_type'])}\nAbstract: {article['abstract']}\n\nPlease provide a structured analysis with the following sections:\n\n1. Summary of Findings:\n- Provide a brief summary of the main findings of this article.\n\n2. Important Outcomes (with PMID, URL, and MeSH terms):\n- List the most important outcomes in bullet points and ensure that the PMID, URL, and MeSH terms mentioned for each outcome correspond to the correct article.\n\n3. Comparisons and Contrasts:\n- Highlight any key differences or similarities between the findings of these articles.\n\n4. Innovative Treatments or Methodologies:\n- Are there any innovative treatments or methodologies mentioned in these articles that could have significant impact on the field?\n\n5. Future Research and Unanswered Questions:\n- Briefly discuss any potential future research directions or unanswered questions based on the findings of these articles.\n\n6. Conclusion:\n- Sum up the main takeaways from this article."
            summary = generate_text(prompt)
            st.markdown(f"### Summary of Findings for PMID: {article['id']}")
            st.markdown(f"**{summary}**")
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
            st.markdown(f"### Summary of Findings for PMID: {article['id']}")
            st.markdown(f"**{summary}**")
            st.write("\n\n\n")
