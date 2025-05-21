import "../styles/Search.css";

import { useEffect, useRef, useState } from "react";
import { Circles } from "react-loader-spinner";
import { useNavigate } from "react-router-dom";
import MapMetadata from "../components/MapMetadata";
import {
  Box,
  Button,
  Checkbox,
  Flex,
  Input,
  list,
  Text,
} from "@chakra-ui/react";

import AllThreeMetadata from "../components/AllThreeMetadata";
// import CytoscapeComponent from 'react-cytoscapejs';
import GraphComponent from "../components/GraphComponent";
import InstitutionMetadata from "../components/InstitutionMetadata";
import MultiInstitutionMetadata from "../components/MultiInstitutionMetadata";
import InstitutionResearcherMetaData from "../components/InstitutionResearcherMetaData";
import ResearcherMetadata from "../components/ResearcherMetadata";
import Suggested from "../components/Suggested";
import TopicInstitutionMetadata from "../components/TopicInstitutionMetadata";
import TopicMetadata from "../components/TopicMetadata";
import TopicResearcherMetadata from "../components/TopicResearcherMetadata";
import { baseUrl, handleAutofill, initialValue } from "../utils/constants";
import { ResearchDataInterface, SearchType } from "../utils/interfaces";

const Search = () => {
  const searchParams = new URLSearchParams(window.location.search);
  // const cyRef = React.useRef<cytoscape.Core | undefined>();
  const institution = searchParams.get("institution");
  const type = searchParams.get("type");
  const topic = searchParams.get("topic");
  const researcher = searchParams.get("researcher");
  const [isNetworkMap, setIsNetworkMap] = useState("list");
  const [universityName, setUniversityName] = useState(institution || "");
  const [universityName2, setUniversityName2] = useState("");
  const [topicType, setTopicType] = useState(topic || "");
  const [institutionType, setInstitutionType] = useState(type || "");
  const [researcherType, setResearcherType] = useState(researcher || "");
  const [researcherType2, setResearcherType2] = useState("");
  const [data, setData] = useState<ResearchDataInterface>(initialValue);
  const [isLoading, setIsLoading] = useState(false);
  const [isAddOrgChecked, setIsAddOrgChecked] = useState(false);
  const [orgList, setOrgList] = useState<File | null>(null);
  const [isAddPersonChecked, setIsAddPersonChecked] = useState(false);
  const [personList, setPersonList] = useState<File | null>(null);
  const [suggestedInstitutions, setSuggestedInstitutions] = useState([]);
  const [suggestedTopics, setSuggestedTopics] = useState([]);

  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(25);
  const [totalPages, setTotalPages] = useState(1);

  const navigate = useNavigate();
  // const toast = useToast();

  // let latestRequestId = 0;
  const handleToggle = (value: string) => {
    setIsNetworkMap(value);
  };
  const institutionTypes = [
    "HBCU",
    "AANAPISI",
    "ANNH",
    "Carnegie R1",
    "Carnegie R2",
    "Emerging",
    "HSI",
    "MSI",
    "NASNTI",
    "PBI",
    "TCU",
  ];

  const sendSearchRequest = (
    search: SearchType,
    {
      universityName,
      institutionType,
      topicType,
      researcherType,
      page,
      per_page,
      extra_institutions,
    }: {
      universityName: string;
      institutionType: string;
      topicType: string;
      researcherType: string;
      page: number;
      per_page: number;
      extra_institutions: string[] | string;
    }
  ) => {
    fetch(`${baseUrl}/initial-search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        organization: universityName,
        type: institutionType,
        topic: topicType,
        researcher: researcherType,
        page: page,
        per_page: per_page,
        extra_institutions: extra_institutions,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        console.log(data);
        setTotalPages(data.metadata_pagination?.total_pages || 1);
        setCurrentPage(data.metadata_pagination?.current_page || 1);
        const dataObj =
          search === "institution"
            ? {
                institution_name: data?.metadata?.name,
                is_hbcu: data?.metadata?.hbcu,
                cited_count: data?.metadata?.cited_count,
                author_count: data?.metadata?.author_count,
                works_count: data?.metadata?.works_count,
                institution_url: data?.metadata?.homepage,
                open_alex_link: data?.metadata?.oa_link,
                ror_link: data?.metadata?.ror,
                graph: data?.graph,
                topics: data?.list,
                search,
                has_multiple_institutions: extra_institutions.length > 0,
                all_institution_metadata: data?.extra_metadata,
              }
            : search === "topic"
            ? {
                topic_name: data?.metadata?.name,
                topic_clusters: data?.metadata?.topic_clusters,
                graph: data?.graph,
                cited_count: data?.metadata?.cited_by_count,
                author_count: data?.metadata?.researchers,
                works_count: data?.metadata?.work_count,
                open_alex_link: data?.metadata?.oa_link,
                organizations: data?.list,
                coordinates: data?.coordinates,
                search,
              }
            : search === "researcher"
            ? {
                institution_name: data?.metadata?.current_institution,
                researcher_name: data?.metadata?.name,
                orcid_link: data?.metadata?.orcid,
                cited_count: data?.metadata?.cited_by_count,
                works_count: data?.metadata?.work_count,
                graph: data?.graph,
                open_alex_link: data?.metadata?.oa_link,
                topics: data?.list,
                institution_url: data?.metadata?.institution_url,
                search,
              }
            : search === "researcher-institution"
            ? {
                graph: data?.graph,
                topics: data?.list,
                institution_url: data?.metadata?.homepage,
                institution_name: data?.metadata?.institution_name,
                researcher_name: data?.metadata?.researcher_name,
                orcid_link: data?.metadata?.orcid,
                works_count: data?.metadata?.work_count,
                cited_count: data?.metadata?.cited_by_count,
                ror_link: data?.metadata?.ror,
                open_alex_link: data?.metadata?.institution_oa_link,
                researcher_open_alex_link: data?.metadata?.researcher_oa_link,
                search,
              }
            : search === "topic-researcher"
            ? {
                graph: data?.graph,
                works: data?.list,
                institution_name: data?.metadata?.current_institution,
                topic_name: data?.metadata?.topic_name,
                researcher_name: data?.metadata?.researcher_name,
                orcid_link: data?.metadata?.orcid,
                works_count: data?.metadata?.work_count,
                cited_count: data?.metadata?.cited_by_count,
                open_alex_link: data?.metadata?.topic_oa_link,
                researcher_open_alex_link: data?.metadata?.researcher_oa_link,
                topic_clusters: data?.metadata?.topic_clusters,
                search,
              }
            : search === "topic-institution"
            ? {
                graph: data?.graph,
                institution_name: data?.metadata?.institution_name,
                topic_name: data?.metadata?.topic_name,
                institution_url: data?.metadata?.homepage,
                cited_count: data?.metadata?.cited_by_count,
                works_count: data?.metadata?.work_count,
                author_count: data?.metadata?.people_count,
                open_alex_link: data?.metadata?.institution_oa_link,
                topic_open_alex_link: data?.metadata?.topic_oa_link,
                ror_link: data?.metadata?.ror,
                topic_clusters: data?.metadata?.topic_clusters,
                authors: data?.list,
                search,
              }
            : {
                graph: data?.graph,
                works: data?.list,
                institution_url: data?.metadata?.homepage,
                institution_name: data?.metadata?.institution_name,
                researcher_name: data?.metadata?.researcher_name,
                topic_name: data?.metadata?.topic_name,
                orcid_link: data?.metadata?.orcid,
                works_count: data?.metadata?.work_count,
                cited_count: data?.metadata?.cited_by_count,
                ror_link: data?.metadata?.ror,
                open_alex_link: data?.metadata?.institution_oa_link,
                topic_open_alex_link: data?.metadata?.topic_oa_link,
                researcher_open_alex_link: data?.metadata?.researcher_oa_link,
                topic_clusters: data?.metadata?.topic_clusters,
                search,
              };
        setData({
          ...initialValue,
          ...dataObj,
        });
        setIsLoading(false);
      })
      .catch((error) => {
        setData(initialValue);
        setIsLoading(false);
        console.log(error);
      });
  };

  const handlePageChange = (newPage: number) => {
    if (newPage > 0 && newPage <= totalPages) {
      setCurrentPage(newPage);
      handleSearch(
        universityName,
        institutionType,
        topicType,
        researcherType,
        newPage
      );
    }
  };

  const handleSearch = (
    newUniversityName: string,
    newInstitutionType: string,
    newTopicType: string,
    newResearcherType: string,
    page: number = 1
  ) => {
    setIsLoading(true);
    const extraInstitutions = isAddOrgChecked && universityName2.trim() ? [universityName2.trim()] : [];
    const params = new URLSearchParams(window.location.search);
    const universityName = params.get("institution") || "";
    const institutionType = params.get("type") || "";
    const topicType = params.get("topic") || "";
    const researcherType = params.get("researcher") || "";
    if (
      universityName !== newUniversityName ||
      institutionType !== newInstitutionType ||
      topicType !== newTopicType ||
      researcherType !== newResearcherType
    ) {
      if (newUniversityName) params.set("institution", newUniversityName);
      if (newInstitutionType) params.set("type", newInstitutionType);
      if (newTopicType) params.set("topic", newTopicType);
      if (newResearcherType) params.set("researcher", newResearcherType);
      navigate(`?${params.toString()}`, { replace: false });
    }
    // Determine search type and call sendSearchRequest using the passed values.
    if (newTopicType && newUniversityName && newResearcherType) {
      sendSearchRequest("all-three-search", {
        universityName: newUniversityName,
        institutionType: newInstitutionType,
        topicType: newTopicType,
        researcherType: newResearcherType,
        page: page,
        per_page: itemsPerPage,
        extra_institutions: extraInstitutions,
      });
    } else if (
      (newTopicType && newResearcherType) ||
      (newResearcherType && newUniversityName) ||
      (newTopicType && newUniversityName)
    ) {
      const search =
        newTopicType && newResearcherType
          ? "topic-researcher"
          : newResearcherType && newUniversityName
          ? "researcher-institution"
          : "topic-institution";
      sendSearchRequest(search, {
        universityName: newUniversityName,
        institutionType: newInstitutionType,
        topicType: newTopicType,
        researcherType: newResearcherType,
        page: page,
        per_page: itemsPerPage,
        extra_institutions: extraInstitutions,
      });
    } else if (newTopicType || newUniversityName || newResearcherType) {
      const search = newTopicType
        ? "topic"
        : newUniversityName
        ? "institution"
        : "researcher";
      sendSearchRequest(search, {
        universityName: newUniversityName,
        institutionType: newInstitutionType,
        topicType: newTopicType,
        researcherType: newResearcherType,
        page: page,
        per_page: itemsPerPage,
        extra_institutions: extraInstitutions,
      });
    } else if (orgList) {
      const search = "institution";
      const reader = new FileReader();
      reader.onload = async (event) => {
        const text = event.target?.result as string;
        sendSearchRequest(search, {
          universityName: newUniversityName,
          institutionType: newInstitutionType,
          topicType: newTopicType,
          researcherType: newResearcherType,
          page: page,
          per_page: itemsPerPage,
          extra_institutions: text,
        });
      };
      reader.readAsText(orgList);
    } else {
      // Default graph request
      fetch(`${baseUrl}/get-default-graph`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: null,
      })
        .then((res) => res.json())
        .then((data) => {
          setData({ ...initialValue, graph: data?.graph });
          setIsNetworkMap("graph");
          setIsLoading(false);
        })
        .catch((error) => {
          setIsLoading(false);
          setData(initialValue);
          console.log(error);
        });
    }
  };

  const orgInputRef = useRef<HTMLInputElement>(null);
  const personInputRef = useRef<HTMLInputElement>(null);

  const handleListClick = (ref: React.RefObject<HTMLInputElement>) => {
    ref?.current?.click();
  };

  const handleListChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    setList: React.Dispatch<React.SetStateAction<File | null>>
  ) => {
    if (e.target.files) {
      const file = e.target.files[0];
      console.log(file);
      if (file && file.name.endsWith(".csv")) {
        setList(file);
      } else if (file) {
        alert("Please select a valid CSV file.");
      }
    }
  };

  useEffect(() => {
    const handlePopState = () => {
      const params = new URLSearchParams(window.location.search);
      const newUniversityName = params.get("institution") || "";
      const newInstitutionType = params.get("type") || "";
      const newTopicType = params.get("topic") || "";
      const newResearcherType = params.get("researcher") || "";

      // Update states if needed (for UI inputs)
      setUniversityName(newUniversityName);
      setInstitutionType(newInstitutionType);
      setTopicType(newTopicType);
      setResearcherType(newResearcherType);

      // Immediately use the extracted values for a search.
      handleSearch(
        newUniversityName,
        newInstitutionType,
        newTopicType,
        newResearcherType
      );
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    handleSearch(universityName, institutionType, topicType, researcherType);
  }, []);

  return (
    <Box>
      <Flex justifyContent={"flex-end"} px="2rem">
        {["List", "Graph", "Map"].map((value) => (
          <Button
            onClick={() => setIsNetworkMap(value.toLowerCase())}
            bg="linear-gradient(#053257, #7e7e7e)"
            color="white"
            mr="1rem"
          >
            {value}
          </Button>
        ))}
      </Flex>
      <div className="main-content">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch(
              universityName,
              institutionType,
              topicType,
              researcherType,
              1
            );
          }}
          className="sidebar"
        >
          <input
            type="text"
            value={universityName}
            list="institutions"
            onChange={(e) => {
              setUniversityName(e.target.value);
              handleAutofill(
                e.target.value,
                false,
                setSuggestedTopics,
                setSuggestedInstitutions
              );
            }}
            placeholder={"University Name"}
            className="textbox"
            // disabled={isLoading}
          />
          <Suggested suggested={suggestedInstitutions} institutions={true} />
          {isAddOrgChecked && (
            <>
              <input
                type="text"
                value={universityName2}
                list="institutions"
                onChange={(e) => {
                  setUniversityName2(e.target.value);
                  handleAutofill(
                    e.target.value,
                    false,
                    setSuggestedTopics,
                    setSuggestedInstitutions
                  );
                }}
                placeholder={"Another University"}
                className="textbox"
                // disabled={isLoading}
              />
              <Suggested
                suggested={suggestedInstitutions}
                institutions={true}
              />
            </>
          )}
          <input
            type="text"
            value={topicType}
            onChange={(e) => {
              setTopicType(e.target.value);
              handleAutofill(
                e.target.value,
                true,
                setSuggestedTopics,
                setSuggestedInstitutions
              );
            }}
            list="topics"
            placeholder="Type Topic"
            className="textbox"
            // disabled={isLoading}
          />
          <Suggested suggested={suggestedTopics} institutions={false} />
          <select
            value={institutionType}
            onChange={(e) => setInstitutionType(e.target.value)}
            className="dropdown"
          >
            <option style={{ color: "black" }} value="">
              Select an institution type
            </option>
            {institutionTypes.map((type) => (
              <option style={{ color: "black" }} key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          {/* <FormControl isInvalid={topicType && !researcherType ? true : false}> */}
          <input
            type="text"
            value={researcherType}
            onChange={(e) => setResearcherType(e.target.value)}
            placeholder="Type Researcher"
            className="textbox"
            // disabled={isLoading}
          />
          {isAddPersonChecked && (
            <input
              type="text"
              value={researcherType2}
              onChange={(e) => setResearcherType2(e.target.value)}
              placeholder="Another Researcher"
              className="textbox"
              // disabled={isLoading}
            />
          )}
          {/* <FormErrorMessage>
            Researcher must be provided when Topic is
          </FormErrorMessage>
        </FormControl> */}
          <Box mt=".6rem">
            <Flex justifyContent={"space-between"}>
              {[
                {
                  checkedState: isAddOrgChecked,
                  setCheckedState: setIsAddOrgChecked,
                  text: "Add Another Org",
                },
                {
                  checkedState: isAddPersonChecked,
                  setCheckedState: setIsAddPersonChecked,
                  text: "Add Another Person",
                },
              ].map(({ checkedState, setCheckedState, text }) => (
                <Flex>
                  <Checkbox
                    mr=".2rem"
                    checked={checkedState}
                    onChange={(e) => setCheckedState(e.target.checked)}
                  />
                  <Text fontSize="11px" color={"white"}>
                    {text}
                  </Text>
                </Flex>
              ))}
            </Flex>
            <Box mt=".6rem">
              {[
                {
                  list: orgList,
                  setList: setOrgList,
                  text: "Upload Org List",
                  ref: orgInputRef,
                },
                {
                  list: personList,
                  setList: setPersonList,
                  text: "Upload Person List",
                  ref: personInputRef,
                },
              ].map(({ list, setList, text, ref }) => (
                <Flex alignItems="center">
                  <Button
                    border="1px solid white"
                    bg="transparent"
                    color="white"
                    fontWeight={400}
                    fontSize={"13px"}
                    onClick={() => handleListClick(ref)}
                    mt=".3rem"
                    mr=".35rem"
                  >
                    {list?.name?.slice(0, 14) || text}
                  </Button>
                  <input
                    onChange={(e) => handleListChange(e, setList)}
                    type="file"
                    ref={ref}
                    accept=".csv"
                    hidden
                  />
                  {list && (
                    <Text
                      fontSize="11px"
                      color={"white"}
                      cursor="pointer"
                      onClick={() => {
                        setList(null);
                        // @ts-ignore
                        ref.current.value = "";
                      }}
                    >
                      remove
                    </Text>
                  )}
                </Flex>
              ))}
            </Box>
            <Button
              width="100%"
              marginTop="10px"
              backgroundColor="transparent"
              color="white"
              border="2px solid white"
              isLoading={isLoading}
              type="submit"
            >
              Search
            </Button>
          </Box>
          {/* <button className='button' onClick={handleToggle}>
            {isNetworkMap ? 'See List Map' : 'See Network Map'}
          </button> */}
        </form>

        <div className="content">
          {isLoading ? (
            <Box
              w={{ lg: "500px" }}
              justifyContent={"center"}
              height={{ base: "190px", lg: "340px" }}
              display={"flex"}
              alignItems="center"
            >
              <Circles
                height="80"
                width="80"
                color="#003057"
                ariaLabel="circles-loading"
                wrapperStyle={{}}
                wrapperClass=""
                visible={true}
              />
            </Box>
          ) : !data?.graph ? (
            <Box
              fontSize={{ lg: "20px" }}
              ml={{ lg: "4rem" }}
              fontWeight={"bold"}
            >
              No result
            </Box>
          ) : isNetworkMap === "graph" ? (
            <div className="network-map">
              <button className="topButton">Network Map</button>
              {/* <img src={NetworkMap} alt='Network Map' /> */}
              <GraphComponent
                graphData={data?.graph}
                setInstitution={setUniversityName}
                setTopic={setTopicType}
                setResearcher={setResearcherType}
              />
            </div>
          ) : isNetworkMap === "map" ? (
            <Box width="100%" height="500px">
              {data?.search === "topic" ? (
                <MapMetadata data={data} />
              ) : (
                <h1>Map not available!</h1>
              )}
            </Box>
          ) : isNetworkMap === "list" ? (
            <div>
              {data?.search === "institution" ? (
                data?.has_multiple_institutions ? (
                  <MultiInstitutionMetadata
                    institutionsMetadata={data?.all_institution_metadata}
                    setTopic={setTopicType}
                  />
                ) : (
                  <InstitutionMetadata
                    data={data}
                    setTopic={setTopicType}
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                  />
                )
              ) : data?.search === "topic" ? (
                <TopicMetadata
                  data={data}
                  setInstitution={setUniversityName}
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              ) : data?.search === "researcher" ? (
                <ResearcherMetadata
                  data={data}
                  setTopic={setTopicType}
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              ) : data?.search === "researcher-institution" ? (
                <InstitutionResearcherMetaData
                  data={data}
                  setTopic={setTopicType}
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              ) : data?.search === "topic-researcher" ? (
                <TopicResearcherMetadata
                  data={data}
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              ) : data?.search === "topic-institution" ? (
                <TopicInstitutionMetadata
                  data={data}
                  setResearcher={setResearcherType}
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              ) : (
                <AllThreeMetadata
                  data={data}
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              )}
            </div>
          ) : isNetworkMap === "map" ? (
            <Box width="100%" height="500px">
              {data?.search === "topic" ? (
                <MapMetadata data={data} />
              ) : (
                <h1>Map not available!</h1>
              )}
            </Box>
          ) : (
            <Box></Box>
          )}
        </div>
      </div>
    </Box>
  );
};

export default Search;
