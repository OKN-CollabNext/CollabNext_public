import { useEffect, useRef, useState, useCallback } from "react";
import { Circles } from "react-loader-spinner";
import { useSearchParams } from "react-router-dom";
import {
  Box, Button, Checkbox, Flex, Text,
} from "@chakra-ui/react";
import "../styles/Search.css";
import AllThreeMetadata from "../components/AllThreeMetadata";
import GraphComponent from "../components/GraphComponent";
import InstitutionMetadata from "../components/InstitutionMetadata";
import InstitutionResearcherMetaData from "../components/InstitutionResearcherMetaData";
import ResearcherMetadata from "../components/ResearcherMetadata";
import Suggested from "../components/Suggested";
import TopicInstitutionMetadata from "../components/TopicInstitutionMetadata";
import TopicMetadata from "../components/TopicMetadata";
import TopicResearcherMetadata from "../components/TopicResearcherMetadata";
import { baseUrl, handleAutofill, initialValue } from "../utils/constants";
import { ResearchDataInterface, SearchType } from "../utils/interfaces";
import { FaBars } from "react-icons/fa";
const MAX_LENGTH = 60;
const MAX_TOPIC_TAGS = 6;
interface TopicTagsInputProps {
  topicTags: string[];
  setTopicTags: React.Dispatch<React.SetStateAction<string[]>>;
  setSuggestedTopics: React.Dispatch<React.SetStateAction<any[]>>;
}

const TopicTagsInput: React.FC<TopicTagsInputProps> = ({
  topicTags,
  setTopicTags,
  setSuggestedTopics,
}) => {
  const [inputValue, setInputValue] = useState("");

  const handleRemoveTag = useCallback(
    (tagToRemove: string) => {
      setTopicTags((prev) => prev.filter((t) => t !== tagToRemove));
    },
    [setTopicTags]
  );

  const addTag = (newTag: string) => {
    const lowerTag = newTag.toLowerCase();
    if (!topicTags.includes(lowerTag) && topicTags.length < MAX_TOPIC_TAGS) {
      setTopicTags([...topicTags, lowerTag]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputValue(val);
    handleAutofill(val, true, setSuggestedTopics, () => { });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if ((e.key === " " || e.key === ",") && inputValue.trim()) {
      e.preventDefault();
      addTag(inputValue.trim());
      setInputValue("");
    } else if (e.key === "Backspace" && !inputValue) {
      if (topicTags.length > 0) {
        handleRemoveTag(topicTags[topicTags.length - 1]);
      }
    }
  };

  return (
    <div className="topicTagsContainer">
      <p className="tagInstructions">Press Space or Comma after each keyword</p>
      <ul className="tagList">
        {topicTags.map((tag, index) => (
          <li key={index} className="tagItem">
            {tag}
            <span className="removeIcon" onClick={() => handleRemoveTag(tag)}>
              &times;
            </span>
          </li>
        ))}
        {topicTags.length < MAX_TOPIC_TAGS && (
          <li className="inputItem">
            <input
              type="text"
              placeholder="Type a topic keyword..."
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              className="tagInput"
            />
          </li>
        )}
      </ul>
      <div className="tagDetails">
        <p>
          <span>{MAX_TOPIC_TAGS - topicTags.length}</span> tags remaining
        </p>
      </div>
    </div>
  );
};

let latestRequestId = 0;

const Search = () => {
  let [searchParams] = useSearchParams();
  const institutionParam = searchParams.get("institution") || "";
  const typeParam = searchParams.get("type") || "Education";
  const topicParam = searchParams.get("topic") || "";
  const researcherParam = searchParams.get("researcher") || "";
  const initialTopicTags = topicParam
    ? topicParam.split(",").map((t) => t.trim()).filter((t) => t.length > 0)
    : [];
  const [isNetworkMap, setIsNetworkMap] = useState("list");
  const [universityName, setUniversityName] = useState(institutionParam);
  const [topicTags, setTopicTags] = useState<string[]>(initialTopicTags);
  const [institutionType, setInstitutionType] = useState(typeParam);
  const [researcherType, setResearcherType] = useState(researcherParam);
  const [data, setData] = useState<ResearchDataInterface>(initialValue);
  const [isLoading, setIsLoading] = useState(false);
  const [isAddOrgChecked, setIsAddOrgChecked] = useState(false);
  const [orgList, setOrgList] = useState<File | null>(null);
  const [isAddPersonChecked, setIsAddPersonChecked] = useState(false);
  const [personList, setPersonList] = useState<File | null>(null);
  const [suggestedInstitutions, setSuggestedInstitutions] = useState<any[]>([]);
  const [suggestedTopics, setSuggestedTopics] = useState<any[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
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
      if (file && file.name.endsWith(".csv")) {
        setList(file);
      } else if (file) {
        alert("Please select a valid CSV file.");
      }
    }
  };

  const getTopicString = () => topicTags.join(",");

  const combinedSearchQuery = [
    universityName,
    ...topicTags,
    researcherType
  ]
    .filter(Boolean)
    .join(" ")

  const sendSearchRequest = (search: SearchType) => {
    const requestId = ++latestRequestId;
    fetch(`${baseUrl}/initial-search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        organization: universityName,
        type: institutionType,
        topic: getTopicString(),
        researcher: researcherType,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (requestId !== latestRequestId) return;
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
        if (requestId === latestRequestId) {
          setData(initialValue);
          setIsLoading(false);
        }
        console.log(error);
      });
  };

  const handleSearch = () => {
    setIsLoading(true);

    const topicString = getTopicString();
    const hasTopic = topicString.length > 0;
    const hasInstitution = !!universityName;
    const hasResearcher = !!researcherType;

    if (hasTopic && hasInstitution && hasResearcher) {
      sendSearchRequest("all-three-search");
    }
    else if (
      (hasTopic && hasResearcher) ||
      (hasResearcher && hasInstitution) ||
      (hasTopic && hasInstitution)
    ) {
      if (hasTopic && hasResearcher) sendSearchRequest("topic-researcher");
      else if (hasResearcher && hasInstitution)
        sendSearchRequest("researcher-institution");
      else if (hasTopic && hasInstitution)
        sendSearchRequest("topic-institution");
    }
    else if (hasTopic || hasInstitution || hasResearcher) {
      if (hasTopic) sendSearchRequest("topic");
      else if (hasInstitution) sendSearchRequest("institution");
      else if (hasResearcher) sendSearchRequest("researcher");
    }
    else {
      fetch(`${baseUrl}/get-default-graph`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: null,
      })
        .then((res) => res.json())
        .then((data) => {
          setData({
            ...initialValue,
            graph: data?.graph,
          });
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

  useEffect(() => {
    handleSearch();
  }, [universityName, institutionType, topicTags, researcherType]);

  return (
    <Box>
      <div className="searchPageHeader">
        <FaBars
          className="hamburgerIcon"
          onClick={() => setShowSidebar(!showSidebar)}
        />
        <Flex justifyContent={"flex-end"} flex="1" px="2rem">
          {["List", "Graph", "Map"].map((value) => (
            <Button
              key={value}
              onClick={() => setIsNetworkMap(value.toLowerCase())}
              bg="linear-gradient(#053257, #7e7e7e)"
              color="white"
              mr="1rem"
            >
              {value}
            </Button>
          ))}
        </Flex>
      </div>

      <div className="main-content">
        {showSidebar && (
          <div className="sidebar">
            <input
              type="text"
              value={universityName}
              list="institutions"
              onChange={(e) => {
                const val = e.target.value.slice(0, MAX_LENGTH);
                setUniversityName(val);
                handleAutofill(val, false, setSuggestedTopics, setSuggestedInstitutions);
              }}
              placeholder={"University Name"}
              className="textbox"
              maxLength={MAX_LENGTH}
            />
            <div className="charCountSidebar">
              {MAX_LENGTH - universityName.length} characters remaining
            </div>
            <Suggested suggested={suggestedInstitutions} institutions={true} />

            {isAddOrgChecked && (
              <>
                <input
                  type="text"
                  list="institutions"
                  onChange={(e) => {
                    const val = e.target.value.slice(0, MAX_LENGTH);
                    setUniversityName(val);
                    handleAutofill(val, false, setSuggestedTopics, setSuggestedInstitutions);
                  }}
                  placeholder={"Another University"}
                  className="textbox"
                  maxLength={MAX_LENGTH}
                />
                <div className="charCountSidebar">
                  {MAX_LENGTH - universityName.length} characters remaining
                </div>
                <Suggested suggested={suggestedInstitutions} institutions={true} />
              </>
            )}

            <TopicTagsInput
              topicTags={topicTags}
              setTopicTags={setTopicTags}
              setSuggestedTopics={setSuggestedTopics}
            />

            <select
              value={institutionType}
              onChange={(e) => setInstitutionType(e.target.value)}
              className="dropdown"
            >
              <option value="Education">HBCU</option>
            </select>

            <input
              type="text"
              value={researcherType}
              onChange={(e) => {
                const val = e.target.value.slice(0, MAX_LENGTH);
                setResearcherType(val);
              }}
              placeholder="Type Researcher"
              className="textbox"
              maxLength={MAX_LENGTH}
            />
            <div className="charCountSidebar">
              {MAX_LENGTH - researcherType.length} characters remaining
            </div>

            {isAddPersonChecked && (
              <>
                <input
                  type="text"
                  value=""
                  onChange={() => { }}
                  placeholder="Another Researcher"
                  className="textbox"
                />
              </>
            )}

            <Box mt=".6rem">
              <Flex justifyContent={"space-between"}>
                <Flex>
                  <Checkbox
                    mr=".2rem"
                    isChecked={isAddOrgChecked}
                    onChange={(e) => setIsAddOrgChecked(e.target.checked)}
                  />
                  <Text fontSize="11px" color={"white"}>
                    Add Another Org
                  </Text>
                </Flex>

                <Flex>
                  <Checkbox
                    mr=".2rem"
                    isChecked={isAddPersonChecked}
                    onChange={(e) => setIsAddPersonChecked(e.target.checked)}
                  />
                  <Text fontSize="11px" color={"white"}>
                    Add Another Person
                  </Text>
                </Flex>
              </Flex>

              <Box mt=".6rem">
                <Flex alignItems="center">
                  <Button
                    border="1px solid white"
                    bg="transparent"
                    color="white"
                    fontWeight={400}
                    fontSize={"13px"}
                    onClick={() => handleListClick(orgInputRef)}
                    mt=".3rem"
                    mr=".35rem"
                  >
                    {orgList?.name?.slice(0, 14) || "Upload Org List"}
                  </Button>
                  <input
                    onChange={(e) => handleListChange(e, setOrgList)}
                    type="file"
                    ref={orgInputRef}
                    accept=".csv"
                    hidden
                  />
                  {orgList && (
                    <Text
                      fontSize="11px"
                      color={"white"}
                      cursor="pointer"
                      onClick={() => {
                        setOrgList(null);
                        if (orgInputRef.current) {
                          orgInputRef.current.value = "";
                        }
                      }}
                    >
                      remove
                    </Text>
                  )}
                </Flex>

                <Flex alignItems="center">
                  <Button
                    border="1px solid white"
                    bg="transparent"
                    color="white"
                    fontWeight={400}
                    fontSize={"13px"}
                    onClick={() => handleListClick(personInputRef)}
                    mt=".3rem"
                    mr=".35rem"
                  >
                    {personList?.name?.slice(0, 14) || "Upload Person List"}
                  </Button>
                  <input
                    onChange={(e) => handleListChange(e, setPersonList)}
                    type="file"
                    ref={personInputRef}
                    accept=".csv"
                    hidden
                  />
                  {personList && (
                    <Text
                      fontSize="11px"
                      color={"white"}
                      cursor="pointer"
                      onClick={() => {
                        setPersonList(null);
                        if (personInputRef.current) {
                          personInputRef.current.value = "";
                        }
                      }}
                    >
                      remove
                    </Text>
                  )}
                </Flex>
              </Box>
            </Box>
          </div>
        )}

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
                visible={true}
              />
            </Box>
          ) : !data?.graph ? (
            <Box fontSize={{ lg: "20px" }} ml={{ lg: "4rem" }} fontWeight={"bold"}>
              No result
            </Box>
          ) : isNetworkMap === "graph" ? (
            <div className="network-map">
              <button className="topButton">Network Map</button>
              <GraphComponent
                graphData={data?.graph}
                setInstitution={setUniversityName}
                setTopic={(val) => setTopicTags(val ? [val] : [])}
                setResearcher={setResearcherType}
              />
            </div>
          ) : isNetworkMap === "list" ? (
            <div>
              {data?.search === "institution" ? (
                <InstitutionMetadata
                  data={data}
                  setTopic={(val: string) => setTopicTags(val ? [val] : [])}
                  searchQuery={combinedSearchQuery}
                />
              ) : data?.search === "topic" ? (
                <TopicMetadata
                  data={data}
                  setInstitution={setUniversityName}
                  searchQuery={combinedSearchQuery}
                />
              ) : data?.search === "researcher" ? (
                <ResearcherMetadata
                  data={data}
                  setTopic={(val: string) => setTopicTags(val ? [val] : [])}
                  searchQuery={combinedSearchQuery}
                />
              ) : data?.search === "researcher-institution" ? (
                <InstitutionResearcherMetaData
                  data={data}
                  setTopic={(val: string) => setTopicTags(val ? [val] : [])}
                  searchQuery={combinedSearchQuery}
                />
              ) : data?.search === "topic-researcher" ? (
                <TopicResearcherMetadata
                  data={data}
                  searchQuery={combinedSearchQuery}
                />
              ) : data?.search === "topic-institution" ? (
                <TopicInstitutionMetadata
                  data={data}
                  setResearcher={setResearcherType}
                  searchQuery={combinedSearchQuery}
                />
              ) : (
                <AllThreeMetadata
                  data={data}
                  searchQuery={combinedSearchQuery}
                />
              )}
            </div>
          ) : (
            <Box></Box>
          )}
        </div>
      </div>
    </Box>
  );
};

export default Search;
