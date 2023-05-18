import os
import openai
import requests
import json
import streamlit as st
from urllib.request import urlopen
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

# App Heading and Description
st.markdown(
    """
    # EBPCharlie: An AI-Powered Literature Review Assistant

    EBPCharlie utilizes AI technology to help automate and accelerate the literature review process for researchers. 
    By integrating PubMed API and OpenAI's GPT-3, EBPCharlie can search for scientific articles based on a given 
    PICO (Patient/Problem, Intervention, Comparison, Outcome) framework, extract relevant information from those articles,
    and provide a structured summary of the findings.
    
    Simply input your PICO criteria, and EBPCharlie will do the rest!
    """
)

# Define function to generate text using OpenAI API
def generate_text(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.7,
    )
    message = response.choices[0].text
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

# Get user PICO input
patient = st.text_input("Patient, Population, or Problem")
intervention = st.text_input("Intervention")
comparison = st.text_input("Comparison")
outcome = st.text_input("Outcome")

# Search for articles using Pubmed API
if st.button("Search with EBPcharlie"):
    if not patient or not intervention or not outcome:
        st.error("Please enter Patient, Intervention, and Outcome to search for articles.")
    else:
        user_input = f"{patient} AND {intervention} AND {outcome} AND {comparison}"
        article_ids = search_pubmed(user_input)
        articles_data = fetch_pubmed(article_ids)
        articles = get_mesh_terms(articles_data)
        st.write(f"Found {len(articles)} articles related to your clinical question.")

        # Generate a list of PMIDs, URLs and MeSH terms
        article_list = "\n".join([f"PMID: {article['id']} URL: {article['url']} MeSH Terms: {', '.join(article['mesh_terms'])}" for article in articles])

        # Generate prompt for OpenAI API
        prompt = f"Using your expert knowledge, analyze the following articles related to the PICO question '{user_input}' published recently:\n{article_list}\n\nPlease provide a structured analysis with the following sections:\n\n1. Summary of Findings:\n- Provide a brief summary of the main findings of these articles.\n\n2. Important Outcomes (with PMID, URL, and MeSH terms):\n- List the most important outcomes in bullet points and ensure that the PMID, URL, and MeSH terms mentioned for each outcome correspond to the correct article.\n\n3. Comparisons and Contrasts:\n- Highlight any key differences or similarities between the findings of these articles.\n\n4. Innovative Treatments or Methodologies:\n- Are there any innovative treatments or methodologies mentioned in these articles that could have significant impact on the field?\n\n5. Future Research and Unanswered Questions:\n- Briefly discuss any potential future research directions or unanswered questions based on the findings of these articles.\n\n6. Conclusion:\n- Sum up the main takeaways from these articles."

        # Generate summary using OpenAI API
        summary = generate_text(prompt)
        st.subheader("Summary of Findings")
        st.write(summary)

        # Display article abstracts and MeSH terms
        st.subheader("Article Abstracts and MeSH terms")
        for article in articles:
            st.write(f"PMID: {article['id']}")
            st.write(f"URL: {article['url']}")
            st.write(f"MeSH terms: {', '.join(article['mesh_terms'])}")
            st.write(article["abstract"])
            st.write("\n\n\n")
