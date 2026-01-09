import streamlit as st
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from google import genai


load_dotenv()
client = genai.Client()

URI=os.getenv("NEO4J_URI")
USERNAME=os.getenv("NEO4J_USERNAME")
PASSWORD=os.getenv("NEO4J_PASSWORD")

with GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD)) as driver:
    driver.verify_connectivity()
    print("Neo4j Connection established!")

    user_question = input("Ask anything: ")
    
    prompt = f"""
    You are an AI that converts natural language questions into Cypher queries.

    IMPORTANT RULES (follow strictly):
    - Output ONLY the Cypher query.
    - Follow the given schema, relationships, and properties. 
    - No explanation.
    - No markdown.
    - No code blocks.
    - No extra text.
    - No backticks.
    - Return plain Cypher only.
    - The Cypher query must return ONLY plain text (string) values.
    No nodes, no maps, no lists of objects, no JSON structures.
    The last line MUST be a RETURN <string property> expression.
    Under no circumstances should the query return nodes or objects.

    Schema:
    (:Movie)-[:IN_GENRE]->(:Genre)
    (:Person)-[:DIRECTED]->(:Movie)
    (:Person)-[:ACTED_IN]->(:Movie)

    Relationships:
    "ACTED_IN"
    "DIRECTED"
    "PRODUCED"
    "WROTE"
    "FOLLOWS"
    "REVIEWED"

    Properties:
    "Movie.title"
    "Movie.released"
    "Movie.tagline"
    "Person.name"
    "Person.born"

    User question: "{user_question}"
    Return ONLY the Cypher query.
    """

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)

    cypher_query = response.text.strip("```").strip()
    print("Generated Cypher:\n", cypher_query)

    with driver.session() as session:
        result = session.run(cypher_query)

        # Get all records as list of dicts
        data = result.data()
        # print("Raw Output:", data)

        # If the query returns only one column, extract it automatically
        if data and len(data[0].keys()) == 1:
            key = list(data[0].keys())[0]
            values = [row[key] for row in data]
        else:
            # Multi-column results stay as dicts
            values = data  

        print("Output: ", values)

with GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD)) as driver:
    
    prompt = f"""
    You are an AI assistant. Summarize database results concisely.
    User question: "{user_question}"
    Database result: "{values}"
    Write all the values with short, clear explanation (1-2 lines).
    """

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    llm_output = response.text.strip("```").strip()
    print("Answer: ", llm_output)