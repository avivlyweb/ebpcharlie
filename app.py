import os
import openai
import requests
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

def generate_text(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1000,
        temperature=0.7,
    )
    message = response.choices[0].text.strip()
    return message

def search_pubmed(query):
    params["term"] = query
    response = requests.get(pubmed_search_endpoint, params=params)
    data = response.json()
    return data["esearchresult"]["idlist"]

def fetch_pubmed(article_ids):
    params = {
        "db": "pubmed",
        "retmode": "xml",
        "id": ",".join(article_ids)
    }
    response = requests.get(pubmed_fetch_endpoint, params=params)
    return BeautifulSoup(response.content, "xml")

def get_article_info(article):
    article_id = article.PMID.text
    title = article.ArticleTitle.text
    abstract = article.Abstract.AbstractText.text if article.Abstract else "No abstract available"
    mesh_terms = [keyword.text for keyword in article.findAll("Keyword")]
    url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}"
    return {"id": article_id, "title": title, "abstract": abstract, "mesh_terms": mesh_terms, "url": url}

st.title("Evidence-Based Practice Charlie")
st.write("This is an AI tool that assists in finding evidence-based information related to your clinical questions using PICO (Patient, Intervention, Comparison, Outcome). It also provides structured analysis of the articles found.")

patient = st.text_input("Patient, Population, or Problem")
intervention = st.text_input("Intervention")
comparison = st.text_input("Comparison")
outcome = st.text_input("Outcome")

pico_query = f"{patient} AND {intervention} AND {comparison} AND {outcome}"
user_input = f"Patient: {patient}, Intervention: {intervention}, Comparison: {comparison}, Outcome: {outcome}"

if st.button("Search with EBPcharlie"):
    if not all([patient, intervention, outcome]):
        st.error("Please complete PICO to search for articles.")
    else:
        article_ids = search_pubmed(pico_query)
        soup = fetch_pubmed(article_ids)
        articles = [get_article_info(article) for article in soup.find_all("PubmedArticle")]

        if not articles:
            st.write("No articles found related to your PICO.")
        else:
            for article in articles:
                prompt = f"Using your expert knowledge, analyze the following systematic review related to '{user_input}' published between 2019-2023:\n\nPMID: {article['id']}\nURL: {article['url']}\nMeSH Terms: {', '.join(article['mesh_terms'])}\nAbstract: {article['abstract']}\n\nPlease provide a structured analysis with the following sections:\n\n1. Summary of Findings:\n- Provide a brief summary of the main findings of this article.\n\n2. Important Outcomes (with PMID, URL, and MeSH terms):\n- List the most important outcomes in bullet points and ensure that the PMID, URL, and MeSH terms mentioned for each outcome correspond to the correct article.\n\n3. Comparisons and Contrasts:\n- Highlight any key differences or similarities between the findings of this article and others.\n\n4. Innovative Treatments or Methodologies:\n- Are there any innovative treatments or methodologies mentioned in this article that could have significant impact on the field?\n\n5. Future Research and Unanswered Questions:\n- Briefly discuss any potential future research directions or unanswered questions based on the findings of this article.\n\n6. Conclusion:\n- Sum up the main takeaways from this article."
                summary = generate_text(prompt)
                st.subheader(f"Article Title: {article['title']}")
                st.write(summary)
