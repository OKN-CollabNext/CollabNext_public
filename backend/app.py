from flask import Flask, send_from_directory, request, jsonify
from dotenv import load_dotenv
import os
import requests
from flask_cors import CORS
import json
import mysql.connector
from mysql.connector import Error
import pandas as pd
import psycopg2

# Load environment variables
try:
  DB_HOST=os.environ['DB_HOST']
  DB_PORT= int(os.environ['DB_PORT'])
  DB_NAME=os.environ['DB_NAME']
  DB_USER=os.environ['DB_USER']
  DB_PASSWORD=os.environ['DB_PASSWORD']
  API=os.getenv('DB_API')

except:
  print("Using Local Variables")
  load_dotenv(dotenv_path=".env")
  API = os.getenv('DB_API')

# Global variable for the SPARQL endpoint
SEMOPENALEX_SPARQL_ENDPOINT = "https://semopenalex.org/sparql"
app= Flask(__name__, static_folder='build', static_url_path='/')
CORS(app)


def execute_query(query, params):
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
            with connection.cursor() as cursor:
                cursor.execute(query, params)                
                return cursor.fetchall()        
    except Exception as e:
        print(e)
        return None

def fetch_last_known_institutions(raw_id):
    """
    Make a request to the OpenAlex API to fetch the last known institutions for a given author id.
    The parameter raw_id is the id in the authors table, which has the format "https://openalex.org/author/1234",
    but we only need the last part of the id, i.e., "1234".
    """
    try:
        id = raw_id.split('/')[-1]
        response = requests.get(f"{'https://api.openalex.org/authors/'}{id}")
        data = response.json()
        return data.get('last_known_institutions', [])
    except Exception as e:
        print(f"Error fetching last known institutions for id {id}: {e}")
        return []

def get_author_ids(author_name):  
    query = """SELECT get_author_id(%s);"""
    results = execute_query(query, (author_name,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def get_institution_id(institution_name):
    query = """SELECT get_institution_id(%s);"""
    results = execute_query(query, (institution_name,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        if results[0][0] == {}:
          return None
        return results[0][0]['institution_id']
    return None

def search_by_author_institution_topic(author_name, institution_name, topic_name):
    author_ids = get_author_ids(author_name)
    if not author_ids:
        print("No author IDs found.")
        return None
    # always pick the first author
    author_id = author_ids[0]['author_id']

    institution_id = get_institution_id(institution_name)
    if institution_id is None:
      return None

    query = """SELECT search_by_author_institution_topic(%s, %s, %s);"""
    results = execute_query(query, (author_id, institution_id, topic_name))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_author_institution(author_name, institution_name):
    author_ids = get_author_ids(author_name)
    if not author_ids:
        print("No author IDs found.")
        return None
    # always pick the first author
    author_id = author_ids[0]['author_id']

    institution_id = get_institution_id(institution_name)
    if institution_id is None:
      return None

    query = """SELECT search_by_author_institution(%s, %s);"""
    results = execute_query(query, (author_id, institution_id))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_institution_topic(institution_name, topic_name):
    institution_id = get_institution_id(institution_name)
    if institution_id is None:
      return None

    query = """SELECT search_by_institution_topic(%s, %s);"""
    results = execute_query(query, (institution_id, topic_name))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_author_topic(author_name, topic_name):
    author_ids = get_author_ids(author_name)
    if not author_ids:
        print("No author IDs found.")
        return None
    # always pick the first author
    author_id = author_ids[0]['author_id']

    query = """SELECT search_by_author_topic(%s, %s);"""
    results = execute_query(query, (author_id, topic_name))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_topic(topic_name):
    query = """SELECT search_by_topic(%s);"""
    results = execute_query(query, (topic_name,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_institution(institution_name):
    institution_id = get_institution_id(institution_name)
    if institution_id is None:
      return None

    query = """SELECT search_by_institution(%s);"""
    results = execute_query(query, (institution_id,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None

def search_by_author(author_name):
    print(DB_HOST)
    author_ids = get_author_ids(author_name)
    if not author_ids:
        print("No author IDs found.")
        return None

    # always pick the first author
    author_id = author_ids[0]['author_id']    

    query = """SELECT search_by_author(%s);"""
    results = execute_query(query, (author_id,))
    if results:
        # psycopg2 returns a list of tuples with each tuple representing a row
        # we only return the first row because the SQL function is designed to return a single/a list of JSON object(s)
        return results[0][0]
    return None


## Creates lists for autofill functionality from the institution and keyword csv files
with open('institutions.csv', 'r') as file:
    autofill_inst_list = file.read().split(',\n')
with open('subfields.csv', 'r') as file:
    autofill_subfields_list = file.read().split('\n')
SUBFIELDS = True
if not SUBFIELDS:
  with open('keywords.csv', 'r') as fil:
      autofill_topics_list = fil.read().split('\n')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
  return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/initial-search', methods=['POST'])
def initial_search():
  """
  Api call for searches from the user. Calls other methods depending on what the user inputted.

  Expects the frontend to pass in the following values:
  organization : input from the "organization" search box
  researcher : input from the "researcher name" search box
  topic : input from the "topic keyword" search box
  type : input from the "type" search box (for now, this is always HBCU)

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  """
  institution = request.json.get('organization')
  researcher = request.json.get('researcher')
  researcher = researcher.title()
  type = request.json.get('type')
  topic = request.json.get('topic')
  if institution and researcher and topic:
    results = get_institution_researcher_subfield_results(institution, researcher, topic)
  elif institution and researcher:
    results = get_institution_and_researcher_results(institution, researcher)
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
  return results

def get_researcher_result(researcher):
  """
  Gets the results when user only inputs a researcher
  Uses database to get result, defaults to SPARQL if researcher is not in database

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  (in form of a dictionary)
  """
  data = search_by_author(researcher)
  if data == None:
    print("Using SPARQL...")
    data = get_author_metadata_sparql(researcher)
    if data == {}:
      print("No Results")
      return {}
    topic_list, graph = list_given_researcher_institution(data['oa_link'], data['name'], data['current_institution'])
    results = {"metadata": data, "graph": graph, "list": topic_list}
    return results
  list = []
  metadata = data['author_metadata']

  if metadata['orcid'] is None:
    metadata['orcid'] = ''
  metadata['work_count'] = metadata['num_of_works']
  metadata['current_institution'] = metadata['last_known_institution']
  metadata['cited_by_count'] = metadata['num_of_citations']
  metadata['oa_link'] = metadata['openalex_url']
  if metadata['last_known_institution'] is None:
    institution_object = fetch_last_known_institutions(metadata['oa_link'])
    if institution_object == []:
      last_known_institution = ""
    else:
      institution_object = institution_object[0]
      last_known_institution = institution_object['display_name']
      institution_url = institution_object['id']
  else:
    last_known_institution = metadata['last_known_institution']
  metadata['current_institution'] = last_known_institution
  metadata['institution_url'] = institution_url
  nodes = []
  edges = []
  nodes.append({ 'id': last_known_institution, 'label': last_known_institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{metadata['openalex_url']}-{last_known_institution}""", 'start': metadata['openalex_url'], 'end': last_known_institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': metadata['openalex_url'], 'label': researcher, "type": "AUTHOR"})
  for entry in data['data']:
    topic = entry['topic']
    num_works = entry['num_of_works']
    list.append((topic, num_works))
    nodes.append({'id': topic, 'label': topic, 'type': "TOPIC"})
    number_id = topic + ":" + str(num_works)
    nodes.append({'id': number_id, 'label': num_works, 'type': "NUMBER"})
    edges.append({ 'id': f"""{metadata['openalex_url']}-{topic}""", 'start': metadata['openalex_url'], 'end': topic, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{metadata['openalex_url']}-{number_id}""", 'start': topic, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_institution_results(institution):
  """
  Gets the results when user only inputs an institution
  Uses database to get result, defaults to SPARQL if institution is not in database

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  (in form of a dictionary)
  """
  data = search_by_institution(institution)
  if data == None:
    print("Using SPARQL...")
    data = get_institution_metadata_sparql(institution)
    if data == {}:
      print("No Results")
      return {}
    topic_list, graph = list_given_institution(data['ror'], data['name'], data['oa_link'])
    results = {"metadata": data, "graph": graph, "list": topic_list}
    return results
  list = []
  metadata = data['institution_metadata']
  
  metadata['homepage'] = metadata['url']
  metadata['works_count'] = metadata['num_of_works']
  metadata['name'] = metadata['institution_name']
  metadata['cited_count'] = metadata['num_of_citations']
  metadata['oa_link'] = metadata['openalex_url']
  metadata['author_count'] = metadata['num_of_authors']

  nodes = []
  edges = []
  institution_id = metadata['openalex_url']
  nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
  for entry in data['data']:
    subfield = entry['topic_subfield']
    number = entry['num_of_authors']
    list.append((subfield, number))
    nodes.append({'id': subfield, 'label': subfield, 'type': "TOPIC"})
    number_id = subfield + ":" + str(number)
    nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{institution_id}-{subfield}""", 'start': institution_id, 'end': subfield, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{subfield}-{number_id}""", 'start': subfield, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_subfield_results(topic):
  """
  Gets the results when user only inputs a subfield
  Uses database to get result
  Shouldn't need to default to SPARQL because the database has all subfields already
  Code to get SPARQL results is still here, but commented out

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  (in form of a dictionary)
  """
  data = search_by_topic(topic)
  if data == None:
    """
    ## Get results from subfields with OpenAlex, but shouldn't be necessary because DB has all subfields already.
    data = get_subfield_metadata(topic)
    topic_list, graph, extra_metadata = list_given_topic(topic, data['oa_link'])
    data['work_count'] = extra_metadata['work_count']
    results = {"metadata": data, "graph": graph, "list": topic_list}
    """
    return {"metadata": None, "graph": None, "list": None}
  list = []
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
  nodes.append({ 'id': topic_id, 'label': topic, 'type': 'TOPIC' })
  for entry in data['data']:
    institution = entry['institution_name']
    number = entry['num_of_authors']
    list.append((institution, number))
    nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
    nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{institution}-{topic_id}""", 'start': institution, 'end': topic_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{institution}-{number}""", 'start': institution, 'end': number, "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_researcher_and_subfield_results(researcher, topic):
  """
  Gets the results when user inputs a researcher and subfield
  Uses database to get result, defaults to SPARQL if researcher is not in database

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  (in form of a dictionary)
  """
  data = search_by_author_topic(researcher, topic)
  if data == None:
    print("Using SPARQL...")
    data = get_topic_and_researcher_metadata_sparql(topic, researcher)
    if data == {}:
      print("No Results")
      return {}
    work_list, graph, extra_metadata = list_given_researcher_topic(topic, researcher, data['current_institution'], data['topic_oa_link'], data['researcher_oa_link'], data['institution_oa_link'])
    data['work_count'] = extra_metadata['work_count']
    data['cited_by_count'] = extra_metadata['cited_by_count']
    results = {"metadata": data, "graph": graph, "list": work_list}
    return results
  list = []
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
    institution_object = fetch_last_known_institutions(metadata['researcher_oa_link'])[0]
    metadata['current_institution'] = institution_object['display_name']
  else:
    metadata['current_institution'] = data['author_metadata']['last_known_institution']
  last_known_institution = metadata['current_institution']

  nodes = []
  edges = []
  researcher_id = metadata['researcher_oa_link']
  subfield_id = metadata['topic_oa_link']
  nodes.append({ 'id': last_known_institution, 'label': last_known_institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{researcher_id}-{last_known_institution}""", 'start': researcher_id, 'end': last_known_institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
  nodes.append({ 'id': subfield_id, 'label': topic, 'type': 'TOPIC' })
  edges.append({ 'id': f"""{researcher_id}-{subfield_id}""", 'start': researcher_id, 'end': subfield_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
  for entry in data['data']:
    work = entry['work_name']
    number = entry['num_of_citations']
    list.append((work, number))
    nodes.append({ 'id': work, 'label': work, 'type': 'WORK' })
    nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{researcher_id}-{work}""", 'start': researcher_id, 'end': work, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
    edges.append({ 'id': f"""{work}-{number}""", 'start': work, 'end': number, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_institution_and_subfield_results(institution, topic):
  """
  Gets the results when user inputs an institution and subfield
  Uses database to get result, defaults to SPARQL if institution is not in database

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  (in form of a dictionary)
  """
  data = search_by_institution_topic(institution, topic)
  if data == None:
    print("Using SPARQL...")
    data = get_institution_and_topic_metadata_sparql(institution, topic)
    if data == {}:
      print("No Results")
      return {}
    topic_list, graph, extra_metadata = list_given_institution_topic(institution, data['institution_oa_link'], topic, data['topic_oa_link'])
    data['work_count'] = extra_metadata['work_count']
    data['people_count'] = extra_metadata['num_people']
    results = {"metadata": data, "graph": graph, "list": topic_list}
    return results
  list = []
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
  nodes.append({ 'id': subfield_id, 'label': topic, 'type': 'TOPIC' })
  nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{institution_id}-{subfield_id}""", 'start': institution_id, 'end': subfield_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
  for entry in data['data']:
    author_id = entry['author_id']
    author_name = entry['author_name']
    number = entry['num_of_works']
    list.append((author_name, number))
    nodes.append({ 'id': author_id, 'label': author_name, 'type': 'AUTHOR' })
    nodes.append({ 'id': number, 'label': number, 'type': 'NUMBER' })
    edges.append({ 'id': f"""{author_id}-{number}""", 'start': author_id, 'end': number, "label": "numWorks", "start_type": "AUTHOR", "end_type": "NUMBER"})
    edges.append({ 'id': f"""{author_id}-{institution_id}""", 'start': author_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  graph = {"nodes": nodes, "edges": edges}
  metadata['people_count'] = len(list)
  return {"metadata": metadata, "graph": graph, "list": list}

def get_institution_and_researcher_results(institution, researcher):
  """
  Gets the results when user inputs an institution and researcher
  Uses database to get result, defaults to SPARQL if institution or researcher is not in database

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  (in form of a dictionary)
  """
  data = search_by_author_institution(researcher, institution)
  if data == None:
    print("Using SPARQL...")
    data = get_researcher_and_institution_metadata_sparql(researcher, institution)
    if data == {}:
      print("No Results")
      return {}
    topic_list, graph = list_given_researcher_institution(data['researcher_oa_link'], researcher, institution)
    results = {"metadata": data, "graph": graph, "list": topic_list}
    return results
  list = []
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
  last_known_institution = metadata['current_institution']
  metadata['work_count'] = data['author_metadata']['num_of_works']
  metadata['cited_by_count'] = data['author_metadata']['num_of_citations']

  nodes = []
  edges = []
  author_id = metadata['researcher_oa_link']
  nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{author_id}-{institution}""", 'start': author_id, 'end': institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': author_id, 'label': researcher, "type": "AUTHOR"})
  for entry in data['data']:
    topic_name = entry['topic_name']
    num_works = entry["num_of_works"]
    list.append((topic_name, num_works))
    nodes.append({'id': topic_name, 'label': topic_name, 'type': "TOPIC"})
    number_id = topic_name + ":" + str(num_works)
    nodes.append({'id': number_id, 'label': num_works, 'type': "NUMBER"})
    edges.append({ 'id': f"""{author_id}-{topic_name}""", 'start': author_id, 'end': topic_name, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{topic_name}-{number_id}""", 'start': topic_name, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list": list}

def get_institution_researcher_subfield_results(institution, researcher, topic):
  """
  Gets the results when user inputs an institution, researcher, and subfield
  Uses database to get result, defaults to SPARQL if institution or researcher is not in database

  Returns:
  metadata : the metadata for the search
  graph : the graph for the search in the form {nodes: [], edges: []}
  list : the list view for the search
  (in form of a dictionary)
  """
  data = search_by_author_institution_topic(researcher, institution, topic)
  if data == None:
    print("Using SPARQL...")
    data = get_institution_and_topic_and_researcher_metadata_sparql(institution, topic, researcher)
    if data == {}:
      print("No Results")
      return {}
    work_list, graph, extra_metadata = list_given_researcher_topic(topic, researcher, institution, data['topic_oa_link'], data['researcher_oa_link'], data['institution_oa_link'])
    data['work_count'] = extra_metadata['work_count']
    data['cited_by_count'] = extra_metadata['cited_by_count']
    results = {"metadata": data, "graph": graph, "list": work_list}
    return results
  list = []
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
  last_known_institution = metadata['current_institution']

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
  nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{researcher_id}-{institution_id}""", 'start': researcher_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
  nodes.append({ 'id': subfield_id, 'label': topic, 'type': 'TOPIC' })
  edges.append({ 'id': f"""{researcher_id}-{subfield_id}""", 'start': researcher_id, 'end': subfield_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
  for entry in data['data']:
    work_name = entry['work_name']
    number = entry['cited_by_count']
    list.append((work_name, number))
    nodes.append({ 'id': work_name, 'label': work_name, 'type': 'WORK' })
    nodes.append({'id': number, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{researcher_id}-{work_name}""", 'start': researcher_id, 'end': work_name, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
    edges.append({ 'id': f"""{work_name}-{number}""", 'start': work_name, 'end': number, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return {"metadata": metadata, "graph": graph, "list":list}

def query_SPARQL_endpoint(endpoint_url, query):
  """
  Queries the endpoint to execute the SPARQL query.

  Arguments:
  endpoint_url : string representing the endpoint url
  query : string representing the SPARQL query

  Returns:
  return_value : returns the information as a list of dictionaries
  """
  response = requests.post(endpoint_url, data={"query": query}, headers={'Accept': 'application/json'})
  return_value = []
  data = response.json()
  for entry in data['results']['bindings']:
    my_dict = {}
    for e in entry:
      my_dict[e] = entry[e]['value']
    return_value.append(my_dict)
  return return_value

def get_institution_metadata_sparql(institution):
  """
  Given an institution, queries the SemOpenAlex endpoint to retrieve metadata on the institution

  Returns:
  metadata : information on the institution as a dictionary with the following keys:
    institution, ror, works_count, cited_count, homepage, author_count, oa_link, hbcu
  """

  query = f"""
  SELECT ?ror ?workscount ?citedcount ?homepage ?institution (COUNT(distinct ?people) as ?peoplecount)
  WHERE {'{'}
  ?institution <http://xmlns.com/foaf/0.1/name> "{institution}" .
  ?institution <https://semopenalex.org/ontology/ror> ?ror .
  ?institution <https://semopenalex.org/ontology/worksCount> ?workscount .
  ?institution <https://semopenalex.org/ontology/citedByCount> ?citedcount .
  ?institution <http://xmlns.com/foaf/0.1/homepage> ?homepage .
  ?people <http://www.w3.org/ns/org#memberOf> ?institution .
  {'}'} GROUP BY ?ror ?workscount ?citedcount ?homepage ?institution
  """
  results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
  if results == []:
    print("No Results")
    return {}
  ror = results[0]['ror']
  works_count = results[0]['workscount']
  cited_count = results[0]['citedcount']
  homepage = results[0]['homepage']
  author_count = results[0]['peoplecount']
  oa_link = results[0]['institution']
  oa_link = oa_link.replace('semopenalex', 'openalex').replace('institution', 'institutions')
  hbcu = is_HBCU(oa_link)
  return {"name": institution, "ror": ror, "works_count": works_count, "cited_count": cited_count, "homepage": homepage, "author_count": author_count, 'oa_link': oa_link, "hbcu": hbcu}

def list_given_institution(ror, name, id):
  """
  Uses OpenAlex to determine the subfields which a given institution study.
  Must iterate through all authors related to the institution and determine what topics OA attributes to them.

  Parameters:
  ror : ror of institution
  name : name of institution
  id : id of institution

  Returns:
  sorted_subfields : the subfields which OpenAlex attributes to a given institution
  graph : a graphical representation of the sorted_subfields.
  """
  final_subfield_count = {}
  headers = {'Accept': 'application/json'}
  response = requests.get(f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=*', headers=headers)
  data = response.json()
  authors = data['results']
  next_page = data['meta']['next_cursor']
  while next_page is not None:
    for a in authors:
      topics = a['topics']
      for topic in topics:
        if topic['subfield']['display_name'] in final_subfield_count:
          final_subfield_count[topic['subfield']['display_name']] = final_subfield_count[topic['subfield']['display_name']] + 1
        else:
          final_subfield_count[topic['subfield']['display_name']] = 1
    response = requests.get(f'https://api.openalex.org/authors?per-page=200&filter=last_known_institutions.ror:{ror}&cursor=' + next_page, headers=headers)
    data = response.json()
    authors = data['results']
    next_page = data['meta']['next_cursor']
  sorted_subfields = sorted([(k, v) for k, v in final_subfield_count.items() if v > 5], key=lambda x: x[1], reverse=True)

  nodes = []
  edges = []
  nodes.append({ 'id': id, 'label': name, 'type': 'INSTITUTION' })
  for subfield, number in sorted_subfields:
    nodes.append({'id': subfield, 'label': subfield, 'type': "TOPIC"})
    number_id = subfield + ":" + str(number)
    nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{id}-{subfield}""", 'start': id, 'end': subfield, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{subfield}-{number_id}""", 'start': subfield, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}

  return sorted_subfields, graph

def get_author_metadata_sparql(author):
  """
  Given an author, queries the SemOpenAlex endpoint to retrieve metadata on the author

  Returns:
  metadata : information on the author as a dictionary with the following keys:
    name, cited_by_count, orcid, work_count, current_institution, oa_link, institution_url
  """

  query = f"""
    SELECT ?cite_count ?orcid ?works_count ?current_institution_name ?author ?current_institution
    WHERE {'{'}
    ?author <http://xmlns.com/foaf/0.1/name> "{author}" .
    ?author <https://semopenalex.org/ontology/citedByCount> ?cite_count .
    OPTIONAL {"{"}?author <https://dbpedia.org/ontology/orcidId> ?orcid .{"}"}
    ?author <https://semopenalex.org/ontology/worksCount> ?works_count .
    ?author <http://www.w3.org/ns/org#memberOf> ?current_institution .
    ?current_institution <http://xmlns.com/foaf/0.1/name> ?current_institution_name .
    {'}'}
  """
  results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
  if results == []:
    print("No Results")
    return {}
  cited_by_count = results[0]['cite_count']
  orcid = results[0]['orcid'] if 'orcid' in results[0] else ''
  work_count = results[0]['works_count']
  current_institution = results[0]['current_institution_name']
  oa_link = results[0]['author']
  oa_link = oa_link.replace('semopenalex', 'openalex').replace('author', 'authors')
  institution_link = results[0]['current_institution'].replace('semopenalex', 'openalex').replace('institution', 'institutions')

  return {"name": author, "cited_by_count": cited_by_count, "orcid": orcid, "work_count": work_count, "current_institution": current_institution, "oa_link": oa_link, "institution_url": institution_link}

def get_researcher_and_institution_metadata_sparql(researcher, institution):
  """
  Given an institution and researcher, collects the metadata for the 2 and returns as one dictionary.

  Returns:
  metadata : information on the institution and researcher as a dictionary with the following keys:
    institution_name, researcher_name, homepage, institution_oa_link, researcher_oa_link, orcid, work_count, cited_by_count, ror
  """

  researcher_data = get_author_metadata_sparql(researcher)
  institution_data = get_institution_metadata_sparql(institution)
  if researcher_data == {} or institution_data == {}:
    return {}

  institution_name = institution
  researcher_name = researcher
  institution_url = institution_data['homepage']
  institution_oa = institution_data['oa_link']
  researcher_oa = researcher_data['oa_link']
  orcid = researcher_data['orcid']
  work_count = researcher_data['work_count']
  cited_by_count = researcher_data['cited_by_count']
  ror = institution_data['ror']

  return {"institution_name": institution_name, "researcher_name": researcher_name, "homepage": institution_url, "institution_oa_link": institution_oa, "researcher_oa_link": researcher_oa, "orcid": orcid, "work_count": work_count, "cited_by_count": cited_by_count, "ror": ror}

def list_given_researcher_institution(id, name, institution):
  """
  When an user searches for a researcher only or a researcher and institution.
  Checks OpenAlex for what topics are attributed to the author.

  Parameters:
  institution : id of author's institution
  name : name of author
  id : id of author

  Returns:
  sorted_subfields : the subfields which OpenAlex attributes to a given author
  graph : a graphical representation of the sorted_subfields.
  """
  final_subfield_count = {}
  headers = {'Accept': 'application/json'}
  search_id = id.replace('https://openalex.org/authors/', '')
  response = requests.get(f'https://api.openalex.org/authors/{search_id}', headers=headers)
  data = response.json()
  topics = data['topics']
  for t in topics:
    subfield = t['subfield']['display_name']
    if subfield in final_subfield_count:
      final_subfield_count[subfield] = final_subfield_count[subfield] + t['count']
    else:
      final_subfield_count[subfield] = t['count']
  sorted_subfields = sorted(final_subfield_count.items(), key=lambda x: x[1], reverse=True)

  nodes = []
  edges = []
  nodes.append({ 'id': institution, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{id}-{institution}""", 'start': id, 'end': institution, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': id, 'label': name, "type": "AUTHOR"})
  for s, number in sorted_subfields:
    nodes.append({'id': s, 'label': s, 'type': "TOPIC"})
    number_id = s + ":" + str(number)
    nodes.append({'id': number_id, 'label': number, 'type': "NUMBER"})
    edges.append({ 'id': f"""{id}-{s}""", 'start': id, 'end': s, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
    edges.append({ 'id': f"""{s}-{number_id}""", 'start': s, 'end': number_id, "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}

  return sorted_subfields, graph

def get_subfield_metadata_sparql(subfield):
  """
  Given a subfield, queries the OpenAlex endpoint to retrieve metadata on the subfield
  Doesn't query SemOpenAlex because the necessary data is faster to retrieve from OpenAlex, but this may change
  in the future.

  Researchers does not work as expected at the moment.

  Returns:
  metadata : information on the subfield as a dictionary with the following keys:
    name, topic_clusters, cited_by_count, work_count, researchers, oa_link
  """
  headers = {'Accept': 'application/json'}
  response = requests.get(f'https://api.openalex.org/subfields?filter=display_name.search:{subfield}', headers=headers) 
  data = response.json()['results'][0]
  oa_link = data['id']
  cited_by_count = data['cited_by_count']
  work_count = data['works_count']
  topic_clusters = []
  for topic in data['topics']:
    topic_clusters.append(topic['display_name'])
  researchers = 0
  return {"name": subfield, "topic_clusters": topic_clusters, "cited_by_count": cited_by_count, "work_count": work_count, "researchers": researchers, "oa_link": oa_link}

def list_given_topic(subfield, id):
  """
  When an user searches for a topic only.
  Searches through each HBCU and partner institution and returns which institutions research the subfield.

  Parameters:
  subfield : name of subfield searched
  id : id of the subfield

  Returns:
  subfield_list : the subfields which OpenAlex attributes to a given institution
  graph : a graphical representation of subfield_list.
  """
  headers = {'Accept': 'application/json'}
  subfield_list = []
  extra_metadata = {}
  total_work_count = 0

  for institution in autofill_inst_list:
    response = requests.get(f'https://api.openalex.org/institutions?select=display_name,topics&filter=display_name.search:{institution}', headers=headers)
    try:
      data = response.json()
      data = data['results'][0]
      inst_topics = data['topics']
      count = 0
      for t in inst_topics:
        if t['subfield']['display_name'] == subfield:
          count = count + t['count']
          total_work_count = total_work_count + t['count']
      if count > 0:
        subfield_list.append((institution, count))
    except:
      continue

  subfield_list.sort(key=lambda x: x[1], reverse=True)
  extra_metadata['work_count'] = total_work_count

  nodes = []
  edges = []
  nodes.append({ 'id': id, 'label': subfield, 'type': 'TOPIC' })
  for i, c in subfield_list:
    if not c == 0:
      nodes.append({ 'id': i, 'label': i, 'type': 'INSTITUTION' })
      nodes.append({'id': c, 'label': c, 'type': "NUMBER"})
      edges.append({ 'id': f"""{i}-{id}""", 'start': i, 'end': id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
      edges.append({ 'id': f"""{i}-{c}""", 'start': i, 'end': c, "label": "number", "start_type": "INSTITUTION", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return subfield_list, graph, extra_metadata

def get_institution_and_topic_metadata_sparql(institution, topic):
  """
  Given a topic and institution, collects the metadata for the 2 and returns as one dictionary.

  Returns:
  metadata : information on the topic and institution as a dictionary with the following keys:
    institution_name, topic_name, work_count, cited_by_count, ror, topic_clusters, people_count, topic_oa_link, institution_oa_link, homepage
  """
  institution_data = get_institution_metadata_sparql(institution)
  topic_data = get_subfield_metadata_sparql(topic)
  if topic_data == {} or institution_data == {}:
    return {}

  institution_name = institution
  subfield_name = topic
  ror = institution_data['ror']
  topic_cluster = topic_data['topic_clusters']
  topic_oa = topic_data['oa_link']
  institution_oa = institution_data['oa_link']
  institution_url = institution_data['homepage']
  work_count = institution_data['works_count']
  cited_by_count = institution_data['cited_count']
  people_count = institution_data['author_count']
  return {"institution_name": institution_name, "topic_name": subfield_name, "work_count": work_count, "cited_by_count": cited_by_count, "ror": ror, "topic_clusters": topic_cluster, "people_count": people_count, "topic_oa_link": topic_oa, "institution_oa_link": institution_oa, "homepage": institution_url}

def list_given_institution_topic(institution, institution_id, subfield, subfield_id):
  """
  When an user searches for an institution and topic
  Uses a SemOpenAlex query to retrieve authors who work at the given institution and have published
  papers relating to the provided subfield.
  Collects the names of the authors and the number of works.

  Parameters:
  institution : name of institution
  institudion_id : OpenAlex id for institution
  subfield : name of subfield
  subfield_id : OpenAlex id for subfield

  Returns:
  final_list : List of works by the author with the given subfield.
  graph : a graphical representation of final_list.
  extra_metadata : some extra metadata, specifically the work_count and cited_by_count for this specific topic.
  """

  query = f"""
  SELECT DISTINCT ?author ?name (GROUP_CONCAT(DISTINCT ?work; SEPARATOR=", ") AS ?works) WHERE {"{"}
  ?institution <http://xmlns.com/foaf/0.1/name> "{institution}" .
  ?author <http://www.w3.org/ns/org#memberOf> ?institution .
  ?author <http://xmlns.com/foaf/0.1/name> ?name .
  ?work <http://purl.org/dc/terms/creator> ?author .
  ?subfield a <https://semopenalex.org/ontology/Subfield> .
  ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{subfield}" .
  ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
  << ?work <https://semopenalex.org/ontology/hasTopic> ?topic >> ?p ?o .
  {"}"}
  GROUP BY ?author ?name
  """
  results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
  works_list = []
  final_list = []
  work_count = 0
  for a in results:
    works_list.append((a['author'], a['name'], a['works'].count(",") + 1))
    final_list.append((a['name'], a['works'].count(",") + 1))
    work_count = work_count + a['works'].count(",") + 1
  # Limits to authors with more than 3 works if at least 5 of these authors exist
  final_list_check = sorted([(k, v) for k, v in final_list if v > 3], key=lambda x: x[1], reverse=True)
  final_list.sort(key=lambda x: x[1], reverse=True)
  num_people = len(final_list)
  """
  if len(final_list_check) >= 5:
    final_list = final_list_check
  """

  nodes = []
  edges = []
  nodes.append({ 'id': subfield_id, 'label': subfield, 'type': 'TOPIC' })
  nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{institution_id}-{subfield_id}""", 'start': institution_id, 'end': subfield_id, "label": "researches", "start_type": "INSTITUTION", "end_type": "TOPIC"})
  for a in works_list:
    author_name = a[1]
    author_id = a[0]
    num_works = a[2]
    nodes.append({ 'id': author_id, 'label': author_name, 'type': 'AUTHOR' })
    nodes.append({ 'id': num_works, 'label': num_works, 'type': 'NUMBER' })
    edges.append({ 'id': f"""{author_id}-{num_works}""", 'start': author_id, 'end': num_works, "label": "numWorks", "start_type": "AUTHOR", "end_type": "NUMBER"})
    edges.append({ 'id': f"""{author_id}-{institution_id}""", 'start': author_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  return final_list, {"nodes": nodes, "edges": edges}, {"num_people": num_people, "work_count": work_count}

def get_topic_and_researcher_metadata_sparql(topic, researcher):
  """
  Given a topic and researcher, collects the metadata for the 2 and returns as one dictionary.

  Returns:
  metadata : information on the topic and researcher as a dictionary with the following keys:
    researcher_name, topic_name, orcid, current_institution, work_count, cited_by_count, topic_clusters, researcher_oa_link, topic_oa_link
  """

  researcher_data = get_author_metadata_sparql(researcher)
  topic_data = get_subfield_metadata_sparql(topic)
  if researcher_data == {} or topic_data == {}:
    return {}

  researcher_name = researcher
  subfield_name = topic
  orcid = researcher_data['orcid']
  current_org = researcher_data['current_institution']
  work_count = researcher_data['work_count']
  cited_by_count = researcher_data['cited_by_count']
  topic_cluster = topic_data['topic_clusters']
  researcher_oa = researcher_data['oa_link']
  topic_oa = topic_data['oa_link']
  institution_oa = researcher_data['institution_url']
  return {"researcher_name": researcher_name, "topic_name": subfield_name, "orcid": orcid, "current_institution": current_org, "work_count": work_count, "cited_by_count": cited_by_count, "topic_clusters": topic_cluster, "researcher_oa_link": researcher_oa, "topic_oa_link": topic_oa, "institution_oa_link": institution_oa}

def list_given_researcher_topic(subfield, researcher, institution, subfield_id, researcher_id, institution_id):
  """
  When an user searches for a researcher and topic or all three.
  Uses SemOpenAlex to retrieve the works of the researcher which relate to the subfield
  Uses OpenAlex to get all institutions (if all_institutions is False)

  Parameters:
  subfield : name of subfield searched
  researcher : name of researcher
  subfield_id : OpenAlex ID for subfield
  researcher_id : OpenAlex ID for researcher
  all_institutions = True : Do we include all of the author's past institutions, or only the one the user searched for

  Returns:
  final_work_list : List of works by the author with the given subfield.
  graph : a graphical representation of final_work_list.
  extra_metadata : some extra metadata, specifically the work_count and cited_by_count for this specific subfield.
  """

  query = f"""
  SELECT DISTINCT ?work ?name ?cited_by_count WHERE {"{"}
  ?author <http://xmlns.com/foaf/0.1/name> "{researcher}" .
  ?work <http://purl.org/dc/terms/creator> ?author .
  << ?work <https://semopenalex.org/ontology/hasTopic> ?topic >> ?p ?o .
  ?topic <http://www.w3.org/2004/02/skos/core#broader> ?subfield .
  ?subfield <http://www.w3.org/2004/02/skos/core#prefLabel> "{subfield}" .
  ?work <http://purl.org/dc/terms/title> ?name .
  ?work <https://semopenalex.org/ontology/citedByCount> ?cited_by_count .
  {'}'}
  """
  results = query_SPARQL_endpoint(SEMOPENALEX_SPARQL_ENDPOINT, query)
  work_list = []
  for a in results:
    work_list.append((a['work'], a['name'], int(a['cited_by_count'])))
  final_work_list = []
  for a in work_list:
    final_work_list.append((a[1], a[2]))
  final_work_list.sort(key=lambda x: x[1], reverse=True)

  nodes = []
  edges = []
  print(institution_id, institution)
  nodes.append({ 'id': institution_id, 'label': institution, 'type': 'INSTITUTION' })
  edges.append({ 'id': f"""{researcher_id}-{institution_id}""", 'start': researcher_id, 'end': institution_id, "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"})
  nodes.append({ 'id': researcher_id, 'label': researcher, 'type': 'AUTHOR' })
  nodes.append({ 'id': subfield_id, 'label': subfield, 'type': 'TOPIC' })
  edges.append({ 'id': f"""{researcher_id}-{subfield_id}""", 'start': researcher_id, 'end': subfield_id, "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
  cited_by_count = 0
  for id, w, c in work_list:
    cited_by_count = cited_by_count + c
    if not c == 0:
      nodes.append({ 'id': id, 'label': w, 'type': 'WORK' })
      nodes.append({'id': c, 'label': c, 'type': "NUMBER"})
      edges.append({ 'id': f"""{researcher_id}-{id}""", 'start': researcher_id, 'end': id, "label": "authored", "start_type": "AUTHOR", "end_type": "WORK"})
      edges.append({ 'id': f"""{id}-{c}""", 'start': id, 'end': c, "label": "citedBy", "start_type": "WORK", "end_type": "NUMBER"})
  graph = {"nodes": nodes, "edges": edges}
  return final_work_list, graph, {"work_count": len(final_work_list), "cited_by_count": cited_by_count}

def get_institution_and_topic_and_researcher_metadata_sparql(institution, topic, researcher):
  """
  Given an institution, topic, and researcher, collects the metadata for the 3 and returns as one dictionary.

  Returns:
  metadata : information on the institution, topic, and researcher as a dictionary with the following keys:
    institution_name, topic_name, researcher_name, topic_oa_link, institution_oa_link, homepage, orcid, topic_clusters, researcher_oa_link, work_count, cited_by_count, ror
  """

  institution_data = get_institution_metadata_sparql(institution)
  topic_data = get_subfield_metadata_sparql(topic)
  researcher_data = get_author_metadata_sparql(researcher)
  if researcher_data == {} or institution_data == {} or topic_data == {}:
    return {}

  institution_url = institution_data['homepage']
  orcid = researcher_data['orcid']
  work_count = researcher_data['work_count']
  cited_by_count = researcher_data['cited_by_count']
  topic_cluster = topic_data['topic_clusters']
  topic_oa = topic_data['oa_link']
  institution_oa = institution_data['oa_link']
  researcher_oa = researcher_data['oa_link']
  ror = institution_data['ror']

  return {"institution_name": institution, "topic_name": topic, "researcher_name": researcher, "topic_oa_link": topic_oa, "institution_oa_link": institution_oa, "homepage": institution_url, "orcid": orcid, "topic_clusters": topic_cluster, "researcher_oa_link": researcher_oa, "work_count": work_count, "cited_by_count": cited_by_count, 'ror': ror}

def query_SQL_endpoint(connection, query):
  """
  Queries the endpoint to execute the SQL query.

  Arguments:
  connection : connection object representing the MySQL database connection 
  query : string representing the SQL query

  Returns:
  return_value : returns the information as a list of tuples
  """

  cursor = connection.cursor()
  try:
      cursor.execute(query)
      result = cursor.fetchall()
      return result
  except Error as e:
      print(f"The error '{e}' occurred")

@app.route('/autofill-institutions', methods=['POST'])
def autofill_institutions():
  """
  Handles autofill for instituions. Checks what institutions contain the phrase the user has already typed.

  Expects the frontend to pass in the following values:
  institution : what the user has typed into the organization box so far.

  Returns:
  A dictionary containing all the possible searches given what the user has typed.
  """
  inst = request.json.get('institution')
  possible_searches = []
  for i in autofill_inst_list:
    if inst.lower() in i.lower():
      possible_searches.append(i)
  return {"possible_searches": possible_searches}

@app.route('/autofill-topics', methods=['POST'])
def autofill_topics():
  """
  Handles autofill for topics. Checks what topics contain the phrase the user has already typed.
  Only searches if the user has typed in more than 2 characters in order to prevent the entire (large) keyword list from
  being returned.

  Expects the frontend to pass in the following values:
  topic : what the user has typed into the Topic Keyword box so far.

  Returns:
  A dictionary containing all the possible searches given what the user has typed.
  """
  topic = request.json.get('topic')
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
  return {"possible_searches": possible_searches}

@app.route('/get-default-graph', methods=['POST'])
def get_default_graph():
  """
  Returns the default graph. This is what the user sees if they do not fill in any of the search boxes.
  Loads the graph from the file default.json, which already contains all the necessary data.

  Returns:
  graph : returns a dictionary with one entry, the graph. The graph is in the same form as all others ({"nodes": [], "edges": []})
  """

  with open("default.json", "r") as file:
    graph = json.load(file)
  nodes = []
  edges = []
  cur_nodes = graph['nodes']
  cur_edges = graph['edges']
  most = {}
  needed_topics = set()
  for edge in cur_edges:
    if edge['start'] in most:
      if edge['connecting_works'] > most[edge['start']]:
        most[edge['start']] = edge['connecting_works']
    else:
      most[edge['start']] = edge['connecting_works']
  for edge in cur_edges:
    if most[edge['start']] == edge['connecting_works']:
      edges.append(edge)
      needed_topics.add(edge['end'])
  for node in cur_nodes:
    if node['type'] == 'TOPIC':
      if node['id'] in needed_topics:
        nodes.append(node)
    else:
      nodes.append(node)
  final_graph = {"nodes": nodes, "edges": edges}
  count = 0
  for a in cur_nodes:
    if a['type'] == "INSTITUTION":
      count = count + 1
  return {"graph": final_graph}

@app.route('/get-topic-space-default-graph', methods=['POST'])
def get_topic_space():
  """
  Returns the default graph for the topic space. This is what the user sees if they click "explore topics".
  Simply includes the 4 high level domain from OpenAlex.

  Returns:
  graph : returns a dictionary with one entry, the graph. The graph is in the same form as all others ({"nodes": [], "edges": []})
  """
  nodes= [{ "id": 1, 'label': "Physical Sciences", 'type': 'DOMAIN'}, { "id": 2, 'label': "Life Sciences", 'type': 'DOMAIN'}, { "id": 3, 'label': "Social Sciences", 'type': 'DOMAIN'}, { "id": 4, 'label': "Health Sciences", 'type': 'DOMAIN'}]
  edges = []
  graph = {"nodes": nodes, "edges": edges}
  return {"graph": graph}

@app.route('/search-topic-space', methods=['POST'])
def search_topic_space():
  """
  Api call for searches from the user when searching the topic space. Retrieves information from the topic_default.json file,
  which contains the OpenAlex topic space. Returns the result as a graph.

  topic : input from the topic search box.

  Returns:
  graph : the graph for the search in the form {nodes: [], edges: []}
  """
  search = request.json.get('topic')
  with open('topic_default.json', 'r') as file:
    graph = json.load(file)
  nodes = []
  edges = []
  for node in graph['nodes']:
    node_additions = []
    edge_additions = []
    if node['label'] == search or node['subfield_name'] == search or node['field_name'] == search or node['domain_name'] == search or search in node['keywords'].split("; "):
      topic_node = { 'id': node['id'], 'label': node['label'], 'type': 'TOPIC', "keywords":node['keywords'], "summary": node['summary'], "wikipedia_url": node['wikipedia_url']}
      node_additions.append(topic_node)
      subfield_node = { "id": node["subfield_id"], 'label': node['subfield_name'], 'type': 'SUBFIELD'}
      node_additions.append(subfield_node)
      field_node = { "id": node["field_id"], 'label': node['field_name'], 'type': 'FIELD'}
      node_additions.append(field_node)
      domain_node = { "id": node["domain_id"], 'label': node['domain_name'], 'type': 'DOMAIN'}
      node_additions.append(domain_node)
      topic_subfield = { 'id': f"""{node['id']}-{node['subfield_id']}""" ,'start': node['id'], 'end': node['subfield_id'], "label": "hasSubfield", "start_type": "TOPIC", "end_type": "SUBFIELD"}
      edge_additions.append(topic_subfield)
      subfield_field = { 'id': f"""{node['subfield_id']}-{node['field_id']}""" ,'start': node['subfield_id'], 'end': node['field_id'], "label": "hasField", "start_type": "SUBFIELD", "end_type": "FIELD"}
      edge_additions.append(subfield_field)
      field_domain = { 'id': f"""{node['field_id']}-{node['domain_id']}""" ,'start': node['field_id'], 'end': node['domain_id'], "label": "hasDomain", "start_type": "FIELD", "end_type": "DOMAIN"}
      edge_additions.append(field_domain)
    for a in node_additions:
      if a not in nodes:
        nodes.append(a)
    for a in edge_additions:
      if a not in edges:
        edges.append(a)
  final_graph = {"nodes": nodes, "edges": edges}
  return {'graph': final_graph}

def create_connection(host_name, user_name, user_password, db_name):
  """Create a sql database connection and return the connection object."""
  connection = None
  try:
      connection = mysql.connector.connect(
          host=host_name,
          user=user_name,
          passwd=user_password,
          database=db_name
      )
      print("Connection to MySQL DB successful")
  except Error as e:
      print(f"The error '{e}' occurred")

  return connection

def is_HBCU(id):
  """
  Checks the sql database to determine if the id corresponds to an HBCU, as OpenAlex does not contain this information.

  Parameters:
  id : OpenAlex id of an institution

  Returns:
  True is the openalex id corresponds to an HBCU, false otherwise.
  """
  connection = create_connection('openalexalpha.mysql.database.azure.com', 'openalexreader', 'collabnext2024reader!', 'openalex')
  id = id.replace('https://openalex.org/institutions/', "")
  query = f"""SELECT HBCU FROM institutions_filtered WHERE id = "{id}";"""
  result = query_SQL_endpoint(connection, query)
  if result == [(1,)]:
    return True
  else:
    return False

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run()
