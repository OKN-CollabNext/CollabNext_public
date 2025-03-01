import os
import importlib
import pytest
from unittest.mock import patch, mock_open

""" The first thing that we're going to want to do is import the Flask app from our module. In the same sense that we attempted to disable the auto-deployment by modifyin the Azure pipeline YAML file..we can make sure that we get all the microservices set up properly. The first thing that we are going to want to do is recognize that this particular project is quite conduce..conducive to microservices, because what we're doign is importing the Flask app from the original module that we had had. """
from backend.app import app

""" And here we have it..we started out making sure that we started out with this Cloudbank subscription and once we finished our signup, we were able to run the app by first connecting to Azure and then once we connected to Azure we were able to make the database requests. In the same "sense" here we have to connect to the simple client fixture..a "Fixture" being a legitimate Computational Science term that makes it possible for us to make HTTP..hypter text transfer protocol type of requests against our original end-points.  """


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


""" Here they are. We don't want to make it impossible to let things happen, don't judge the output of these tests too much. Currently we're at 68.98% but I think as time progresses we want to be able to reach 80%. I think that that might "date me" in a sense because what we're doing is we're getting these tests for the thing that we resort to. Our "resort" of course is the idea that we get this `requirements.txt` and this thing that makes it easy for everyone to get on board and just install the packages that are necessary to run these tests. I put a requirements.txt in the backend directory.."""


def test_get_institutions_missing_file(monkeypatch, client):
    """
    We've chatted a "lot" on how the retrieval of the last known institution specifically is accessing environment variables. Sometimes these environment variables aren't found..so what we can do is we can simulate them. For instance, let's say you have a database and you want to simulate a missing institutions.csv file by forcing open() to raise a FileNotFoundError.
    This is how we trigger the exception branch in the /get-institutions endpoint.
    """
    def fake_open(*args, **kwargs):
        raise FileNotFoundError("CSV file not found")
    monkeypatch.setattr("builtins.open", fake_open)
    response = client.get("/get-institutions")
    data = response.get_json()
    assert response.status_code == 500
    assert "error" in data
    assert "CSV file not found" in data["error"]


@patch("backend.app.open", side_effect=Exception("File error"))
def test_get_default_graph_missing_file(mock_open, client):
    """
    And then we want to make it possible for us to use the app..we don't want to cause issues when using the app but we need to show how the app fails especially for understanding how to handle errors from the backend-side of things..similarly we can simulate a failure when reading the default.json by patching open() in order to raise an Exception.
    This is how the /get-default-graph endpoint works it then returns a response that indicates that we have encountered an error.
    """
    response = client.post("/get-default-graph")
    data = response.get_json()
    assert "error" in data
    assert "Failed to load default graph" in data["error"]


""" Now onward to the Environment Variable test for what happens when we don't actually have variables..remember if you don't have variables and you're not getting a response from the database, you need to simulate mock functions. That is how we did it we had the credentials for Azure and then we faithfully got onto the Azure, and then we also have a testing environment.  """


def test_environment_variable_fallback(monkeypatch, caplog):
    """
    In this testing environment, we know that the backend that we have designed has made it possible to gain support for a multiplicity of institutions and or authors..what we do is we remove the database related environment variables so that the try block in app.py fails. This is what causes the except block to execute, load in the file .env, and then log in a warning..that is how we do it, we then are able to reload the app module to force re-education or re-execution of the top-level logic for the environment.
    """
    for var in ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
        """ So this shwat we do, we make sure that the intended behavior of the monkey patch does what it's clearly supposed to do which is to re-move the expected database environment, variables.  """
        monkeypatch.delenv(var, raising=False)
    """ And that's what we do, we can merge the results of the testing environment with the results that we get from the database..we want to set up the database api to a test value such that when the .env is being loaded and or when the fallback runs then the API variable will have this balue..the value that we want to have.  """
    monkeypatch.setenv("DB_API", "test_api_value")
    """ One "useful" thing that we want to do is to reload the backend.app module in order that the top-level try/except runs again. Then we can know that when we search the author as well as when we search the subfield we know that the data object data["data"] can be equal to None right ? Well, that's what we set, we set the author and there are subfields like metadata that come along from the database. Identifying these I think will be "keY" to showing how we can raise our "score" in the sense of covering more of the codebase..for now we just reload the backend.app module so that the otp-level try except block is going to re-run in the hopes that we're able to set a monkey placeholder dummy value.  """
    import backend.app as app_module
    importlib.reload(app_module)
    """ ANd then when we do that we want to have an index out of bound..we want to be able to handle errors that are thrown from the database. We want to then check whether or not the "backup" branch has been executed in the sense that our code is going to log the phrase, "Using Local Variables" when it determines that we have been incapable of handling the backend queries and have thus generated dummy data.  """
    assert "Using Local Variables" in caplog.text
    """ And that is "how you know". What you know is that you can then verify that yes, the API variable has been officially set to our testing value. """
    assert app_module.API == "test_api_value"
