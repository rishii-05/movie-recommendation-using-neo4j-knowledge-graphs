import streamlit as st
from neo4j import GraphDatabase
import pandas as pd

# --- NEO4J CONNECTION DETAILS ---
URI = ""your_uri_here""
USER = "neo4j"
# IMPORTANT: Replace with your password
PASSWORD = ""your_password_here"" 

# --- HELPER FUNCTIONS ---

@st.cache_resource
def get_driver():
    """Establishes connection to Neo4j and returns the driver object."""
    try:
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        driver.verify_connectivity()
        print("Connected to Neo4j")
        return driver
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {e}")
        return None

def run_query(driver, query, params={}):
    """Runs a Cypher query and returns the results as a Pandas DataFrame."""
    with driver.session() as session:
        result = session.run(query, params)
        return pd.DataFrame([r.data() for r in result])

# --- DEFINE THE QUERIES ---

# Basic Semantic Query (Shared Actors & Genres)
basic_rec_query = """
MATCH (m:Movie) WHERE toLower(m.title) = toLower($title)
MATCH (m)-[:HAS_GENRE]->(g:Genre)
MATCH (rec:Movie)-[:HAS_GENRE]->(g)
WHERE m <> rec
WITH m, rec, count(g) AS sharedGenres
MATCH (m)<-[:ACTED_IN]-(a:Actor)-[:ACTED_IN]->(rec)
WITH rec, sharedGenres, count(a) AS sharedActors
RETURN rec.title AS Recommendation, sharedGenres, sharedActors
ORDER BY sharedActors DESC, sharedGenres DESC
LIMIT 10
"""

# --- BUILD THE STREAMLIT APP ---

st.title("🎬 Movie Recommendation Engine")
st.write("Powered by Neo4j Knowledge Graph")

# Get the Neo4j driver
driver = get_driver()

if driver:
    # Get user input
    movie_title = st.text_input("Enter a movie title you like (e.g., Inception, The Matrix, Avatar):")

    if movie_title:
        # Check that the movie exists in the DB
        movie_exists_df = run_query(driver, "MATCH (m:Movie) WHERE toLower(m.title) = toLower($title) RETURN m.title AS title", {'title': movie_title})

        if movie_exists_df.empty:
            st.error(f"Movie '{movie_title}' not found in the database. Check capitalization and spelling.")
        else:
            # --- Basic Recommendations ---
            st.subheader("Basic Recommendations (Shared Actors & Genres)")
            with st.spinner("Finding recommendations based on actors and genres..."):
                basic_df = run_query(driver, basic_rec_query, {'title': movie_title})
                if basic_df.empty:
                    st.write("No basic recommendations found.")
                else:
                    basic_df.index += 1
                    st.dataframe(basic_df, use_container_width=True)
            

    # Clean up the driver connection when the app closes
    # This part might not be strictly necessary for Streamlit, but it's good practice.
    # driver.close() # Caching handles this