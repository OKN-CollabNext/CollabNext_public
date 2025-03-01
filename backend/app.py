import os
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import psycopg2
from os.path import exists  # <--this import exists from os.path

# -----------------------------------------------------------------------------
# As per my usage I have an absolute base directory for data files to put
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------------------------------------
# Load up the environment variables in the loop from .env
# -----------------------------------------------------------------------------
try:
    DB_HOST = os.environ["DB_HOST"]
    DB_PORT = int(os.environ["DB_PORT"])
    DB_NAME = os.environ["DB_NAME"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    API = os.getenv("DB_API")
except:
    logger = logging.getLogger(__name__)
    logger.warning("Using Local Variables")
    load_dotenv(dotenv_path=".env")
    API = os.getenv("DB_API")

# Global variable needs to be kept for the SPARQL endpoint
SEMOPENALEX_SPARQL_ENDPOINT = "https://semopenalex.org/sparql"

app = Flask(__name__, static_folder="build", static_url_path="/")
CORS(app)


def setup_logger():
    """Configure logging with rotating file handlers for all levels."""
    log_path = "/home/LogFiles" if os.environ.get(
        "WEBSITE_SITE_NAME") else "logs"
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handlers = {
        "debug": RotatingFileHandler(os.path.join(log_path, "debug.log"), maxBytes=15 * 1024 * 1024, backupCount=3),
        "info": RotatingFileHandler(os.path.join(log_path, "info.log"), maxBytes=15 * 1024 * 1024, backupCount=3),
        "warning": RotatingFileHandler(os.path.join(log_path, "warning.log"), maxBytes=10 * 1024 * 1024, backupCount=3),
        "error": RotatingFileHandler(os.path.join(log_path, "error.log"), maxBytes=5 * 1024 * 1024, backupCount=3),
        "critical": RotatingFileHandler(os.path.join(log_path, "critical.log"), maxBytes=2 * 1024 * 1024, backupCount=3),
    }

    handlers["debug"].setLevel(logging.DEBUG)
    handlers["info"].setLevel(logging.INFO)
    handlers["warning"].setLevel(logging.WARNING)
    handlers["error"].setLevel(logging.ERROR)
    handlers["critical"].setLevel(logging.CRITICAL)

    for h in handlers.values():
        h.setFormatter(formatter)

    logger_ = logging.getLogger("flask.app")
    logger_.setLevel(logging.DEBUG)
    for h in handlers.values():
        logger_.addHandler(h)

    return logger_


# Watch and initialize the logger
logger = setup_logger()
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)

# -----------------------------------------------------------------------------
# Custom exception is necessary for non-200 HTTP responses
# -----------------------------------------------------------------------------


class SomeCustomError(Exception):
    pass


def execute_query(query, params):
    """
    We definitely know more about the utility function than we do about executing a query and fetching the results from the database. That's why we need to handle the connection and the management of the cursor.
    """
    try:
        with psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            sslmode="disable",
        ) as connection:
            app.logger.debug(f"Executing query: {query} with params: {params}")
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                app.logger.info(
                    f"Query executed successfully, returned {len(results)} results")
                return results
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")
        return None


def fetch_last_known_institutions(raw_id: str) -> list:
    """
    Makes a question in my opinion, to send a request to the OpenAlex Application Programming Interface which is the way forward to "fetch" the last known institutions for a given author ID.
    """
    try:
        just_id = raw_id.split("/")[-1]
        response = requests.get(f"https://api.openalex.org/authors/{just_id}")
        if response.status_code != 200:
            raise SomeCustomError(
                f"OpenAlex API returned status code {response.status_code}")
        data = response.json()
        return data.get("last_known_institutions", [])
    except SomeCustomError:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching last known institutions for id {just_id}: {str(e)}")
        return []


def get_author_ids(author_name):
    """
    Get author IDs out of the database stored function called `get_author_id`.
    """
    app.logger.debug(f"Getting author IDs for: {author_name}")
    query = """SELECT get_author_id(%s);"""
    results = execute_query(query, (author_name,))
    if results:
        app.logger.info(f"Found author IDs for {author_name}")
        return results[0][0]
    app.logger.warning(f"No author IDs found for {author_name}")
    return None


def get_institution_id(institution_name):
    """
    Get institution ID out of the database stored function called `get_institution_id`.
    """
    app.logger.debug(f"Getting institution ID for: {institution_name}")
    query = """SELECT get_institution_id(%s);"""
    results = execute_query(query, (institution_name,))
    if results:
        if results[0][0] == {}:
            app.logger.warning(
                f"No institution ID found for {institution_name}")
            return None
        app.logger.info(f"Found institution ID for {institution_name}")
        return results[0][0]["institution_id"]
    app.logger.warning(
        f"Query returned no results for institution {institution_name}")
    return None


# ----------------------------------------------------------------------
# Search functions that can call the stored procedures that are "located" in the Postgres DB.
# ----------------------------------------------------------------------
def search_by_author(author_name):
    """
    We only searching using the name of the author which calls the search_by_author in the database.
    """
    app.logger.debug(f"Searching by author: {author_name}")
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    author_id = author_ids[0]['author_id']
    app.logger.debug(f"Using author ID: {author_id}")
    query = """SELECT search_by_author(%s);"""
    results = execute_query(query, (author_id,))
    if results:
        app.logger.info(f"Found results for author search: {author_name}")
        return results[0][0]
    app.logger.warning(f"No results found for author: {author_name}")
    return None


def search_by_author_institution_topic(author_name, institution_name, topic_name):
    """
    Furthermore, we search with the institution and with the author and the topic so that we can call the search_by_author_institution_Topic in the database.
    """
    app.logger.debug(
        f"Searching by author, institution, and topic: {author_name}, {institution_name}, {topic_name}"
    )
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    author_id = author_ids[0]["author_id"]
    app.logger.debug(f"Using author ID: {author_id}")
    institution_id = get_institution_id(institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None
    query = """SELECT search_by_author_institution_topic(%s, %s, %s);"""
    results = execute_query(query, (author_id, institution_id, topic_name))
    if results:
        app.logger.info("Found results for author-institution-topic search")
        return results[0][0]
    app.logger.warning("No results found for author-institution-topic search")
    return None


def search_by_author_institution(author_name, institution_name):
    """
    Then we can search with the institution & author -> call then the search_by_author_insitution in the database.
    """
    app.logger.debug(
        f"Searching by author and institution: {author_name}, {institution_name}"
    )
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    author_id = author_ids[0]["author_id"]
    app.logger.debug(f"Using author ID: {author_id}")
    institution_id = get_institution_id(institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None
    query = """SELECT search_by_author_institution(%s, %s);"""
    results = execute_query(query, (author_id, institution_id))
    if results:
        app.logger.info("Found results for author-institution search")
        return results[0][0]
    app.logger.warning("No results found for author-institution search")
    return None


def search_by_institution_topic(institution_name, topic_name):
    """
    I will get the search via the institutione & the topic -> then, I can call the search_by_institution_topic in the database!
    """
    app.logger.debug(
        f"Searching by institution and topic: {institution_name}, {topic_name}")
    institution_id = get_institution_id(institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None
    query = """SELECT search_by_institution_topic(%s, %s);"""
    results = execute_query(query, (institution_id, topic_name))
    if results:
        app.logger.info("Found results for institution-topic search")
        return results[0][0]
    app.logger.warning("No results found for institution-topic search")
    return None


def search_by_author_topic(author_name, topic_name):
    """
    Searching via author and topic, this function calls search_by_author_topic in the database.
    """
    app.logger.debug(
        f"Searching by author and topic: {author_name}, {topic_name}")
    author_ids = get_author_ids(author_name)
    if not author_ids:
        app.logger.warning(f"No author IDs found for {author_name}")
        return None
    author_id = author_ids[0]["author_id"]
    app.logger.debug(f"Using author ID: {author_id}")
    query = """SELECT search_by_author_topic(%s, %s);"""
    results = execute_query(query, (author_id, topic_name))
    if results:
        app.logger.info("Found results for author-topic search")
        return results[0][0]
    app.logger.warning("No results found for author-topic search")
    return None


def search_by_topic(topic_name):
    """
    Searching only with the topic, this function called the search_by_topic in the database.
    """
    app.logger.debug(f"Searching by topic: {topic_name}")
    query = """SELECT search_by_topic(%s);"""
    results = execute_query(query, (topic_name,))
    if results:
        app.logger.info(f"Found results for topic search: {topic_name}")
        return results[0][0]
    app.logger.warning(f"No results found for topic: {topic_name}")
    return None


def search_by_institution(institution_name):
    """
    Searching only with the institution, this function called search_by_institution in the database.
    """
    app.logger.debug(f"Searching by institution: {institution_name}")
    institution_id = get_institution_id(institution_name)
    if institution_id is None:
        app.logger.warning(f"No institution ID found for {institution_name}")
        return None
    query = """SELECT search_by_institution(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        app.logger.info(
            f"Found results for institution search: {institution_name}")
        return results[0][0]
    app.logger.warning(f"No results found for institution: {institution_name}")
    return None


# -----------------------------------------------------------------------------
# While Flask has inbuilt logging with 5 levels of severity, we don't have any such thing for CSV files so we load them with absolute paths
# -----------------------------------------------------------------------------
institutions_csv_path = os.path.join(BASE_DIR, "institutions.csv")
subfields_csv_path = os.path.join(BASE_DIR, "subfields.csv")
with open(institutions_csv_path, "r") as file:
    autofill_inst_list = file.read().split(",\n")
with open(subfields_csv_path, "r") as file:
    autofill_subfields_list = file.read().split("\n")
SUBFIELDS = True
if not SUBFIELDS:
    keywords_csv_path = os.path.join(BASE_DIR, "keywords.csv")
    with open(keywords_csv_path, "r") as fil:
        autofill_topics_list = fil.read().split("\n")


@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f"404 error: {request.url}")
    return send_from_directory(app.static_folder, "index.html")


@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"500 error: {str(e)}")
    """ Internal server error is probably the least descriptive error that I have ever ever heard of. """
    return "Internal Server Error", 500


@app.route("/initial-search", methods=["POST"])
def initial_search():
    """
    The API call is what we do for the searches we make from the user. Once the user makes a search we delete it and call "other" methods depending on what the user inputted.

    I am not the person to expect this, that the frontend passes this in:
      organization (string)
      researcher   (string)
      topic        (string)
      type         (string) (for now, always HBCU)

    Returns a dictionary with the following:
      metadata : ...
      graph    : { nodes: [], edges: [] }
      list     : ...
    """
    institution = request.json.get("organization", "")
    researcher = request.json.get("researcher", "")
    researcher = researcher.title()  # Title-case the researcher name
    type_ = request.json.get("type", "")
    topic = request.json.get("topic", "")

    app.logger.info(
        f"Received search request - Institution: {institution}, "
        f"Researcher: {researcher}, Topic: {topic}, Type: {type_}"
    )

    try:
        if institution and researcher and topic:
            results = get_institution_researcher_subfield_results(
                institution, researcher, topic
            )
        elif institution and researcher:
            results = get_institution_and_researcher_results(
                institution, researcher)
        elif institution and topic:
            results = get_institution_and_subfield_results(institution, topic)
        elif researcher and topic:
            results = get_researcher_and_subfield_results(researcher, topic)
        elif topic:
            results = get_subfield_results(topic)
        elif institution:
            results = get_institution_results(institution)
        elif researcher:
            results = get_researcher_result(researcher)
        else:
            results = None

        if not results:
            app.logger.warning("Search returned no results")
            return {}

        app.logger.info("Search completed successfully")
        return results
    except Exception as e:
        app.logger.critical(f"Critical error during search: {str(e)}")
        return {"error": "An unexpected error occurred"}

# -----------------------------------------------------------------------------
# The rest of the `get_institution_results`, `get_subfield_results`, etc.
# they do remain unchanged except for, we might add absolute path logic for the
# JSON loads which means that we have to integrate the GET functions with our tests.
# What we have to do is look at the `get_default_graph` as well as the `search_topic_space`
# below and when we do we will see that our Dockerized application is functioning
# correctly in accordance with the application of the database.
# -----------------------------------------------------------------------------
# Thus follows the identical functions, we're not modifying the wrappers we're modifying
# what we expect which is to see that we just need to change the test results in
# each test function platform variable to mock get_researcher_result, etc.


def get_researcher_result(researcher):
    """
    Response comes faster to a direct query of one paragraph than 13 long messages.
    That's correct that the user only inputs a researcher, it's just the only
    question that we have is is the user going to only input one researcher and then
    how is our test function utilizing the existing database to get the result? If we're using the database then
    We should be able to default to SPARQL and write a test case for when the user..
    the researcher is not in the database.
    """
    data = search_by_author(researcher)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_author_metadata_sparql(researcher)
        if data == {}:
            app.logger.warning("No results found in SPARQL for researcher")
            return {}
        topic_list, graph = list_given_researcher_institution(
            data['oa_link'], data['name'], data['current_institution']
        )
        return {"metadata": data, "graph": graph, "list": topic_list}
    app.logger.debug("Processing database results for researcher")
    list_ = []
    metadata = data['author_metadata']
    """ I normalized the fields for the front-end """
    if metadata['orcid'] is None:
        metadata['orcid'] = ''
    metadata['work_count'] = metadata['num_of_works']
    metadata['current_institution'] = metadata['last_known_institution']
    metadata['cited_by_count'] = metadata['num_of_citations']
    metadata['oa_link'] = metadata['openalex_url']
    institution_url = ""
    if metadata['last_known_institution'] is None:
        app.logger.debug("Fetching last known institutions from OpenAlex")
        institution_object = fetch_last_known_institutions(metadata['oa_link'])
        if institution_object == []:
            app.logger.warning("No last known institution found")
            last_known_institution = ""
        else:
            institution_object = institution_object[0]
            last_known_institution = institution_object['display_name']
            institution_url = institution_object['id']
    else:
        last_known_institution = metadata['last_known_institution']
    metadata['current_institution'] = last_known_institution
    metadata['institution_url'] = institution_url
    app.logger.debug("Building graph structure")
    nodes = []
    edges = []
    """ The node for the Institution """
    nodes.append({
        'id': last_known_institution,
        'label': last_known_institution,
        'type': 'INSTITUTION'
    })
    """ The edge to the Institution from the Author """
    edges.append({
        'id': f"""{metadata['openalex_url']}-{last_known_institution}""",
        'start': metadata['openalex_url'],
        'end': last_known_institution,
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    })
    """ The node for the Author """
    nodes.append({
        'id': metadata['openalex_url'],
        'label': researcher,
        "type": "AUTHOR"
    })
    for entry in data['data']:
        topic = entry['topic']
        num_works = entry['num_of_works']
        list_.append((topic, num_works))
        """ The Node for the Topic """
        nodes.append({'id': topic, 'label': topic, 'type': "TOPIC"})
        number_id = topic + ":" + str(num_works)
        """ The Node for the Number """
        nodes.append({'id': number_id, 'label': num_works, 'type': "NUMBER"})
        """ The topic's Edges """
        edges.append({
            'id': f"""{metadata['openalex_url']}-{topic}""",
            'start': metadata['openalex_url'],
            'end': topic,
            "label": "researches",
            "start_type": "AUTHOR",
            "end_type": "TOPIC"
        })
        edges.append({
            'id': f"""{metadata['openalex_url']}-{number_id}""",
            'start': topic,
            'end': number_id,
            "label": "number",
            "start_type": "TOPIC",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    return {"metadata": metadata, "graph": graph, "list": list_}


def get_institution_results(institution):
    """
    These are all correlated, we could do something like denormalization for our
    test cases. Here we have to get the results when the user inputs a research
    object as well as a subfield..thus we use the database to get the result and then
    we default to SPARQL if the researcher is not in the database.
    """
    data = search_by_institution(institution)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_institution_metadata_sparql(institution)
        if data == {}:
            app.logger.warning("No results found in SPARQL for institution")
            return {}
        topic_list, graph = list_given_institution(
            data['ror'], data['name'], data['oa_link']
        )
        return {"metadata": data, "graph": graph, "list": topic_list}
    app.logger.debug("Processing database results for institution")
    list_ = []
    metadata = data['institution_metadata']
    # Field needs to be Remapped
    metadata['homepage'] = metadata['url']
    metadata['works_count'] = metadata['num_of_works']
    metadata['name'] = metadata['institution_name']
    metadata['cited_count'] = metadata['num_of_citations']
    metadata['oa_link'] = metadata['openalex_url']
    metadata['author_count'] = metadata['num_of_authors']
    nodes = []
    edges = []
    institution_id = metadata['openalex_url']
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    for entry in data['data']:
        subfield = entry['topic_subfield']
        number = entry['num_of_authors']
        list_.append((subfield, number))
        nodes.append({'id': subfield, 'label': subfield, 'type': "TOPIC"})
        number_id = subfield + ":" + str(number)
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({
            'id': f"""{institution_id}-{subfield}""",
            'start': institution_id,
            'end': subfield,
            "label": "researches",
            "start_type": "INSTITUTION",
            "end_type": "TOPIC"
        })
        edges.append({
            'id': f"""{subfield}-{number_id}""",
            'start': subfield,
            'end': number_id,
            "label": "number",
            "start_type": "TOPIC",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    return {"metadata": metadata, "graph": graph, "list": list_}


def get_subfield_results(topic):
    """
    Main get subfield results function. Every get function seems to be bundled with,
    what happens when the user inputs an institution and subfield. Then we do,
    we usually use the database to get the result and then default to SPARQL if the
    institution is not in the database. However, since we're only handling the search for the subfield only from the database we don't need to fall back to SPARQL at the moment at least.
    """
    data = search_by_topic(topic)
    if data is None:
        app.logger.warning(f"No results found for topic: {topic}")
        return {"metadata": None, "graph": None, "list": None}
    app.logger.debug("Processing database results for topic")
    list_ = []
    metadata = {}
    topic_clusters = []
    for entry in data['subfield_metadata']:
        topic_cluster = entry['topic']
        topic_clusters.append(topic_cluster)
        subfield_oa_link = entry['subfield_url']
    metadata['topic_clusters'] = topic_clusters
    metadata['work_count'] = data['totals']['total_num_of_works']
    metadata['cited_by_count'] = data['totals']['total_num_of_citations']
    metadata['researchers'] = data['totals']['total_num_of_authors']
    metadata['oa_link'] = subfield_oa_link
    metadata['name'] = topic.title()
    nodes = []
    edges = []
    topic_id = topic
    nodes.append({'id': topic_id, 'label': topic, 'type': 'TOPIC'})
    for entry in data['data']:
        institution = entry['institution_name']
        number = entry['num_of_authors']
        list_.append((institution, number))
        nodes.append(
            {'id': institution, 'label': institution, 'type': 'INSTITUTION'})
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({
            'id': f"""{institution}-{topic_id}""",
            'start': institution,
            'end': topic_id,
            "label": "researches",
            "start_type": "INSTITUTION",
            "end_type": "TOPIC"
        })
        edges.append({
            'id': f"""{institution}-{number}""",
            'start': institution,
            'end': number,
            "label": "number",
            "start_type": "INSTITUTION",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    return {"metadata": metadata, "graph": graph, "list": list_}


def get_researcher_and_subfield_results(researcher, topic):
    """
    I was wonder if we can test this by getting the results with the mock cases..
    how can we mock the experience of what happens when the user inputs an institution
    and researcher? Well, we can use the database to get the result and then default
    to SPARQL if the institution or researcher is not in the database. Same as always.
    """
    data = search_by_author_topic(researcher, topic)
    if data is None:
        app.logger.info("No database results, falling back to SPARQL...")
        data = get_topic_and_researcher_metadata_sparql(topic, researcher)
        if data == {}:
            app.logger.warning(
                "No results found in SPARQL for researcher and topic")
            return {}
        work_list, graph, extra_metadata = list_given_researcher_topic(
            topic,
            researcher,
            data['current_institution'],
            data['topic_oa_link'],
            data['researcher_oa_link'],
            data['institution_url'],
        )
        data['work_count'] = extra_metadata['work_count']
        data['cited_by_count'] = extra_metadata['cited_by_count']
        return {"metadata": data, "graph": graph, "list": work_list}
    app.logger.debug("Processing database results for researcher and topic")
    list_ = []
    metadata = {}
    topic_clusters = []
    for entry in data['subfield_metadata']:
        topic_cluster = entry['topic']
        topic_clusters.append(topic_cluster)
        subfield_oa_link = entry['subfield_url']
    metadata['topic_name'] = topic
    metadata['topic_clusters'] = topic_clusters
    metadata['work_count'] = data['totals']['total_num_of_works']
    metadata['cited_by_count'] = data['totals']['total_num_of_citations']
    metadata['topic_oa_link'] = subfield_oa_link
    if data['author_metadata']['orcid'] is None:
        metadata['orcid'] = ''
    else:
        metadata['orcid'] = data['author_metadata']['orcid']
    metadata['researcher_name'] = researcher
    metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
    if data['author_metadata']['last_known_institution'] is None:
        app.logger.debug("Fetching last known institutions from OpenAlex")
        institution_object = fetch_last_known_institutions(
            metadata['researcher_oa_link'])[0]
        metadata['current_institution'] = institution_object['display_name']
    else:
        metadata['current_institution'] = data['author_metadata']['last_known_institution']
    last_known_institution = metadata['current_institution']
    nodes = []
    edges = []
    researcher_id = metadata['researcher_oa_link']
    subfield_id = metadata['topic_oa_link']
    """ Node for the Institution """
    nodes.append({
        'id': last_known_institution,
        'label': last_known_institution,
        'type': 'INSTITUTION'
    })
    edges.append({
        'id': f"""{researcher_id}-{last_known_institution}""",
        'start': researcher_id,
        'end': last_known_institution,
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    })
    """ Node for the Author """
    nodes.append({'id': researcher_id, 'label': researcher, 'type': 'AUTHOR'})
    """ Node for the Subfield """
    nodes.append({'id': subfield_id, 'label': topic, 'type': 'TOPIC'})
    edges.append({
        'id': f"""{researcher_id}-{subfield_id}""",
        'start': researcher_id,
        'end': subfield_id,
        "label": "researches",
        "start_type": "AUTHOR",
        "end_type": "TOPIC"
    })
    for entry in data['data']:
        work = entry['work_name']
        number = entry['num_of_citations']
        list_.append((work, number))
        """ Node for Work """
        nodes.append({'id': work, 'label': work, 'type': 'WORK'})
        """ Node for Numberage """
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({
            'id': f"""{researcher_id}-{work}""",
            'start': researcher_id,
            'end': work,
            "label": "authored",
            "start_type": "AUTHOR",
            "end_type": "WORK"
        })
        edges.append({
            'id': f"""{work}-{number}""",
            'start': work,
            'end': number,
            "label": "citedBy",
            "start_type": "WORK",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    return {"metadata": metadata, "graph": graph, "list": list_}


def get_institution_and_subfield_results(institution, topic):
    """
    Some minor results, these are the results that the user gets when the user inputs
    an institution & researcher & subfield..uses the database, to get result and then
    defaults to SPARQL if the institution or the researcher is not in the database.
    """
    data = search_by_institution_topic(institution, topic)
    if data is None:
        app.logger.info("Using SPARQL for institution and topic search...")
        data = get_institution_and_topic_metadata_sparql(institution, topic)
        if data == {}:
            app.logger.warning(
                "No results found in SPARQL for institution and topic")
            return {}
        topic_list, graph, extra_metadata = list_given_institution_topic(
            institution,
            data['institution_oa_link'],
            topic,
            data['topic_oa_link']
        )
        data['work_count'] = extra_metadata['work_count']
        data['people_count'] = extra_metadata['num_people']
        return {"metadata": data, "graph": graph, "list": topic_list}
    app.logger.debug("Processing database results for institution and topic")
    list_ = []
    metadata = {}
    topic_clusters = []
    for entry in data['subfield_metadata']:
        topic_cluster = entry['topic']
        topic_clusters.append(topic_cluster)
        subfield_oa_link = entry['subfield_url']
    metadata['topic_name'] = topic
    metadata['topic_clusters'] = topic_clusters
    metadata['work_count'] = data['totals']['total_num_of_works']
    metadata['cited_by_count'] = data['totals']['total_num_of_citations']
    metadata['people_count'] = data['totals']['total_num_of_authors']
    metadata['topic_oa_link'] = subfield_oa_link
    metadata['topic_name'] = topic
    metadata['homepage'] = data['institution_metadata']['url']
    metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
    metadata['ror'] = data['institution_metadata']['ror']
    metadata['institution_name'] = institution
    nodes = []
    edges = []
    subfield_id = metadata['topic_oa_link']
    institution_id = metadata['institution_oa_link']
    nodes.append({'id': subfield_id, 'label': topic, 'type': 'TOPIC'})
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({
        'id': f"""{institution_id}-{subfield_id}""",
        'start': institution_id,
        'end': subfield_id,
        "label": "researches",
        "start_type": "INSTITUTION",
        "end_type": "TOPIC"
    })
    for entry in data['data']:
        author_id = entry['author_id']
        author_name = entry['author_name']
        number = entry['num_of_works']
        list_.append((author_name, number))
        nodes.append({'id': author_id, 'label': author_name, 'type': 'AUTHOR'})
        nodes.append({'id': number, 'label': number, 'type': 'NUMBER'})
        edges.append({
            'id': f"""{author_id}-{number}""",
            'start': author_id,
            'end': number,
            "label": "numWorks",
            "start_type": "AUTHOR",
            "end_type": "NUMBER"
        })
        edges.append({
            'id': f"""{author_id}-{institution_id}""",
            'start': author_id,
            'end': institution_id,
            "label": "memberOf",
            "start_type": "AUTHOR",
            "end_type": "INSTITUTION"
        })
    graph = {"nodes": nodes, "edges": edges}
    metadata['people_count'] = len(list_)
    return {"metadata": metadata, "graph": graph, "list": list_}


def get_institution_and_researcher_results(institution, researcher):
    """
    Queries the endpoint to execute the SPARQL query. ✨ Handles institution & researcher search from DB, "reverts" to SPARQL if none found.
    """
    data = search_by_author_institution(researcher, institution)
    if data is None:
        app.logger.info(
            "Using SPARQL for institution and researcher search...")
        data = get_researcher_and_institution_metadata_sparql(
            researcher, institution)
        if data == {}:
            app.logger.warning(
                "No results found in SPARQL for institution and researcher")
            return {}
        topic_list, graph = list_given_researcher_institution(
            data['researcher_oa_link'], researcher, institution
        )
        return {"metadata": data, "graph": graph, "list": topic_list}
    app.logger.debug(
        "Processing database results for institution and researcher")
    list_ = []
    metadata = {}
    metadata['homepage'] = data['institution_metadata']['url']
    metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
    metadata['ror'] = data['institution_metadata']['ror']
    metadata['institution_name'] = institution
    if data['author_metadata']['orcid'] is None:
        metadata['orcid'] = ''
    else:
        metadata['orcid'] = data['author_metadata']['orcid']
    metadata['researcher_name'] = researcher
    metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
    metadata['current_institution'] = ""
    metadata['work_count'] = data['author_metadata']['num_of_works']
    metadata['cited_by_count'] = data['author_metadata']['num_of_citations']
    nodes = []
    edges = []
    author_id = metadata['researcher_oa_link']
    nodes.append(
        {'id': institution, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({
        'id': f"""{author_id}-{institution}""",
        'start': author_id,
        'end': institution,
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    })
    nodes.append({'id': author_id, 'label': researcher, "type": "AUTHOR"})
    for entry in data['data']:
        topic_name = entry['topic_name']
        num_works = entry["num_of_works"]
        list_.append((topic_name, num_works))
        nodes.append({'id': topic_name, 'label': topic_name, 'type': "TOPIC"})
        number_id = topic_name + ":" + str(num_works)
        nodes.append({'id': number_id, 'label': num_works, 'type': "NUMBER"})
        edges.append({
            'id': f"""{author_id}-{topic_name}""",
            'start': author_id,
            'end': topic_name,
            "label": "researches",
            "start_type": "AUTHOR",
            "end_type": "TOPIC"
        })
        edges.append({
            'id': f"""{topic_name}-{number_id}""",
            'start': topic_name,
            'end': number_id,
            "label": "number",
            "start_type": "TOPIC",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    return {"metadata": metadata, "graph": graph, "list": list_}


def get_institution_researcher_subfield_results(institution, researcher, topic):
    """
    Proposed test task addition for backend: given an institution, make sure that we are querying the SemOpenAlex endpoint to retrieve metadata on the institution.
    """
    data = search_by_author_institution_topic(researcher, institution, topic)
    if data is None:
        app.logger.info(
            "Using SPARQL for institution, researcher, and topic search...")
        data = get_institution_and_topic_and_researcher_metadata_sparql(
            institution, topic, researcher
        )
        if data == {}:
            app.logger.warning(
                "No results found for institution, researcher, and topic")
            return {}
        work_list, graph, extra_metadata = list_given_researcher_topic(
            topic,
            researcher,
            institution,
            data['topic_oa_link'],
            data['researcher_oa_link'],
            data['institution_oa_link']
        )
        data['work_count'] = extra_metadata['work_count']
        data['cited_by_count'] = extra_metadata['cited_by_count']
        return {"metadata": data, "graph": graph, "list": work_list}
    app.logger.debug(
        "Processing database results for institution, researcher, and topic")
    list_ = []
    metadata = {}
    metadata['homepage'] = data['institution_metadata']['url']
    metadata['institution_oa_link'] = data['institution_metadata']['openalex_url']
    metadata['ror'] = data['institution_metadata']['ror']
    metadata['institution_name'] = institution
    if data['author_metadata']['orcid'] is None:
        metadata['orcid'] = ''
    else:
        metadata['orcid'] = data['author_metadata']['orcid']
    metadata['researcher_name'] = researcher
    metadata['researcher_oa_link'] = data['author_metadata']['openalex_url']
    metadata['current_institution'] = ""
    topic_clusters = []
    for entry in data['subfield_metadata']:
        topic_cluster = entry['topic']
        topic_clusters.append(topic_cluster)
        subfield_oa_link = entry['subfield_url']
    metadata['topic_name'] = topic
    metadata['topic_clusters'] = topic_clusters
    metadata['work_count'] = data['totals']['total_num_of_works']
    metadata['cited_by_count'] = data['totals']['total_num_of_citations']
    metadata['topic_oa_link'] = subfield_oa_link
    nodes = []
    edges = []
    institution_id = metadata['institution_oa_link']
    researcher_id = metadata['researcher_oa_link']
    subfield_id = metadata['topic_oa_link']
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({
        'id': f"""{researcher_id}-{institution_id}""",
        'start': researcher_id,
        'end': institution_id,
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    })
    nodes.append({'id': researcher_id, 'label': researcher, 'type': 'AUTHOR'})
    nodes.append({'id': subfield_id, 'label': topic, 'type': 'TOPIC'})
    edges.append({
        'id': f"""{researcher_id}-{subfield_id}""",
        'start': researcher_id,
        'end': subfield_id,
        "label": "researches",
        "start_type": "AUTHOR",
        "end_type": "TOPIC"
    })
    for entry in data['data']:
        work_name = entry['work_name']
        number = entry['cited_by_count']
        list_.append((work_name, number))
        nodes.append({'id': work_name, 'label': work_name, 'type': 'WORK'})
        nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
        edges.append({
            'id': f"""{researcher_id}-{work_name}""",
            'start': researcher_id,
            'end': work_name,
            "label": "authored",
            "start_type": "AUTHOR",
            "end_type": "WORK"
        })
        edges.append({
            'id': f"""{work_name}-{number}""",
            'start': work_name,
            'end': number,
            "label": "citedBy",
            "start_type": "WORK",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    return {"metadata": metadata, "graph": graph, "list": list_}

# ----------------------------------------------------------------------
# SPARQL query helpers are here.
# ----------------------------------------------------------------------


def query_SPARQL_endpoint(endpoint_url, query):
    """
    Before we get the institution we have to use OpenAlex to determine the sub-fields which a given institution studies..thus we "must" iterate through all authors related to the institution and then determine what topics OpenAlex attributes, to them.
    """
    app.logger.debug(f"Executing SPARQL query: {query}")
    try:
        response = requests.post(
            endpoint_url,
            data={"query": query},
            headers={'Accept': 'application/json'}
        )
        response.raise_for_status()
        data = response.json()
        return_value = []
        for entry in data['results']['bindings']:
            row_dict = {}
            for e in entry:
                row_dict[e] = entry[e]['value']
            return_value.append(row_dict)
        app.logger.info(f"SPARQL query returned {len(return_value)} results")
        return return_value
    except requests.exceptions.RequestException as e:
        app.logger.error(f"SPARQL query failed: {str(e)}")
        return []


def get_institution_metadata_sparql(institution):
    """
    Here we have to be "ready" to push the update to the metadata..the meta-data is a part of the object in the sense that we can't have an object without the metadata..we have to query the SemOpenAlex endpoint in order to retrieve the metadata on the author.
    """
    app.logger.debug(
        f"Fetching institution metadata from SPARQL for: {institution}")
    query = f"""
    SELECT ?ror ?workscount ?citedcount ?homepage ?institution (COUNT(distinct ?people) as ?peoplecount)
    WHERE {{
      ?institution <http://xmlns.com/foaf/0.1/name> "{institution}" .
      ?institution <https://semopenalex.org/ontology/ror> ?ror .
      ?institution <https://semopenalex.org/ontology/worksCount> ?workscount .
      ?institution <https://semopenalex.org/ontology/citedByCount> ?citedcount .
      ?institution <http://xmlns.com/foaf/0.1/homepage> ?homepage .
      ?people <http://www.w3.org/ns/org#memberOf> ?institution .
    }} GROUP BY ?ror ?workscount ?citedcount ?homepage ?institution
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    if not results:
        app.logger.warning(
            f"No SPARQL results found for institution: {institution}")
        return {}
    data = results[0]
    ror = data['ror']
    works_count = data['workscount']
    cited_count = data['citedcount']
    homepage = data['homepage']
    author_count = data['peoplecount']
    oa_link = data['institution'].replace('semopenalex', 'openalex').replace(
        'institution', 'institutions'
    )
    hbcu = is_HBCU(oa_link)
    metadata = {
        "name": institution,
        "ror": ror,
        "works_count": works_count,
        "cited_count": cited_count,
        "homepage": homepage,
        "author_count": author_count,
        'oa_link': oa_link,
        "hbcu": hbcu
    }
    return metadata


def list_given_institution(ror, name, id):
    """
    Return value: the metadata consists of information on the author in the form of a dictionary with the following keys: name, cited_by_count, orcid, work_count, current_institution, oa-link, institution_url. "Gather" subfields for an institution by looking up its authors on OpenAlex, and of course counting "how many times" each subfield occurs.
    """
    app.logger.debug(
        f"Fetching subfields for institution: {name} (ROR: {ror})")
    final_subfield_count = {}
    headers = {'Accept': 'application/json'}
    response = requests.get(
        f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=*',
        headers=headers
    )
    data = response.json()
    authors = data['results']
    next_page = data['meta']['next_cursor']
    counter = 0
    while next_page is not None and counter < 10:
        for a in authors:
            topics = a['topics']
            for topic in topics:
                subfield = topic['subfield']['display_name']
                final_subfield_count[subfield] = final_subfield_count.get(
                    subfield, 0) + 1
        response = requests.get(
            f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor={next_page}',
            headers=headers
        )
        data = response.json()
        authors = data['results']
        next_page = data['meta']['next_cursor']
        counter += 1
    """ Then we return some metadata that "consists of" the informatino on the institution as well as the researcher as a dictionary with the following keys: institution_name, researcher_name, homepage, institution_oa_link, researcher_oa_link, orcid, work_count, cited_by_count, ror. But then we filter out the sub-fields that have 5 or even fewer authors. """
    sorted_subfields = sorted(
        [(k, v) for k, v in final_subfield_count.items() if v > 5],
        key=lambda x: x[1],
        reverse=True
    )
    nodes = []
    edges = []
    """ Node for Institution """
    nodes.append({'id': id, 'label': name, 'type': 'INSTITUTION'})
    for subfield, number in sorted_subfields:
        """ Node for Subfield """
        nodes.append({'id': subfield, 'label': subfield, 'type': "TOPIC"})
        number_id = subfield + ":" + str(number)
        """ Node for the Number """
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({
            'id': f"""{id}-{subfield}""",
            'start': id,
            'end': subfield,
            "label": "researches",
            "start_type": "INSTITUTION",
            "end_type": "TOPIC"
        })
        edges.append({
            'id': f"""{subfield}-{number_id}""",
            'start': subfield,
            'end': number_id,
            "label": "number",
            "start_type": "TOPIC",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    return sorted_subfields, graph


def get_author_metadata_sparql(author):
    """
    Retrieve author metadata out of SPARQL by name. In the same "sense" that we can aviate the hybrid search, we can have the user search for a researcher only or a researcher & institution. We check OpenAlex, for what topics are attributed to the author.
    """
    query = f"""
    SELECT ?cite_count ?orcid ?works_count ?current_institution_name ?author ?current_institution
    WHERE {{
      ?author <http://xmlns.com/foaf/0.1/name> "{author}" .
      ?author <https://semopenalex.org/ontology/citedByCount> ?cite_count .
      OPTIONAL {{?author <https://dbpedia.org/ontology/orcidId> ?orcid .}}
      ?author <https://semopenalex.org/ontology/worksCount> ?works_count .
      ?author <http://www.w3.org/ns/org#memberOf> ?current_institution .
      ?current_institution <http://xmlns.com/foaf/0.1/name> ?current_institution_name .
    }}
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    if results == []:
        return {}
    first = results[0]
    cited_by_count = first['cite_count']
    orcid = first['orcid'] if 'orcid' in first else ''
    work_count = first['works_count']
    current_institution = first['current_institution_name']
    oa_link = first['author'].replace('semopenalex', 'openalex').replace(
        'author', 'authors'
    )
    institution_link = first['current_institution'].replace(
        'semopenalex', 'openalex'
    ).replace('institution', 'institutions')
    return {
        "name": author,
        "cited_by_count": cited_by_count,
        "orcid": orcid,
        "work_count": work_count,
        "current_institution": current_institution,
        "oa_link": oa_link,
        "institution_url": institution_link
    }


def get_researcher_and_institution_metadata_sparql(researcher, institution):
    """
    Retrieve combined researcher & institution metadata from the SPARQL directory. We finalize the subfield, as a property and then query the OpenAlex endpoint in order to retrieve the metadata on the subfield..we don't make massive code changes but we do query the database. The only thing is we don't actually query SemOpenAlex because the necessary data is faster to retrieve from OpenAlex, but this may change..in the future.
    And what we do is we realize that researchers do not work as expected at the moment.
    We have to make sure that we return the proper values. We return the metadata which consists of subfield-related information as a dictionary with the following keys--name, topic_clusters, cited_by_count, work_count, researchers, oa_link.
    """
    researcher_data = get_author_metadata_sparql(researcher)
    institution_data = get_institution_metadata_sparql(institution)
    if researcher_data == {} or institution_data == {}:
        return {}
    return {
        "institution_name": institution,
        "researcher_name": researcher,
        "homepage": institution_data['homepage'],
        "institution_oa_link": institution_data['oa_link'],
        "researcher_oa_link": researcher_data['oa_link'],
        "orcid": researcher_data['orcid'],
        "work_count": researcher_data['work_count'],
        "cited_by_count": researcher_data['cited_by_count'],
        "ror": institution_data['ror']
    }


def list_given_researcher_institution(id, name, institution):
    """
    Build up the (topics, counts) list and a graph for a given researcher + institution using the OpenAlex /authors API (topics). In order to list the given topic, we need to know that a user searches for a topic only. We search through each Historically Black College and University as well as partner institutions and we return which institutions research the subfield.
    """
    app.logger.debug(
        f"Building list for researcher: {name} at institution: {institution}")
    final_subfield_count = {}
    headers = {'Accept': 'application/json'}
    search_id = id.replace('https://openalex.org/authors/', '')
    response = requests.get(
        f'https://api.openalex.org/authors/{search_id}', headers=headers
    )
    data = response.json()
    topics = data.get('topics', [])
    for t in topics:
        subfield = t['subfield']['display_name']
        final_subfield_count[subfield] = final_subfield_count.get(
            subfield, 0) + t['count']
    sorted_subfields = sorted(
        final_subfield_count.items(), key=lambda x: x[1], reverse=True)
    nodes = []
    edges = []
    nodes.append(
        {'id': institution, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({
        'id': f"""{id}-{institution}""",
        'start': id,
        'end': institution,
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    })
    nodes.append({'id': id, 'label': name, "type": "AUTHOR"})
    for s, number in sorted_subfields:
        nodes.append({'id': s, 'label': s, 'type': "TOPIC"})
        number_id = s + ":" + str(number)
        nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
        edges.append({
            'id': f"""{id}-{s}""",
            'start': id,
            'end': s,
            "label": "researches",
            "start_type": "AUTHOR",
            "end_type": "TOPIC"
        })
        edges.append({
            'id': f"""{s}-{number_id}""",
            'start': s,
            'end': number_id,
            "label": "number",
            "start_type": "TOPIC",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    return sorted_subfields, graph


def get_subfield_metadata_sparql(subfield):
    """
    What are the parameters that we take?
        subfield: This is the name of the subfield searched.
        id: id of the subfield, just in case the document ends up being 99 pages.
    Get meta-data for a sub-field from OpenAlex sub-fields. (This is 'the approach of the placeholder'.)
    """
    headers = {'Accept': 'application/json'}
    response = requests.get(
        f'https://api.openalex.org/subfields?filter=display_name.search:{subfield}',
        headers=headers
    )
    data = response.json()['results'][0]
    oa_link = data['id']
    cited_by_count = data['cited_by_count']
    work_count = data['works_count']
    topic_clusters = [t['display_name'] for t in data['topics']]
    """ And here is what we return, it's quite wonderful in that we can return the subfield_list, which is the subfields which OpenAlex attributes to a given institution AND the graph, which is a graphical representation of subfield_list. So we know that the "researchers" are not exposed in the same type of detail therefore the default is 0 or we compute "that" externally. """
    researchers = 0
    return {
        "name": subfield,
        "topic_clusters": topic_clusters,
        "cited_by_count": cited_by_count,
        "work_count": work_count,
        "researchers": researchers,
        "oa_link": oa_link
    }


def list_given_topic(subfield, id):
    """
    We could probably dockerize the backend in such a way as to make sure that we can do a demo of the test features, we need to be able to run pytest on all of these functions which means that, given a topic & institution we collect the metadata for the 2 as well as return one as one dictionary.
    What do we return? Well, we return the metadata which consists of information on the topic & institution as a dictionary with the following keys:
        institution_name, topic_Name, work_count, cited_by_count, ror, topic_clusters, people_count, topic_oa_link, institution_oa_link, homepage
    Utility function to get all the data gathered about a subfield across institutions. We don't actively use the approach of the placeholder just "yet".
    """
    headers = {'Accept': 'application/json'}
    subfield_list = []
    extra_metadata = {}
    total_work_count = 0
    """ Creating a venv might help. When a user searches for an institution and topic we want to use a SemOpenAlex query to retrieve the authors who work at the given institution AND HAVE published papers that are related to the provided subfield. We know for demonstration that we can iterate over known institutions. """
    for institution in autofill_inst_list:
        response = requests.get(
            f'https://api.openalex.org/institutions?select=display_name,topics&filter=display_name.search:{institution}',
            headers=headers
        )
        try:
            data = response.json()['results'][0]
            inst_topics = data['topics']
            count = 0
            for t in inst_topics:
                if t['subfield']['display_name'] == subfield:
                    count += t['count']
                    total_work_count += t['count']
            if count > 0:
                subfield_list.append((institution, count))
        except:
            continue
    subfield_list.sort(key=lambda x: x[1], reverse=True)
    extra_metadata['work_count'] = total_work_count
    nodes = []
    edges = []
    nodes.append({'id': id, 'label': subfield, 'type': 'TOPIC'})
    for i, c in subfield_list:
        if c != 0:
            nodes.append({'id': i, 'label': i, 'type': 'INSTITUTION'})
            nodes.append({'id': c, 'label': c, 'type': "NUMBER"})
            edges.append({
                'id': f"""{i}-{id}""",
                'start': i,
                'end': id,
                "label": "researches",
                "start_type": "INSTITUTION",
                "end_type": "TOPIC"
            })
            edges.append({
                'id': f"""{i}-{c}""",
                'start': i,
                'end': c,
                "label": "number",
                "start_type": "INSTITUTION",
                "end_type": "NUMBER"
            })
    graph = {"nodes": nodes, "edges": edges}
    return subfield_list, graph, extra_metadata


def get_institution_and_topic_metadata_sparql(institution, topic):
    """
    I recommended checking the documentation for SPARQL as well because we know that when we do the unit tests, we have to confirm that these functions like SSL on Postgres being mandatory for all cloud platforms..we have got to collect the metadata for the topic and researcher which are supplied as parameters for the 2 and returns as one dictionary. Retrieve the combined topic & institutional metadata from the SPARQL database.
    """
    institution_data = get_institution_metadata_sparql(institution)
    topic_data = get_subfield_metadata_sparql(topic)
    if topic_data == {} or institution_data == {}:
        return {}
    return {
        "institution_name": institution,
        "topic_name": topic,
        "work_count": institution_data['works_count'],
        "cited_by_count": institution_data['cited_count'],
        "ror": institution_data['ror'],
        "topic_clusters": topic_data['topic_clusters'],
        "people_count": institution_data['author_count'],
        "topic_oa_link": topic_data['oa_link'],
        "institution_oa_link": institution_data['oa_link'],
        "homepage": institution_data['homepage']
    }


def list_given_institution_topic(institution, institution_id, topic, topic_id):
    """
    We have got to return some metadata such as the information on the topic & researcher as a dictionary with the following keys:
        researcher_name, topic_name, orcid, current_institution, work_count, cited_by_count, topic_clusters, researcher_oa_link, topic_oa_link.

    This is how we make things happen we have made sure that every person who is on orCID has an official account, so that we can train our unit tests on more data.
    That's 'what we're doing', we're building the list of authors who do work at the given institution on the given topic via SemOpenAlex SPARQL.
    """
    app.logger.debug(
        f"Building list for institution: {institution} and topic: {topic}")
    query = f"""
    SELECT DISTINCT ?author ?name (GROUP_CONCAT(DISTINCT ?work; SEPARATOR=", ") AS ?works)
    WHERE {{
      ?institution <http://xmlns.com/foaf/0.1/name> "{institution}" .
      ?author <http://www.w3.org/ns/org#memberOf> ?institution .
      ?author <http://xmlns.com/foaf/0.1/name> ?name .
      ?work <http://purl.org/dc/terms/creator> ?author .
      ?subfield a <https://semopenalex.org/ontology/Subfield> .
      ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
      ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
      << ?work <https://semopenalex.org/ontology/hasTopic> ?topic >> ?p ?o .
    }}
    GROUP BY ?author ?name
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    works_list = []
    final_list = []
    work_count = 0
    for a in results:
        """ For error traces and such, when a user searches for a researcher and topic we know that the server-side is going to be quite "silent" to put it shortly..searching for a researcher and topic utilizes a SemOpenAlex query to retrieve works by the author that are related to the topic. Count works by splitting down the GROUP_CONCAT """
        n_works = a['works'].count(",") + 1
        works_list.append((a['author'], a['name'], n_works))
        final_list.append((a['name'], n_works))
        work_count += n_works
    final_list.sort(key=lambda x: x[1], reverse=True)
    num_people = len(final_list)
    nodes = []
    edges = []
    nodes.append({'id': topic_id, 'label': topic, 'type': 'TOPIC'})
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({
        'id': f"""{institution_id}-{topic_id}""",
        'start': institution_id,
        'end': topic_id,
        "label": "researches",
        "start_type": "INSTITUTION",
        "end_type": "TOPIC"
    })
    for author, name, num_works in works_list:
        nodes.append({'id': author, 'label': name, 'type': 'AUTHOR'})
        nodes.append({'id': num_works, 'label': num_works, 'type': 'NUMBER'})
        edges.append({
            'id': f"""{author}-{institution_id}""",
            'start': author,
            'end': institution_id,
            "label": "memberOf",
            "start_type": "AUTHOR",
            "end_type": "INSTITUTION"
        })
        edges.append({
            'id': f"""{author}-{num_works}""",
            'start': author,
            'end': num_works,
            "label": "numWorks",
            "start_type": "AUTHOR",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    extra_metadata = {"work_count": work_count, "num_people": num_people}
    return final_list, graph, extra_metadata


def get_topic_and_researcher_metadata_sparql(topic, researcher):
    """
    I don't know why I dropped off the metadata tag during my unit tests, but what I do know is that given an institution & topic & researcher I should be able to collect the metadata for the 3 and return it as one dictionary. Retrieve the combined researcher & topic metadata from SPARQL!
    """
    researcher_data = get_author_metadata_sparql(researcher)
    topic_data = get_subfield_metadata_sparql(topic)
    if researcher_data == {} or topic_data == {}:
        return {}
    return {
        "researcher_name": researcher,
        "topic_name": topic,
        "orcid": researcher_data['orcid'],
        "current_institution": researcher_data['current_institution'],
        "work_count": researcher_data['work_count'],
        "cited_by_count": researcher_data['cited_by_count'],
        "topic_clusters": topic_data['topic_clusters'],
        "researcher_oa_link": researcher_data['oa_link'],
        "topic_oa_link": topic_data['oa_link'],
        "institution_url": researcher_data['institution_url']
    }


def list_given_researcher_topic(
    topic, researcher, institution, topic_id, researcher_id, institution_id
):
    """
    We can remove the institutions and handle autofill for them by testing them to make sure that everything still works before pushing that code. We can build the 'works' list' by "any" given researcher on any given topic via SPARQL.
    """
    app.logger.debug(
        f"Building list for researcher: {researcher} and topic: {topic}")
    query = f"""
    SELECT DISTINCT ?work ?title ?cited_by_count
    WHERE {{
      ?author <http://xmlns.com/foaf/0.1/name> "{researcher}" .
      ?work <http://purl.org/dc/terms/creator> ?author .
      ?work <http://xmlns.com/foaf/0.1/name> ?title .
      ?work <https://semopenalex.org/ontology/citedByCount> ?cited_by_count .
      ?subfield a <https://semopenalex.org/ontology/Subfield> .
      ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{topic}" .
      ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
      << ?work <https://semopenalex.org/ontology/hasTopic> ?topic >> ?p ?o .
    }}
    """
    results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
    work_list = []
    total_citations = 0
    for r in results:
        title = r['title']
        ccount = int(r['cited_by_count'])
        work_list.append((title, ccount))
        total_citations += ccount
    work_list.sort(key=lambda x: x[1], reverse=True)
    nodes = []
    edges = []
    # Node for the Institution
    nodes.append(
        {'id': institution_id, 'label': institution, 'type': 'INSTITUTION'})
    edges.append({
        'id': f"""{researcher_id}-{institution_id}""",
        'start': researcher_id,
        'end': institution_id,
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    })
    # Node for the Author
    nodes.append({'id': researcher_id, 'label': researcher, 'type': 'AUTHOR'})
    # Node for the Topic
    nodes.append({'id': topic_id, 'label': topic, 'type': 'TOPIC'})
    edges.append({
        'id': f"""{researcher_id}-{topic_id}""",
        'start': researcher_id,
        'end': topic_id,
        "label": "researches",
        "start_type": "AUTHOR",
        "end_type": "TOPIC"
    })
    for work, number in work_list:
        nodes.append({'id': work, 'label': work, 'type': 'WORK'})
        nodes.append({'id': str(number), 'label': number, 'type': "NUMBER"})
        edges.append({
            'id': f"""{researcher_id}-{work}""",
            'start': researcher_id,
            'end': work,
            "label": "authored",
            "start_type": "AUTHOR",
            "end_type": "WORK"
        })
        edges.append({
            'id': f"""{work}-{number}""",
            'start': work,
            'end': str(number),
            "label": "citedBy",
            "start_type": "WORK",
            "end_type": "NUMBER"
        })
    graph = {"nodes": nodes, "edges": edges}
    extra_metadata = {"work_count": len(
        work_list), "cited_by_count": total_citations}
    return work_list, graph, extra_metadata


def get_institution_and_topic_and_researcher_metadata_sparql(institution, topic, researcher):
    """
    So once we get added to the CloudBank subscription we are ready to finish the handling of the autofill for the topics. Retrieve combined institution + topic + researcher metadata from the SPARQL directory.
    """
    app.logger.debug(
        f"Fetching metadata for institution: {institution}, topic: {topic}, researcher: {researcher}"
    )
    institution_data = get_institution_metadata_sparql(institution)
    topic_data = get_subfield_metadata_sparql(topic)
    researcher_data = get_author_metadata_sparql(researcher)
    if researcher_data == {} or institution_data == {} or topic_data == {}:
        app.logger.warning("Missing metadata from one or more entities")
        return {}
    ror = institution_data['ror']
    metadata = {
        "institution_name": institution,
        "topic_name": topic,
        "researcher_name": researcher,
        "topic_oa_link": topic_data['oa_link'],
        "institution_oa_link": institution_data['oa_link'],
        "homepage": institution_data['homepage'],
        "orcid": researcher_data['orcid'],
        "topic_clusters": topic_data['topic_clusters'],
        "researcher_oa_link": researcher_data['oa_link'],
        "work_count": researcher_data['work_count'],
        "cited_by_count": researcher_data['cited_by_count'],
        'ror': ror
    }
    return metadata


def create_connection(host_name, user_name, user_password, db_name):
    app.logger.debug(f"Attempting to connect to MySQL database: {db_name}")
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name,
        )
        app.logger.info("Successfully connected to MySQL database")
    except mysql.connector.Error as e:
        app.logger.error(f"Failed to connect to MySQL database: {str(e)}")
    except Exception as e:
        app.logger.error(f"Generic error while connecting: {str(e)}")
        return None

    return connection


def is_HBCU(openalex_id):
    """
    My suggestion is that when we do the graph, we have to optimize the search. The thing about search is that it's "reasonably" fast on the CollabNext.io and the CollabNext.io/alpha subdomain, we just have to remember to return the default graph from default.json using the absolute path. So we check whether an institution with a given OpenAlex ID is even an Historically Black College or University, by querying the MySQL `institutions_filtered` table. Returns True/False.
    """
    app.logger.debug(f"Checking HBCU status for institution ID: {openalex_id}")
    connection = create_connection(
        "openalexalpha.mysql.database.azure.com",
        "openalexreader",
        "collabnext2024reader!",
        "openalex",
    )
    local_id = openalex_id.replace("https://openalex.org/institutions/", "")
    query = f"""SELECT HBCU FROM institutions_filtered WHERE id = "{local_id}";"""
    result = query_SQL_endpoint(connection, query)
    is_hbcu = (result == [(1,)])
    app.logger.info(f"Institution {local_id} HBCU status: {is_hbcu}")
    return is_hbcu


def query_SQL_endpoint(connection, query):
    """
    They call that a default graph because it has all the nodes and all the edges.
    I will push a unit test draft in order to show how we can return a small lift, the default graph for the topic space (hard-coded example).
    Here it is, the helper for executing raw SQL queries on MySQL.
    """
    app.logger.debug(f"Executing SQL query: {query}")
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        app.logger.info(f"SQL query returned {len(result)} results")
        return result
    except Error as e:
        app.logger.error(f"SQL query failed: {str(e)}")

# -----------------------------------------------------------------------------
#     It would be best that I write this Application Programming Interface call for searches from the user when searching the space of all topics, the static file serving route (now there's only one route)
# -----------------------------------------------------------------------------


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and exists(os.path.join(app.static_folder, path)):
        app.logger.debug(f"Serving static file: {path}")
        return send_from_directory(app.static_folder, path)
    app.logger.debug("Serving index.html for frontend routing")
    return send_from_directory(app.static_folder, "index.html")


# -----------------------------------------------------------------------------
# Last but not least we must create an Structured Query Language Database connection and then return the connection object. Other endpoints (get-institutions, autofill, graph endpoints, etc. are within contained).
# -----------------------------------------------------------------------------
@app.route("/get-institutions", methods=["GET"])
def get_institutions():
    try:
        institutions_csv_path = os.path.join(BASE_DIR, "institutions.csv")
        with open(institutions_csv_path, "r") as file:
            institutions = file.read().split(",\n")
        return jsonify(institutions=institutions)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/autofill-institutions', methods=['POST'])
def autofill_institutions():
    inst = request.json.get('institution')
    app.logger.debug(f"Processing institution autofill for: {inst}")
    possible_searches = []
    for i in autofill_inst_list:
        if inst.lower() in i.lower():
            possible_searches.append(i)
    app.logger.info(
        f"Found {len(possible_searches)} matching institutions for '{inst}'")
    return {"possible_searches": possible_searches}


@app.route('/autofill-topics', methods=['POST'])
def autofill_topics():
    topic = request.json.get('topic')
    app.logger.debug(f"Processing topic autofill for: {topic}")
    possible_searches = []
    if len(topic) > 0:
        if SUBFIELDS:
            for i in autofill_subfields_list:
                if topic.lower() in i.lower():
                    possible_searches.append(i)
        else:
            for i in autofill_topics_list:
                if topic.lower() in i.lower():
                    possible_searches.append(i)
    app.logger.info(
        f"Found {len(possible_searches)} matching topics for '{topic}'")
    return {"possible_searches": possible_searches}


@app.route("/get-default-graph", methods=["POST"])
def get_default_graph():
    default_json_path = os.path.join(BASE_DIR, "default.json")
    app.logger.debug("Loading default graph from file")
    try:
        with open(default_json_path, "r") as file:
            graph = json.load(file)
    except Exception as e:
        app.logger.error(f"Failed to load default graph: {str(e)}")
        return {"error": "Failed to load default graph"}
    """ I merged some changes to main from the backend to fix the check whether or not an institution is a Historically Black College or University not from the perspective of loading issues on localhost or even on the Dockerized version, since there haven't really been that many backend changes from the Alpha version to the Public version, but because we have got some changes applied regarding the unit tests that are applicable to this database query format. (Graph processing logic remains unchanged). """
    nodes = []
    edges = []
    cur_nodes = graph["nodes"]
    cur_edges = graph["edges"]
    most = {}
    needed_topics = set()
    for edge in cur_edges:
        if edge["start"] in most:
            if edge["connecting_works"] > most[edge["start"]]:
                most[edge["start"]] = edge["connecting_works"]
        else:
            most[edge["start"]] = edge["connecting_works"]
    for edge in cur_edges:
        if most[edge["start"]] == edge["connecting_works"]:
            edges.append(edge)
            needed_topics.add(edge["end"])
    for node in cur_nodes:
        if node["type"] == "TOPIC":
            if node["id"] in needed_topics:
                nodes.append(node)
        else:
            nodes.append(node)
    final_graph = {"nodes": nodes, "edges": edges}
    app.logger.info(
        f"Successfully processed default graph with {len(nodes)} nodes and {len(edges)} edges")
    return {"graph": final_graph}


@app.route("/get-topic-space-default-graph", methods=["POST"])
def get_topic_space():
    app.logger.debug("Building topic space default graph")
    nodes = [
        {"id": 1, "label": "Physical Sciences", "type": "DOMAIN"},
        {"id": 2, "label": "Life Sciences", "type": "DOMAIN"},
        {"id": 3, "label": "Social Sciences", "type": "DOMAIN"},
        {"id": 4, "label": "Health Sciences", "type": "DOMAIN"},
    ]
    edges = []
    graph = {"nodes": nodes, "edges": edges}
    app.logger.info("Successfully built topic space default graph")
    return {"graph": graph}


@app.route("/search-topic-space", methods=["POST"])
def search_topic_space():
    search_term = request.json.get("topic", "")
    app.logger.debug(f"Searching topic space for: {search_term}")
    topic_default_json_path = os.path.join(BASE_DIR, "topic_default.json")
    try:
        with open(topic_default_json_path, "r") as file:
            graph = json.load(file)
    except Exception as e:
        app.logger.error(f"Failed to load topic space data: {str(e)}")
        return {"error": "Failed to load topic space data"}
    """ In order to make everyone's lives a little bit easier, "instead of" the tedious process to execute the SQL query in a single line of code we query the endpoint and then test it. Search processing logic does remain unchanged. """
    nodes = []
    edges = []
    matches_found = 0
    app.logger.debug("Processing topic space search results")
    for node in graph["nodes"]:
        if (
            node["label"] == search_term
            or node["subfield_name"] == search_term
            or node["field_name"] == search_term
            or node["domain_name"] == search_term
            or search_term in node["keywords"].split("; ")
        ):
            matches_found += 1
            node_additions = []
            edge_additions = []
            topic_node = {
                "id": node["id"],
                "label": node["label"],
                "type": "TOPIC",
                "keywords": node["keywords"],
                "summary": node["summary"],
                "wikipedia_url": node["wikipedia_url"],
            }
            node_additions.append(topic_node)
            subfield_node = {
                "id": node["subfield_id"],
                "label": node["subfield_name"],
                "type": "SUBFIELD",
            }
            node_additions.append(subfield_node)
            field_node = {
                "id": node["field_id"],
                "label": node["field_name"],
                "type": "FIELD",
            }
            node_additions.append(field_node)
            domain_node = {
                "id": node["domain_id"],
                "label": node["domain_name"],
                "type": "DOMAIN",
            }
            node_additions.append(domain_node)
            topic_subfield = {
                "id": f"""{node["id"]}-{node["subfield_id"]}""",
                "start": node["id"],
                "end": node["subfield_id"],
                "label": "hasSubfield",
                "start_type": "TOPIC",
                "end_type": "SUBFIELD",
            }
            edge_additions.append(topic_subfield)
            subfield_field = {
                "id": f"""{node["subfield_id"]}-{node["field_id"]}""",
                "start": node["subfield_id"],
                "end": node["field_id"],
                "label": "hasField",
                "start_type": "SUBFIELD",
                "end_type": "FIELD",
            }
            edge_additions.append(subfield_field)
            field_domain = {
                "id": f"""{node["field_id"]}-{node["domain_id"]}""",
                "start": node["field_id"],
                "end": node["domain_id"],
                "label": "hasDomain",
                "start_type": "FIELD",
                "end_type": "DOMAIN",
            }
            edge_additions.append(field_domain)
            for na in node_additions:
                if na not in nodes:
                    nodes.append(na)
            for ea in edge_additions:
                if ea not in edges:
                    edges.append(ea)
    final_graph = {"nodes": nodes, "edges": edges}
    app.logger.info(
        f"Found {matches_found} matches in topic space for '{search_term}'")
    return {"graph": final_graph}


if __name__ == "__main__":
    app.logger.info("Starting Flask microservice application")
    app.run()
