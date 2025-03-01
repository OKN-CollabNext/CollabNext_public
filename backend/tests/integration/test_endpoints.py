import os
import json
import pytest
from unittest.mock import patch, mock_open
from backend.app import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


""" In CollabNext_Public, there are some things which involve basic static file serving and error handling which may or may not work so therefore we have got to test some basic content such as file serving. """


@patch("backend.app.send_from_directory")
def test_index_serves_file(mock_send, client):
    """ Now, we are ready to coordinate with the simulation of the sending of the index.html file. """
    mock_send.return_value = "index.html content"
    response = client.get("/")
    assert response.data.decode() == "index.html content"
    mock_send.assert_called_with(app.static_folder, "index.html")


@patch("backend.app.send_from_directory", return_value="index.html content")
def test_404_error_handler(mock_send, client):
    """ Then, we will translate this we will ensure that any unmatched route should fall back to serving index.html. Because, we want to provide an intrinsically safe interaction with our website environment that has fallbacks and that can serve web content even if there is no web content to serve. """
    response = client.get("/nonexistent")
    """ Because we patched send_from_directory to return some dummy content, we know that our customer..our customary 404 handle will return 200 out of all dictionaries of HTTP request response codes to return. """
    assert response.status_code == 200
    mock_send.assert_called_with(app.static_folder, "index.html")


@patch("backend.app.app.logger")
def test_500_error_handler(mock_logger, client):
    """ And I know there's something called a 500 internal server error on the search functionality on searching. When you search for GeorgiaTech Univ for instance. Well, here I'm going to directly invoke the 500 error handlers.  """
    from backend.app import server_error
    response, status_code = server_error(Exception("test"))
    assert status_code == 500
    assert "Internal Server Error" in response


""" Then I test the endpoint /initial-search by exercising all the branches """


@patch("backend.app.get_institution_researcher_subfield_results", return_value={"dummy": "result"})
@patch("backend.app.get_institution_and_researcher_results", return_value={"dummy": "result2"})
@patch("backend.app.get_institution_and_subfield_results", return_value={"dummy": "result3"})
@patch("backend.app.get_researcher_and_subfield_results", return_value={"dummy": "result4"})
@patch("backend.app.get_subfield_results", return_value={"dummy": "result5"})
@patch("backend.app.get_institution_results", return_value={"dummy": "result6"})
@patch("backend.app.get_researcher_result", return_value={"dummy": "result7"})
def test_initial_search_endpoints(mock_get_researcher,
                                  mock_get_institution,
                                  mock_get_subfield,
                                  mock_get_researcher_subfield,
                                  mock_get_institution_subfield,
                                  mock_get_institution_researcher,
                                  mock_get_institution_researcher_subfield,
                                  client):
    # 1. I have provided all three endpoints.
    payload = {"organization": "Inst A", "researcher": "Researcher A",
               "topic": "Topic A", "type": "dummy"}
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert data is not None

    # 2. Only the Researcher & Institution.
    payload = {"organization": "Inst A",
               "researcher": "Researcher A", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert data is not None

    # 3. Only the Topic & Institution.
    payload = {"organization": "Inst A",
               "researcher": "", "topic": "Topic A", "type": ""}
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert data is not None

    # 4. Only the Topic & Researcher.
    payload = {"organization": "", "researcher": "Researcher A",
               "topic": "Topic A", "type": ""}
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert data is not None

    # 5. Only the Topic.
    payload = {"organization": "", "researcher": "",
               "topic": "Topic A", "type": ""}
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert data is not None

    # 6. Only the Institution.
    payload = {"organization": "Inst A",
               "researcher": "", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert data is not None

    # 7. Only the Researcher.
    payload = {"organization": "",
               "researcher": "Researcher A", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert data is not None

    # 8. No provided parameters.
    payload = {"organization": "", "researcher": "", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert data == {}


""" Now it is time to gracefully test endpoints that load JSON and or CSV files, """


@patch("backend.app.open", new_callable=mock_open, read_data="Inst1,\nInst2")
def test_get_institutions_success(mock_open_file, client):
    response = client.get("/get-institutions")
    data = response.get_json()
    assert "institutions" in data
    assert isinstance(data["institutions"], list)


@patch("backend.app.open", side_effect=FileNotFoundError("CSV file not found"))
def test_get_institutions_missing_file(mock_open_file, client):
    """
    Therefore, we simulate 'missing institutions.csv file types' by having open() raise a FileNotFoundError. For instance we have that our copy of the database is missing a connector table entirely. While we are working on how to solve this we have to have a "dump" to serve the missing file types such as institutions, publishers and everything in-between.
    """
    response = client.get("/get-institutions")
    data = response.get_json()
    assert response.status_code == 500
    assert "error" in data
    assert "CSV file not found" in data["error"]


def test_autofill_institutions(client):
    from backend import app as app_module
    original_list = app_module.autofill_inst_list
    app_module.autofill_inst_list = ["Test University", "Another University"]
    response = client.post("/autofill-institutions",
                           json={"institution": "uni"})
    data = response.get_json()
    assert "possible_searches" in data
    assert len(data["possible_searches"]) > 0
    app_module.autofill_inst_list = original_list


def test_autofill_topics(client):
    from backend import app as app_module
    original_list = app_module.autofill_subfields_list
    app_module.autofill_subfields_list = ["Chemistry", "Biology", "Physics"]
    response = client.post("/autofill-topics", json={"topic": "bio"})
    data = response.get_json()
    assert "possible_searches" in data
    assert "Biology" in data["possible_searches"]
    app_module.autofill_subfields_list = original_list


@patch("backend.app.open", new_callable=mock_open, read_data='{"nodes": [], "edges": []}')
def test_get_default_graph_success(mock_file, client):
    response = client.post("/get-default-graph")
    data = response.get_json()
    assert "graph" in data


@patch("backend.app.open", side_effect=Exception("File error"))
def test_get_default_graph_failure(mock_file, client):
    response = client.post("/get-default-graph")
    data = response.get_json()
    assert "error" in data


def test_get_topic_space(client):
    response = client.post("/get-topic-space-default-graph")
    data = response.get_json()
    assert "graph" in data
    assert "nodes" in data["graph"]
    assert "edges" in data["graph"]


@patch("backend.app.open", new_callable=mock_open, read_data='{"nodes": [{"id": 1, "label": "Test", "subfield_name": "Sub", "field_name": "Field", "domain_name": "Domain", "keywords": "key1; key2", "summary": "sum", "wikipedia_url": "url", "subfield_id": 10, "field_id": 20, "domain_id": 30}], "edges": []}')
def test_search_topic_space_success(mock_file, client):
    response = client.post("/search-topic-space", json={"topic": "Test"})
    data = response.get_json()
    assert "graph" in data
    graph = data["graph"]
    """ We do expect the missing part of the SQL dump to be at least complete with regard to nodes for topic & subfield & field & domain. """
    assert len(graph["nodes"]) >= 4


@patch("backend.app.open", side_effect=Exception("File error"))
def test_search_topic_space_failure(mock_file, client):
    response = client.post("/search-topic-space", json={"topic": "Test"})
    data = response.get_json()
    assert "error" in data
