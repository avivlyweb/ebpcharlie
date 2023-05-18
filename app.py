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
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up Pubmed API endpoint and query parameters
pubmed_endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
params = {
    "db": "pubmed",
    "retmode": "json",
    "retmax": 5,
    "api_key": os.getenv("PUBMED_API_KEY")
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

# Define function to scrape article abstracts and MeSH terms
def scrape_articles(articles):
    for article in articles:
        url = article["url"]
        html_page = urlopen(url)
        soup = BeautifulSoup(html_page, features="lxml")
        abstract = soup.find("div", {"class": "abstract-content selected"}).text
        mesh_terms = [mesh.get_text() for mesh in soup.find_all("li", {"class": "mesh-term"})]
        article["abstract"] = abstract
        article["mesh_terms"] = mesh_terms
    return articles

# Define function to convert html abstracts to text
def convert_to_text(articles):
    h = html2text.HTML2Text()
    h.ignore_links = True
    for article in articles:
        text_abstract = h.handle(article["abstract"])
        article["abstract"] = text_abstract
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
        articles = convert_to_text(articles)

        # Generate a list of PMIDs, URLs, and MeSH terms
        article_list = "\n".join([f"PMID: {article['id']}\nURL: {article['url']}\nMeSH terms: {', '.join(article['mesh_terms'])}\nAbstract: {article['abstract']}\n" for article in articles])

        # Generate prompt for OpenAI API
        prompt = f"""
        Using your expert knowledge, analyze the following systematic reviews related to '{user_input}' published between 2019-2023:\n{article_list}
        Please provide a focused and efficient analysis with the following sections:

        1. Focused Summary of Findings:
        - Provide a brief summary of these articles, focusing specifically on outcomes and findings relevant to [insert researcher's specific area of interest here].

        2. Key Findings (with PMID, URL, and MeSH terms):
        - List only the key findings from each article. Ensure that the PMID, URL, and MeSH terms for each finding correspond to the correct article.

        3. Specific Methodologies or Treatments:
        - Highlight any methodologies or treatments mentioned in these articles that align with [insert researcher's specific methodology or treatment of interest here].

        4. Direct Comparisons:
        - Provide direct comparisons of [insert specific metrics or outcome measures of interest here] across these articles.

        5. Future Research Directions:
        - Discuss potential future research directions related to [insert researcher's specific area of study here] based on the findings of these articles.

        6. Conclusion:
        - Sum up the key takeaways from these articles that are directly relevant to [insert researcher's specific area of interest here].
        """
        
        # Generate summary using OpenAI API
        summary = generate_text(prompt)
        st.subheader("Summary of Findings")
        st.write(summary)

        # Display article abstracts
        st.subheader("Article Abstracts")
        for article in articles:
            st.write(f"PMID: {article['id']}")
            st.write(f"URL: {article['url']}")
            st.write(f"MeSH Terms: {', '.join(article['mesh_terms'])}")
            st.write(article["abstract"])
            st.write("\n\n\n")
