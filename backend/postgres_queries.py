import psycopg2
import os
import requests

"""
This file contains the methods involved in querying the postgres database to retrieve initial search results. These methods are primarily
used in basic_searches.py to retrieve results.
"""

def execute_query(app, query, params):
    """
    Utility function to execute a query and fetch results from the database.
    Handles connection and cursor management.
    """
    try:
        with psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),            
            database=os.getenv('DB_NAME'),
            sslmode='disable'       
        ) as connection:
            app.logger.debug(f"Executing query: {query} with params: {params}")
            with connection.cursor() as cursor:
                cursor.execute(query, params)                
                results = cursor.fetchall()
                app.logger.info(f"Query executed successfully, returned {len(results)} results")
                return results        
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")
        return None

def fetch_last_known_institutions(app, raw_id: str) -> list:
    """
    Make a request to the OpenAlex API to fetch the last known institutions for a given author id.
    The parameter raw_id is the id in the authors table, which has the format "https://openalex.org/author/1234",
    but we only need the last part of the id, i.e., "1234".
    """
    try:
        id = raw_id.split('/')[-1]
        response = requests.get(f"https://api.openalex.org/authors/{id}")
        data = response.json()
        return data.get("last_known_institutions", [])
    except Exception as e:
        app.logger.error(f"Error fetching last known institutions for id {id}: {str(e)}")
        return []

def get_author_ids(app, author_name):  
    """
    Queries the database in order to retrieve the author ID for a given author name
    """
    app.logger.debug(f"Getting author IDs for: {author_name}")
    query = """SELECT get_author_ids(%s);"""
    results = execute_query(app, query, (author_name,))
    if results:
        app.logger.info(f"Found author IDs for {author_name}")
        return results[0][0]
    app.logger.warning(f"No author IDs found for {author_name}")
    return None

def get_institution_id(app, institution_name):
    """
    Queries the database to retrieve the institution ID for the given institution name
    """
    app.logger.debug(f"Getting institution ID for: {institution_name}")
    query = """SELECT get_institution_id(%s);"""
    results = execute_query(app, query, (institution_name,))
    if results:
        if results[0][0] == {}:
            app.logger.warning(f"No institution ID found for {institution_name}")
            return None
        app.logger.info(f"Found institution ID for {institution_name}")
        return results[0][0]['institution_id']
    app.logger.warning(f"Query returned no results for institution {institution_name}")
    return None

def search_by_author_institution_topic(app, author_name, institution_name, topic_name):
    """
    Performs the query to the database when all 3 fields are filled in (author, institution, and topic)
    """
    app.logger.debug(f"Searching by author, institution, and topic: {author_name}, {institution_name}, {topic_name}")
    author_ids = get_author_ids(app, author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    
    author_id = author_ids[0]['author_id']
    app.logger.debug(f"Using author ID: {author_id}")

    institution_id = get_institution_id(app, institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT search_by_author_institution_topic(%s, %s, %s);"""
    results = execute_query(app, query, (author_id, institution_id, topic_name))
    if results:
        app.logger.info("Found results for author-institution-topic search")
        return results[0][0]
    app.logger.warning("No results found for author-institution-topic search")
    return None

def search_by_author_institution(app, author_name, institution_name):
    """
    Performs the query to the database when only the author and institution fields are filled in
    """
    app.logger.debug(f"Searching by author and institution: {author_name}, {institution_name}")
    author_ids = get_author_ids(app, author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    
    author_id = author_ids[0]['author_id']
    app.logger.debug(f"Using author ID: {author_id}")

    institution_id = get_institution_id(app, institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT search_by_author_institution(%s, %s);"""
    results = execute_query(app, query, (author_id, institution_id))
    if results:
        app.logger.info("Found results for author-institution search")
        return results[0][0]
    app.logger.warning("No results found for author-institution search")
    return None

def search_by_institution_topic(app, institution_name, topic_name):
    """
    Performs the query to the database when only the institution and topic fields are filled in
    """
    app.logger.debug(f"Searching by institution and topic: {institution_name}, {topic_name}")
    institution_id = get_institution_id(app, institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None

    query = """SELECT search_by_institution_topic(%s, %s);"""
    results = execute_query(app, query, (institution_id, topic_name))
    if results:
        app.logger.info("Found results for institution-topic search")
        return results[0][0]
    app.logger.warning("No results found for institution-topic search")
    return None

def search_by_author_topic(app, author_name, topic_name):
    """
    Performs the query to the database when only the author and topic fields are filled in
    """
    app.logger.debug(f"Searching by author and topic: {author_name}, {topic_name}")
    author_ids = get_author_ids(app, author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    
    author_id = author_ids[0]['author_id']
    app.logger.debug(f"Using author ID: {author_id}")

    query = """SELECT search_by_author_topic(%s, %s);"""
    results = execute_query(app, query, (author_id, topic_name))
    if results:
        app.logger.info("Found results for author-topic search")
        return results[0][0]
    app.logger.warning("No results found for author-topic search")
    return None

def search_by_topic(app, topic_name):
    """
    Performs the query to the database when only the topic field is filled in
    """
    app.logger.debug(f"Searching by topic: {topic_name}")
    query = """SELECT search_by_topic(%s);"""
    results = execute_query(app, query, (topic_name,))
    if results:
        app.logger.info(f"Found results for topic search: {topic_name}")
        return results[0][0]
    app.logger.warning(f"No results found for topic: {topic_name}")
    return None

def search_by_institution(app, institution_name, id=None):
    """
    Performs the query to the database when only the institution field is filled in
    The id parameter allows the search to be performed with an institution ID rather than an institution name, and may be left blank
    """
    app.logger.debug(f"Searching by institution: {institution_name}")
    if not id:
        institution_id = get_institution_id(app, institution_name)
        if institution_id is None:
            app.logger.warning(f"No institution ID found for {institution_name}")
            return None
    else:
        institution_id = id
    query = """SELECT search_by_institution(%s);"""
    results = execute_query(app, query, (institution_id,))
    if results:
        app.logger.info(f"Found results for institution search: {institution_name}")
        return results[0][0]
    app.logger.warning(f"No results found for institution: {institution_name}")
    return None

def search_by_author(app, author_name, id=None):
    """
    Performs the query to the database when only the author field is filled in
    The id parameter allows the search to be performed with an author ID rather than an author name, and may be left blank
    """
    app.logger.debug(f"Searching by author: {author_name}")
    if not id:
        author_ids = get_author_ids(app, author_name)
        if not author_ids:
            app.logger.warning(f"No author IDs found for {author_name}")
            return None
        author_id = author_ids[0]['author_id']
    else:
        author_id = id

    app.logger.debug(f"Using author ID: {author_id}")

    query = """SELECT search_by_author(%s);"""
    results = execute_query(app, query, (author_id,))
    if results:
        app.logger.info(f"Found results for author search: {author_name}")
        return results[0][0]
    app.logger.warning(f"No results found for author: {author_name}")
    return None