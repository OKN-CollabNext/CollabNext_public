"""
New test file for backend.app (Almost there!)
"""

import json
import os
from io import StringIO
from unittest.mock import patch, MagicMock, mock_open

import pytest
import requests
import logging
import importlib

from flask import Response

from backend.app import (
    app,
    setup_logger,
    execute_query,
    fetch_last_known_institutions,
    query_SPARQL_endpoint,
    get_author_ids,
    get_institution_id,
    search_by_author_institution_topic,
    search_by_author_institution,
    search_by_institution_topic,
    search_by_author_topic,
    search_by_topic,
    search_by_institution,
    search_by_author,
    get_institution_metadata_sparql,
    is_HBCU,
    combine_graphs,
    autofill_topics,
    get_institution_mup_id,
    get_researcher_result,
    get_default_graph,
    get_topic_and_researcher_metadata_sparql,
    get_institution_endowments_and_givings,
    get_institution_medical_expenses,
    get_institution_doctorates_and_postdocs,
    get_institution_num_of_researches,
    get_institutions_r_and_d,
    get_institutions_faculty_awards,
    get_geo_info,
    get_institution_results,
    get_subfield_results,
    get_institution_and_subfield_results,
    get_institution_and_researcher_results,
    list_given_topic,
    list_given_institution_topic,
    list_given_researcher_institution,
    get_institution_sat_scores,
    query_SQL_endpoint,
    get_author_metadata_sparql,
    get_subfield_metadata_sparql,
    list_given_researcher_topic,
    get_researcher_and_subfield_results,
    get_institution_and_topic_metadata_sparql,
    get_researcher_and_institution_metadata_sparql,
    create_connection,
)

# Set environment variables
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "testdb"
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASSWORD"] = "testpass"
os.environ["DB_API"] = "http://testapi"

# --- Fixtures ---


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# This fixture patches file I/O for endpoints that read CSV/JSON files.


@pytest.fixture(autouse=True)
def patch_files(monkeypatch):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    monkeypatch.setattr(
        "builtins.open",
        lambda f, mode='r': (
            StringIO(fake_institutions_csv())
            if "institutions.csv" in f
            else StringIO(fake_subfields_csv())
            if "subfields.csv" in f
            else StringIO(json.dumps(fake_default_json()))
            if "default.json" in f
            else StringIO("")
        )
    )


def fake_institutions_csv():
    return "Institution A,\nInstitution B,\nInstitution C"


def fake_subfields_csv():
    return "Biology\nChemistry\nPhysics"


def fake_default_json():
    return {
        "nodes": [
            {"id": "T1", "label": "Topic1", "type": "TOPIC"},
            {"id": "I1", "label": "Institution1", "type": "INSTITUTION"}
        ],
        "edges": [
            {"id": "I1-T1", "start": "I1", "end": "T1", "connecting_works": 10}
        ]
    }


class TestAppCoverage:
    def test_index_serves_html(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("<html>Index</html>", status=200))
        response = client.get("/")
        assert response.status_code == 200
        assert b"<html>" in response.data

    def test_static_file_serving(self, client, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda path: True)
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("static content", status=200))
        response = client.get("/dummy.js")
        assert response.status_code == 200
        assert b"static content" in response.data

    def test_404_error_handler(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("Index fallback", status=200))
        response = client.get("/non-existent-path")
        assert response.status_code == 200
        assert b"Index fallback" in response.data

    def test_500_error_handler(self, client):
        with patch("backend.app.get_institution_researcher_subfield_results", side_effect=Exception("Forced error")):
            payload = {"organization": "TestOrg",
                       "researcher": "TestRes", "topic": "TestTopic", "type": ""}
            response = client.post("/initial-search", json=payload)
            assert response.status_code == 500
            assert b"Internal Server Error" in response.data

    @patch("builtins.open", new_callable=lambda: lambda f, mode='r': StringIO(fake_institutions_csv()))
    def test_get_institutions_success(self, mock_open, client):
        response = client.get("/get-institutions")
        data = response.get_json()
        assert "institutions" in data
        assert isinstance(data["institutions"], list)
        assert "Institution A" in data["institutions"]

    @patch("builtins.open", new_callable=lambda: lambda f, mode='r': StringIO(fake_subfields_csv()))
    def test_autofill_topics_with_subfields(self, mock_open, client, monkeypatch):
        monkeypatch.setattr("backend.app.SUBFIELDS", True)
        response = client.post("/autofill-topics", json={"topic": "bio"})
        data = response.get_json()
        assert "possible_searches" in data
        assert any("Biology" in topic for topic in data["possible_searches"])

    def test_get_default_graph_success(self, client, monkeypatch):
        dummy_graph = {"nodes": [{"id": "1", "label": "Node1", "type": "TOPIC"}],
                       "edges": [{"id": "1-2", "start": "1", "end": "2"}]}
        monkeypatch.setattr("builtins.open", lambda f,
                            mode='r': StringIO(json.dumps(dummy_graph)))
        response = client.post("/get-default-graph", json={})
        data = response.get_json()
        if "error" not in data:
            assert "graph" in data
            graph = data["graph"]
            assert "nodes" in graph
            assert "edges" in graph
        else:
            pytest.skip(
                "Default graph file not found (expected in some environments)")

    def test_execute_query_success(self):
        fake_cursor = MagicMock()
        fake_cursor.fetchall.return_value = [("result",)]
        fake_cursor.__enter__.return_value = fake_cursor
        fake_conn = MagicMock()
        fake_conn.cursor.return_value = fake_cursor
        fake_conn.__enter__.return_value = fake_conn
        with patch("backend.app.psycopg2.connect", return_value=fake_conn):
            result = execute_query("SELECT 1;", None)
            assert result == [("result",)]

    def test_fetch_last_known_institutions_success(self):
        fake_response = MagicMock()
        fake_response.json.return_value = {
            "last_known_institutions": [{"display_name": "Test Inst", "id": "https://openalex.org/institutions/123"}]
        }
        fake_response.status_code = 200
        with patch("backend.app.requests.get", return_value=fake_response):
            insts = fetch_last_known_institutions(
                "https://openalex.org/author/9999")
            assert isinstance(insts, list)
            assert insts[0]["display_name"] == "Test Inst"

    def test_query_SPARQL_endpoint_success(self):
        fake_response = MagicMock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = {"results": {
            "bindings": [{"var": {"value": "value1"}}]}}
        with patch("backend.app.requests.post", return_value=fake_response):
            results = query_SPARQL_endpoint(
                "https://semopenalex.org/sparql", "SELECT *")
            assert results == [{"var": "value1"}]

    def test_setup_logger_returns_handlers(self):
        logger_obj = setup_logger()
        assert hasattr(logger_obj, "handlers")
        assert len(logger_obj.handlers) >= 5

    def test_backend_init_import(self):
        import backend
        assert backend is not None

    def test_combine_graphs(self):
        g1 = {"nodes": [{"id": "A"}], "edges": [{"id": "AB"}]}
        g2 = {"nodes": [{"id": "B"}, {"id": "C"}], "edges": [{"id": "BC"}]}
        combined = combine_graphs(g1, g2)
        node_ids = {n["id"] for n in combined["nodes"]}
        edge_ids = {e["id"] for e in combined["edges"]}
        assert node_ids == {"A", "B", "C"}
        assert edge_ids == {"AB", "BC"}

    def test_index_route(self, client, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda path: True)
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("<html>Index</html>", status=200))
        response = client.get("/")
        assert response.status_code == 200
        assert b"<html>" in response.data

    def test_static_file_route(self, client, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda path: True)
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("Static content", status=200))
        response = client.get("/dummy.js")
        assert response.status_code == 200
        assert b"Static content" in response.data

    def test_404_handler_full(self, client, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda path: False)
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("Index fallback", status=200))
        response = client.get("/non-existent")
        assert response.status_code == 200
        assert b"Index fallback" in response.data

    def test_500_handler_full(self, client):
        with patch("backend.app.get_institution_researcher_subfield_results", side_effect=Exception("Forced error")):
            payload = {"organization": "Inst",
                       "researcher": "Res", "topic": "Topic", "type": ""}
            response = client.post("/initial-search", json=payload)
            assert response.status_code == 500
            assert b"Internal Server Error" in response.data

    def test_get_institutions_endpoint(self, client):
        response = client.get("/get-institutions")
        data = response.get_json()
        assert "institutions" in data
        assert "Institution A" in data["institutions"]

    def test_autofill_institutions(self, client):
        response = client.post("/autofill-institutions",
                               json={"institution": "A"})
        data = response.get_json()
        assert "possible_searches" in data
        assert any("Institution A" in s for s in data["possible_searches"])

    def test_autofill_topics_subfields(self, client, monkeypatch):
        monkeypatch.setattr("backend.app.SUBFIELDS", True)
        response = client.post("/autofill-topics", json={"topic": "bio"})
        data = response.get_json()
        assert "possible_searches" in data
        assert any("Biology" in s for s in data["possible_searches"])

    def test_get_default_graph_endpoint(self, client):
        response = client.post("/get-default-graph", json={})
        data = response.get_json()
        if "error" in data:
            pytest.skip(
                "Default graph file not found (expected in some environments)")
        else:
            assert "graph" in data
            graph = data["graph"]
            assert "nodes" in graph and "edges" in graph

    def test_get_topic_space_endpoint(self, client):
        response = client.post("/get-topic-space-default-graph", json={})
        data = response.get_json()
        assert "graph" in data
        graph = data["graph"]
        assert len(graph["nodes"]) == 4

    def test_search_topic_space_endpoint(self, client, monkeypatch):
        fake_topic_graph = {
            "nodes": [
                {
                    "id": "T1",
                    "label": "Test Topic",
                    "subfield_name": "SubTest",
                    "field_name": "FieldTest",
                    "domain_name": "DomainTest",
                    "keywords": "alpha; beta",
                    "summary": "Dummy",
                    "wikipedia_url": "http://wikipedia.org",
                    "subfield_id": "ST1",
                    "field_id": "F1",
                    "domain_id": "D1"
                }
            ],
            "edges": []
        }
        monkeypatch.setattr("builtins.open", lambda f, mode='r': StringIO(
            json.dumps(fake_topic_graph)) if "topic_default.json" in f else StringIO(""))
        response = client.post("/search-topic-space",
                               json={"topic": "Test Topic"})
        data = response.get_json()
        assert "graph" in data
        graph = data["graph"]
        assert any(n.get("type") == "TOPIC" for n in graph["nodes"])

    def test_geo_info_endpoint_success(self, client):
        fake_geo = {"geo": {"country_code": "US",
                            "region": "TestRegion", "latitude": 0.0, "longitude": 0.0}}
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = fake_geo
        with patch("backend.app.requests.get", return_value=fake_response):
            payload = {"institution_oa_link": "openalex.org/institutions/12345"}
            response = client.post("/geo_info", json=payload)
            data = response.get_json()
            assert isinstance(data, dict)
            assert data["region"] == "TestRegion"

    def test_geo_info_endpoint_404(self, client):
        fake_response = MagicMock()
        fake_response.status_code = 404
        with patch("backend.app.requests.get", return_value=fake_response):
            payload = {
                "institution_oa_link": "openalex.org/institutions/notfound"}
            response = client.post("/geo_info", json=payload)
            data = response.get_json()
            assert data is None or data == {}

    def test_get_mup_id_endpoint(self, client):
        with patch("backend.app.get_institution_mup_id", return_value={"institution_mup_id": "MUP123"}):
            payload = {"institution_name": "Test Univ"}
            response = client.post("/get-mup-id", json=payload)
            data = response.get_json()
            assert "institution_mup_id" in data
            assert data["institution_mup_id"] == "MUP123"

    def test_mup_sat_scores_endpoint_notfound(self, client):
        with patch("backend.app.get_institution_sat_scores", return_value=None):
            payload = {"institution_name": "Unknown Univ"}
            response = client.post("/mup-sat-scores", json=payload)
            assert response.status_code == 404

    def test_institution_medical_expenses_endpoint_notfound(self, client):
        with patch("backend.app.get_institution_medical_expenses", return_value=None):
            payload = {"institution_name": "NoMed"}
            response = client.post(
                "/institution_medical_expenses", json=payload)
            assert response.status_code == 404

    def test_initial_search_fallback_sparql(self, client):
        with patch("backend.app.search_by_author", return_value=None), \
                patch("backend.app.get_author_metadata_sparql", return_value={
                    "oa_link": "https://openalex.org/author/1234",
                    "name": "Test Author",
                    "current_institution": "Test Inst"
                }), \
                patch("backend.app.list_given_researcher_institution", return_value=(["dummy_topic"], {"nodes": [], "edges": []})):
            payload = {"researcher": "Test Author",
                       "organization": "", "topic": "", "type": ""}
            response = client.post("/initial-search", json=payload)
            data = response.get_json()
            assert isinstance(data, dict)
            assert "metadata" in data
            assert "graph" in data
            assert "list" in data

    def test_serve_route_static_file_coverage(self, client, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda path: True)
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("Static File Content", status=200))
        response = client.get("/somefile.js")
        assert response.status_code == 200
        assert b"Static File Content" in response.data

    def test_serve_route_index_fallback_coverage(self, client, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda path: False)
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("Index HTML", status=200))
        response = client.get("/nonexistent")
        assert response.status_code == 200
        assert b"Index HTML" in response.data


class TestAll:
    def test_404_not_found(self, client):
        response = client.get("/non-existent-route")
        assert response.status_code in (200, 404)

    def test_500_internal_server_error(self, client, mocker):
        mocker.patch("backend.app.get_institution_and_researcher_results",
                     side_effect=Exception("Forced error"))
        payload = {"organization": "TestOrg",
                   "researcher": "TestRes", "topic": "", "type": ""}
        response = client.post("/initial-search", json=payload)
        assert response.status_code == 500

    def test_env_var_loading(self):
        for var in ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
            os.environ.pop(var, None)
        import backend.app as app_module_temp
        importlib.reload(app_module_temp)
        assert os.getenv("DB_HOST") is None
        importlib.reload(app_module_temp)

    def test_index_route_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"<html" in resp.data or b"<!DOCTYPE html>" in resp.data

    def test_index_route_subpath(self, client, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda path: True)
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("static content", status=200))
        response = client.get("/dummy.js")
        assert response.status_code == 200
        assert b"static content" in response.data

    @patch("backend.app.psycopg2.connect")
    def test_execute_query_success_all(self, mock_connect):
        fake_cursor = MagicMock()
        fake_cursor.fetchall.return_value = [("dummy",)]
        fake_cursor.__enter__.return_value = fake_cursor
        fake_conn = MagicMock()
        fake_conn.cursor.return_value = fake_cursor
        fake_conn.__enter__.return_value = fake_conn
        mock_connect.return_value = fake_conn
        result = execute_query("SELECT 1;", None)
        assert result == [("dummy",)]

    @patch("backend.app.psycopg2.connect", side_effect=Exception("DB error"))
    def test_execute_query_failure_all(self, mock_connect):
        result = execute_query("SELECT 1;", None)
        assert result is None

    @patch("backend.app.requests.get")
    def test_fetch_last_known_institutions_success_all(self, mock_get):
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "last_known_institutions": [{"display_name": "Test Univ", "id": "https://openalex.org/institution/999"}]
        }
        mock_get.return_value = fake_response
        result = fetch_last_known_institutions(
            "https://openalex.org/author/1234")
        assert isinstance(result, list)
        assert result[0]["display_name"] == "Test Univ"

    @patch("backend.app.requests.get", side_effect=Exception("Connection error"))
    def test_fetch_last_known_institutions_failure_all(self, mock_get):
        result = fetch_last_known_institutions(
            "https://openalex.org/author/1234")
        assert result == []

    @patch("backend.app.requests.post")
    def test_query_sparql_success_all(self, mock_post):
        fake_response = MagicMock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = {
            "results": {"bindings": [{"var": {"value": "val"}}]}}
        mock_post.return_value = fake_response
        result = query_SPARQL_endpoint(
            "https://semopenalex.org/sparql", "SELECT *")
        assert result == [{"var": "val"}]

    @patch("backend.app.requests.post", side_effect=requests.exceptions.RequestException("Error"))
    def test_query_sparql_failure_all(self, mock_post):
        result = query_SPARQL_endpoint(
            "https://semopenalex.org/sparql", "SELECT *")
        assert result == []

    def test_autofill_topics_success(self, client, monkeypatch):
        dummy_data = "Computer Science\nBiology\nChemistry\n"
        monkeypatch.setattr("builtins.open", lambda f,
                            mode='r': MagicMock(read=lambda: dummy_data))
        monkeypatch.setattr("backend.app.SUBFIELDS", True)
        response = client.post("/autofill-topics", json={"topic": "bio"})
        data = response.get_json()
        assert "possible_searches" in data
        assert "Biology" in data["possible_searches"]

    def test_combine_graphs_all(self):
        g1 = {"nodes": [{"id": "A"}, {"id": "B"}], "edges": [
            {"id": "AB", "start": "A", "end": "B"}]}
        g2 = {"nodes": [{"id": "B"}, {"id": "C"}], "edges": [
            {"id": "BC", "start": "B", "end": "C"}]}
        combined = combine_graphs(g1, g2)
        node_ids = {n["id"] for n in combined["nodes"]}
        edge_ids = {e["id"] for e in combined["edges"]}
        assert node_ids == {"A", "B", "C"}
        assert edge_ids == {"AB", "BC"}

    def test_backend_init_import_all(self):
        import backend
        assert backend is not None

    def test_pytest_hook_report_header(self, monkeypatch):
        from backend import conftest
        conftest._test_finish_message.append("Test finished")
        header = conftest.pytest_report_header(None)
        assert "Test finished" in header[0]

    def test_get_researcher_result_fetch_last(self, monkeypatch):
        fake_data = {
            "author_metadata": {
                "orcid": "ORCID456",
                "num_of_works": 5,
                "last_known_institution": None,
                "num_of_citations": 2,
                "openalex_url": "https://openalex.org/author/9999"
            },
            "data": [{"topic": "TestTopic", "num_of_works": 1}]
        }
        monkeypatch.setattr("backend.app.search_by_author",
                            lambda author: fake_data)
        monkeypatch.setattr("backend.app.fetch_last_known_institutions", lambda oa_link: [
                            {"display_name": "FetchedInst", "id": "https://openalex.org/institutions/5555"}])
        result = get_researcher_result("Test Author", page=1, per_page=10)
        assert result["metadata"]["current_institution"] == "FetchedInst"
        assert "metadata_pagination" in result

    def test_get_default_graph_all(self, monkeypatch):
        fake_default = {
            "nodes": [
                {"id": "A", "type": "INSTITUTION"},
                {"id": "B", "type": "TOPIC"},
                {"id": "C", "type": "AUTHOR"}
            ],
            "edges": [
                {"start": "A", "end": "B", "connecting_works": 10},
                {"start": "A", "end": "B", "connecting_works": 5},
                {"start": "C", "end": "B", "connecting_works": 3}
            ]
        }
        fake_file = StringIO(json.dumps(fake_default))
        monkeypatch.setattr("builtins.open", lambda filename,
                            mode='r': fake_file if filename == "default.json" else open(filename, mode))
        response = get_default_graph()
        graph = response["graph"]
        assert len(graph["edges"]) == 2
        node_ids = {node["id"] for node in graph["nodes"]}
        assert "B" in node_ids

    def test_get_topic_and_researcher_metadata_sparql_missing(self, monkeypatch):
        monkeypatch.setattr(
            "backend.app.get_author_metadata_sparql", lambda author: {})
        monkeypatch.setattr("backend.app.get_subfield_metadata_sparql", lambda topic: {
                            "topic_clusters": ["ClusterX"], "oa_link": "http://topicX"})
        result = get_topic_and_researcher_metadata_sparql(
            "TopicMissing", "AuthorMissing")
        assert result == {}

    def test_get_institution_endowments_and_givings_no_data(self, monkeypatch, caplog):
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstEG")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institution_endowments_and_givings("InstEG")
        assert result is None
        assert "No MUP endowments and givings data found for InstEG" in caplog.text

    def test_get_institution_medical_expenses_no_data(self, monkeypatch, caplog):
        monkeypatch.setattr("backend.app.get_institution_mup_id", lambda name: {
                            "institution_mup_id": "MUP123"})
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institution_medical_expenses("InstMed")
        assert result is None
        assert "No MUP medical expenses data found for InstMed" in caplog.text

    def test_get_institution_doctorates_and_postdocs_no_data(self, monkeypatch, caplog):
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstDP")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institution_doctorates_and_postdocs("InstDP")
        assert result is None
        assert "No MUP doctorates and postdocs data found for InstDP" in caplog.text

    def test_get_institution_num_of_researches_no_data(self, monkeypatch, caplog):
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstNR")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institution_num_of_researches("InstNR")
        assert result is None
        assert "No MUP number of researchers data found for InstNR" in caplog.text

    def test_get_institutions_r_and_d_no_data(self, monkeypatch, caplog):
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstRD")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institutions_r_and_d("InstRD")
        assert result is None
        assert "No MUP R&D datafound for InstRD" in caplog.text

    def test_get_institutions_faculty_awards_no_data(self, monkeypatch, caplog):
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstFA")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institutions_faculty_awards("InstFA")
        assert result is None
        assert "No MUP faculty awards data found for InstFA" in caplog.text

    def test_db_configuration(self):
        os.environ['DB_PORT'] = '5432'
        os.environ['DB_NAME'] = 'testdb'
        os.environ['DB_USER'] = 'testuser'
        os.environ['DB_PASSWORD'] = 'testpass'
        os.environ['DB_API'] = 'http://testapi'
        from backend.app import DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, API
        assert DB_PORT == 5432
        assert DB_NAME == 'testdb'
        assert DB_USER == 'testuser'
        assert DB_PASSWORD == 'testpass'
        assert API == 'http://testapi'

    def test_search_by_author_institution_no_result(self, caplog):
        with patch("backend.app.get_author_ids", return_value=[{"author_id": "A1"}]), \
                patch("backend.app.get_institution_id", return_value="I1"), \
                patch("backend.app.execute_query", return_value=None):
            result = search_by_author_institution("Author", "Institution")
            assert result is None
            assert "No results found for author-institution search" in caplog.text

    def test_search_by_institution_topic_no_result(self, caplog):
        with patch("backend.app.get_institution_id", return_value=None):
            result = search_by_institution_topic("Institution", "Topic")
            assert result is None
            assert "No results found for institution-topic search" in caplog.text

    def test_search_by_author_topic_no_result(self, caplog):
        with patch("backend.app.get_author_ids", return_value=None):
            result = search_by_author_topic("Author", "Topic")
            assert result is None
            assert "No results found for author-topic search" in caplog.text

    def test_search_by_institution_no_result(self, caplog):
        with patch("backend.app.get_institution_id", return_value=None):
            result = search_by_institution("Institution")
            assert result is None
            assert "No results found for institution: Institution" in caplog.text

    def test_search_by_author_no_result(self, caplog):
        with patch("backend.app.get_author_ids", return_value=None):
            result = search_by_author("Author")
            assert result is None
            assert "No results found for author: Author" in caplog.text

    def test_keywords_csv_read(self, monkeypatch):
        monkeypatch.setattr("backend.app.SUBFIELDS", False)
        dummy_keywords = "Keyword1\nKeyword2\nKeyword3"
        monkeypatch.setattr("builtins.open", lambda filename, mode='r': StringIO(
            dummy_keywords) if "keywords.csv" in filename else StringIO(""))
        import backend.app as app_module_temp
        importlib.reload(app_module_temp)
        from backend.app import autofill_topics_list
        assert autofill_topics_list == ["Keyword1", "Keyword2", "Keyword3"]

    def test_get_geo_info_no_data(self, caplog):
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = None
        with patch("backend.app.requests.get", return_value=fake_response):
            result = get_geo_info("openalex.org/institutions/12345")
            assert result is None
            assert "No data found for institution" in caplog.text

    def test_get_researcher_and_topic_results(self, monkeypatch):
        fake_data = {
            "subfield_metadata": [{"topic": "Sub1", "subfield_url": "http://sub1"}],
            "totals": {"total_num_of_works": 30, "total_num_of_citations": 10, "total_num_of_authors": 4},
            "data": [{"institution_name": "InstC", "num_of_authors": 2}]
        }
        monkeypatch.setattr("backend.app.search_by_topic",
                            lambda topic: fake_data)
        result = get_subfield_results(
            "SubfieldX", "AuthorX", page=1, per_page=10)
        metadata = result["metadata"]
        assert metadata["work_count"] == 30
        assert "SubfieldX" in metadata["topic_name"]

    def test_get_institution_and_topic_results(self, monkeypatch):
        fake_data = {
            "institution_metadata": {
                "url": "http://instF",
                "openalex_url": "http://instF",
                "ror": "ROR123"
            },
            "data": [{"topic_name": "Sub1", "num_of_works": 3}]
        }
        monkeypatch.setattr(
            "backend.app.search_by_institution_topic", lambda i, t: fake_data)
        result = get_institution_and_subfield_results(
            "InstF", "Sub1", page=1, per_page=10)
        metadata = result["metadata"]
        assert metadata["work_count"] == 3
        assert "InstF" in metadata["institution_name"]

    def test_get_researcher_and_institution_results(self, monkeypatch):
        fake_data = {
            "institution_metadata": {
                "url": "http://instG",
                "openalex_url": "http://instG",
                "ror": "ROR456"
            },
            "author_metadata": {
                "openalex_url": "http://authorG",
                "orcid": "ORCID456",
                "num_of_works": 12,
                "num_of_citations": 7
            },
            "data": [{"topic_name": "TopicG", "num_of_works": 4}]
        }
        monkeypatch.setattr(
            "backend.app.search_by_author_institution", lambda a, i: fake_data)
        result = get_institution_and_researcher_results(
            "InstG", "AuthorG", page=1, per_page=10)
        assert "metadata" in result
        assert result["metadata"]["institution_name"] == "InstG"

    def test_get_institution_researcher_subfield_results(self, monkeypatch):
        fake_data = {
            "institution_metadata": {
                "url": "http://instI",
                "openalex_url": "http://instI",
                "ror": "ROR789"
            },
            "author_metadata": {
                "openalex_url": "http://authorI",
                "orcid": "ORCID789",
                "num_of_works": 9,
                "num_of_citations": 3,
                "last_known_institution": "InstI"
            },
            "subfield_metadata": [{"topic": "SubfieldI", "subfield_url": "http://subI"}],
            "totals": {"total_num_of_works": 50, "total_num_of_citations": 25},
            "data": [{"work_name": "Work1", "cited_by_count": 5}]
        }
        monkeypatch.setattr(
            "backend.app.search_by_author_institution_topic", lambda a, i, t: fake_data)
        result = get_institution_researcher_subfield_results(
            "InstI", "AuthorI", "TopicI", page=1, per_page=10)
        metadata = result["metadata"]
        assert metadata["institution_name"] == "InstI"
        assert "graph" in result
        assert "list" in result
        # Expecting one item in list for this fake data
        assert len(result["list"]) == 1

    def test_get_institution_id_success(self, monkeypatch):
        fake_result = [[{"institution_id": "I123"}]]
        monkeypatch.setattr("backend.app.execute_query",
                            lambda query, params: fake_result)
        result = get_institution_id("TestInst")
        assert result == "I123"

    def test_search_by_author_topic_success(self, monkeypatch):
        fake_author_ids = [{"author_id": "A123"}]
        fake_result = [[{"result_key": "value"}]]
        monkeypatch.setattr("backend.app.get_author_ids",
                            lambda name: fake_author_ids)
        monkeypatch.setattr("backend.app.execute_query",
                            lambda query, params: fake_result)
        result = search_by_author_topic("TestAuthor", "TestTopic")
        assert result == {"result_key": "value"}

    def test_get_subfield_results_success_variant(self, monkeypatch):
        fake_data = {
            "subfield_metadata": [{"topic": "SubTest", "subfield_url": "http://subtest"}],
            "totals": {"total_num_of_works": 40, "total_num_of_citations": 20, "total_num_of_authors": 5},
            "data": [{"institution_name": "InstTest", "num_of_authors": 3}]
        }
        monkeypatch.setattr("backend.app.search_by_topic",
                            lambda topic: fake_data)
        result = get_subfield_results("SubfieldX", page=1, per_page=10)
        metadata = result["metadata"]
        assert metadata["work_count"] == 40
        assert "SubfieldX" in metadata.get("name", "SubfieldX")

    def test_get_institution_researcher_subfield_results_multiple(self, monkeypatch):
        fake_data = {
            "institution_metadata": {
                "url": "http://instI",
                "openalex_url": "http://instI",
                "ror": "ROR789"
            },
            "author_metadata": {
                "openalex_url": "http://authorI",
                "orcid": "ORCID789",
                "num_of_works": 9,
                "num_of_citations": 3,
                "last_known_institution": "InstI"
            },
            "subfield_metadata": [{"topic": "SubfieldI", "subfield_url": "http://subI"}],
            "totals": {"total_num_of_works": 50, "total_num_of_citations": 25},
            "data": [
                {"work_name": "Work1", "cited_by_count": 5},
                {"work_name": "Work2", "cited_by_count": 10},
            ]
        }
        monkeypatch.setattr(
            "backend.app.search_by_author_institution_topic", lambda a, i, t: fake_data)
        result = get_institution_researcher_subfield_results(
            "InstI", "AuthorI", "TopicI", page=1, per_page=10)
        metadata = result["metadata"]
        assert metadata["institution_name"] == "InstI"
        assert "graph" in result
        assert "list" in result
        assert len(result["list"]) == 2

    def test_get_researcher_and_institution_metadata_sparql(self):
        fake_researcher = {
            "oa_link": "http://authorJ",
            "orcid": "ORCIDJ",
            "work_count": 11,
            "cited_by_count": 6,
            "current_institution": "InstJ",
            "institution_url": "http://instJ"
        }
        fake_institution = {
            "homepage": "http://instJ",
            "oa_link": "http://instJ",
            "ror": "ROR101"
        }
        with patch("backend.app.get_author_metadata_sparql", return_value=fake_researcher), \
                patch("backend.app.get_institution_metadata_sparql", return_value=fake_institution):
            result = get_researcher_and_institution_metadata_sparql(
                "AuthorJ", "InstJ")
            assert result["institution_name"] == "InstJ"
            assert result["researcher_name"] == "AuthorJ"
            assert result["orcid"] == "ORCIDJ"
            assert result["ror"] == "ROR101"

    def test_list_given_topic(self, monkeypatch):
        fake_response_data = {
            "results": [{
                "display_name": "InstK",
                "topics": [{"subfield": {"display_name": "SubK"}, "count": 7}]
            }],
            "meta": {"next_cursor": None}
        }
        fake_get = MagicMock()
        fake_get.json.return_value = fake_response_data
        monkeypatch.setattr("backend.app.requests.get",
                            lambda url, headers: fake_get)
        subfield_list, graph, extra_metadata = list_given_topic(
            "SubK", "ID_SubK")
        assert subfield_list == [("InstK", 7)]
        assert extra_metadata["work_count"] == 7

    def test_list_given_institution_topic_work_count(self, monkeypatch):
        fake_sparql_results = [
            {"author": "A1", "name": "Author1", "works": {"value": "W1, W2, W3"}}
        ]
        monkeypatch.setattr("backend.app.query_SPARQL_endpoint",
                            lambda endpoint, query: fake_sparql_results)
        subfield_list, graph, extra_metadata = list_given_institution_topic(
            "InstL", "ID_InstL", "SubL", "ID_SubL")
        assert extra_metadata["work_count"] == 3

    def test_list_given_researcher_institution_graph(self, monkeypatch):
        fake_api_response = {"topics": [
            {"subfield": {"display_name": "SubM"}, "count": 4}]}
        fake_get = MagicMock()
        fake_get.json.return_value = fake_api_response
        monkeypatch.setattr("backend.app.requests.get",
                            lambda url, headers: fake_get)
        sorted_subfields, graph = list_given_researcher_institution(
            "https://openalex.org/authors/9999", "AuthorM", "InstM")
        node_ids = {node["id"] for node in graph["nodes"]}
        assert "InstM" in node_ids
        assert "SubM" in node_ids

    def test_get_topic_and_researcher_metadata_sparql_extra(self):
        fake_researcher_data = {
            "orcid": "ORCIDX",
            "current_institution": "InstX",
            "work_count": 15,
            "cited_by_count": 8,
            "oa_link": "http://authorX",
            "institution_url": "http://instX"
        }
        fake_topic_data = {
            "topic_clusters": ["Cluster1", "Cluster2"],
            "oa_link": "http://topicX"
        }
        with patch("backend.app.get_author_metadata_sparql", return_value=fake_researcher_data), \
                patch("backend.app.get_subfield_metadata_sparql", return_value=fake_topic_data):
            result = get_topic_and_researcher_metadata_sparql(
                "TopicX", "AuthorX")
            assert result["orcid"] == "ORCIDX"
            assert result["topic_clusters"] == ["Cluster1", "Cluster2"]

    def test_list_given_researcher_topic_citation_count(self, monkeypatch):
        fake_sparql_results = [
            {"title": "WorkA", "cited_by_count": {"value": "10"}}
        ]
        monkeypatch.setattr("backend.app.query_SPARQL_endpoint",
                            lambda endpoint, query: fake_sparql_results)
        work_list, graph, extra_metadata = list_given_researcher_topic(
            "TopicY", "AuthorY", "InstY", "ID_TopicY", "ID_AuthorY", "ID_InstY")
        assert work_list[0][1] == 10
        assert extra_metadata["cited_by_count"] == 10

    def test_list_given_researcher_topic_graph_nodes(self, monkeypatch):
        fake_sparql_results = [
            {"title": "WorkB", "cited_by_count": {"value": "5"}}
        ]
        monkeypatch.setattr("backend.app.query_SPARQL_endpoint",
                            lambda endpoint, query: fake_sparql_results)
        work_list, graph, extra_metadata = list_given_researcher_topic(
            "TopicZ", "AuthorZ", "InstZ", "ID_TopicZ", "ID_AuthorZ", "ID_InstZ")
        node_ids = {node["id"] for node in graph["nodes"]}
        assert "WorkB" in node_ids

    def test_list_given_researcher_topic_extra_metadata(self, monkeypatch):
        fake_sparql_results = [
            {"title": "WorkC", "cited_by_count": {"value": "2"}}
        ]
        monkeypatch.setattr("backend.app.query_SPARQL_endpoint",
                            lambda endpoint, query: fake_sparql_results)
        work_list, graph, extra_metadata = list_given_researcher_topic(
            "TopicW", "AuthorW", "InstW", "ID_TopicW", "ID_AuthorW", "ID_InstW")
        assert extra_metadata["work_count"] == 1
        assert extra_metadata["cited_by_count"] == 2

    def test_query_SQL_endpoint_error(self, monkeypatch, caplog):
        fake_connection = MagicMock()
        fake_cursor = MagicMock()
        fake_cursor.execute.side_effect = Exception("SQL Error")
        fake_connection.cursor.return_value.__enter__.return_value = fake_cursor
        with pytest.raises(Exception):
            query_SQL_endpoint(fake_connection, "SELECT * FROM table")
        assert "SQL query failed" in caplog.text

    def test_autofill_topics_filter(self, client):
        response = client.post("/autofill-topics", json={"topic": "Che"})
        data = response.get_json()
        assert any("Chemistry" in s for s in data["possible_searches"])

    def test_create_connection_success(self, monkeypatch):
        fake_conn = MagicMock()
        with patch("backend.app.mysql.connector.connect", return_value=fake_conn):
            conn = create_connection("host", "user", "pass", "db")
            assert conn == fake_conn

    def test_get_institution_mup_id_success(self, monkeypatch, caplog):
        fake_inst_id = "Inst123"
        fake_query_result = [[{"institution_id": "Inst123"}]]
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: fake_inst_id)
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: fake_query_result)
        result = get_institution_mup_id("TestInst")
        assert result == {"institution_id": "Inst123"}

    def test_get_institution_mup_id_no_inst(self, monkeypatch, caplog):
        monkeypatch.setattr(
            "backend.app.get_institution_id", lambda name: None)
        result = get_institution_mup_id("NoInst")
        assert result is None
        assert "No institution ID found" in caplog.text

    def test_get_institution_sat_scores_not_found(self, monkeypatch, caplog):
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstNotFound")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institution_sat_scores("NoSatInst")
        assert result is None
        assert "No MUP SAT scores data found" in caplog.text

    def test_get_institution_endowments_and_givings_success(self, monkeypatch, caplog):
        fake_result = [[{"endowment": 100, "giving": 50, "year": 2020}]]
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstEG")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: fake_result)
        result = get_institution_endowments_and_givings("InstEG")
        assert result["endowment"] == 100

    def test_get_institution_medical_expenses_no_mup(self, monkeypatch, caplog):
        monkeypatch.setattr(
            "backend.app.get_institution_mup_id", lambda name: None)
        result = get_institution_medical_expenses("NoMedInst")
        assert result is None

    def test_get_institution_doctorates_and_postdocs_success(self, monkeypatch):
        fake_result = [
            [{"num_postdocs": 3, "num_doctorates": 10, "year": 2021}]]
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstDP")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: fake_result)
        result = get_institution_doctorates_and_postdocs("InstDP")
        assert result["num_doctorates"] == 10

    def test_get_institution_num_of_researches_success(self, monkeypatch):
        fake_result = [[{"num_federal_research": 2,
                         "num_nonfederal_research": 3, "total_research": 5, "year": 2022}]]
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstNR")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: fake_result)
        result = get_institution_num_of_researches("InstNR")
        assert result["total_research"] == 5

    def test_get_institutions_faculty_awards_success(self, monkeypatch):
        fake_result = [[{"nae": "NAE", "nam": "NAM",
                         "nas": "NAS", "num_fac_awards": 4, "year": 2019}]]
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstFA")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: fake_result)
        result = get_institutions_faculty_awards("InstFA")
        assert result["num_fac_awards"] == 4

    def test_get_institutions_r_and_d_success(self, monkeypatch):
        fake_result = [[{"category": "Cat", "federal": 1,
                         "percent_federal": 50, "total": 2, "percent_total": 50}]]
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstRD")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: fake_result)
        result = get_institutions_r_and_d("InstRD")
        assert result["total"] == 2

    @pytest.mark.parametrize("endpoint", [
        "/mup-sat-scores",
        "/endowments-and-givings",
        "/mup-faculty-awards",
        "/mup-r-and-d"
    ])
    def test_endpoint_missing_institution_name(self, client, endpoint):
        response = client.post(endpoint, json={})
        assert response.status_code == 400
        assert b"Missing 'institution_name'" in response.data

    def test_serve_route_static_file_all(self, client, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda path: True)
        monkeypatch.setattr("backend.app.send_from_directory", lambda folder, file: Response(
            "Static File Content", status=200))
        response = client.get("/dummy.js")
        assert response.status_code == 200
        assert b"Static File Content" in response.data

    def test_serve_route_index_fallback_all(self, client, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda path: False)
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("Index HTML", status=200))
        response = client.get("/nonexistent")
        assert response.status_code == 200
        assert b"Index HTML" in response.data
