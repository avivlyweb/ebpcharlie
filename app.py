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
    "retmax": 500,  # Increased from 20 to 500
    "api_key": "5cd7903972b3a715e29b76f1a15001ce9a08"
}

# Define function to generate text using OpenAI API
def generate_text(prompt, max_tokens=1000):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    message = response.choices[0].text.strip()
    return message

# Define function to search for articles using Pubmed API
def search_pubmed(query):
    params["term"] = f"{query} AND (systematic[sb] OR meta-analysis[pt])"  # Narrow down to systematic reviews or meta-analyses
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
            for article in articles:
                outcome_prompt = f"Based on your expert knowledge and the abstract of the following article related to '{user_input}', what could be the likely outcome?\n{article['abstract']}"
                outcome_text = generate_text(outcome_prompt, max_tokens=300)
                article['outcome'] = outcome_text

                # Generate prompt for OpenAI API
                prompt = f"Using your expert knowledge, analyze the following systematic review related to '{user_input}':\n{article['abstract']}\n\nPlease provide a structured analysis with the following sections:\n\n1. Summary of Findings:\n- Provide a brief summary of the main findings of this article.\n\n2. Important Outcomes (with PMID: {article['id']}, URL: {article['url']}, and MeSH terms: {', '.join(article['mesh_terms'])}):\n- List the most important outcomes in bullet points and ensure that the PMID, URL, and MeSH terms mentioned for each outcome correspond to the correct article.\n\n3. Comparisons and Contrasts:\n- Highlight any key differences or similarities with other findings.\n\n4. Innovative Treatments or Methodologies:\n- Are there any innovative treatments or methodologies mentioned in this article that could have significant impact on the field?\n\n5. Future Research and Unanswered Questions:\n- Briefly discuss any potential future research directions or unanswered questions based on the findings of this article.\n\n6. Conclusion:\n- Sum up the main takeaways from this article."
                # Generate text using OpenAI API
                text = generate_text(prompt)
                article['analysis'] = text

                # Generate a summary of the main findings
                summary_prompt = f"Based on your expert knowledge and the abstract of the following article related to '{user_input}', what are the main findings?\n{article['abstract']}"
                summary_text = generate_text(summary_prompt, max_tokens=150)
                article['summary'] = summary_text

            # Displaying the articles in a compact, summarised card view
            for article in articles:
                if st.button('More', key=article['id']):
                    st.markdown(f"**Outcome related to your clinical question**: {article['outcome']}")
                    st.markdown(f"**Complete Analysis**:")
                    st.write(article['analysis'])
                else:
                    st.markdown(f"**PMID**: {article['id']}\n**URL**: {article['url']}\n**Outcome**: {article['outcome']}\n**Summary of Findings**: {article['summary']}\n-----")
