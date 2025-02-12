import { useEffect, useRef, useState, useCallback } from "react";
import { Circles } from "react-loader-spinner";
import { useSearchParams } from "react-router-dom";
import {
  Box,
  Button,
  Checkbox,
  Flex,
  Text
} from "@chakra-ui/react";
import "../styles/Search.css"; // Keep your existing styles
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

/** MAX input length for text fields */
const MAX_LENGTH = 60;
/** Maximum number of topic tags (from the new code) */
const MAX_TOPIC_TAGS = 6;

/**
 * A reusable TopicTagsInput component from the new code (c371ba2).
 */
interface TopicTagsInputProps {
  topicTags: string[];
  setTopicTags: React.Dispatch<React.SetStateAction<string[]>>;
  setSuggestedTopics: React.Dispatch<React.SetStateAction<any[]>>;
}
const TopicTagsInput: React.FC<TopicTagsInputProps> = ({
  topicTags,
  setTopicTags,
  setSuggestedTopics
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
    // The second argument "true" in handleAutofill means "search topics"
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

/** Keep track of the last request ID to prevent race conditions */
let latestRequestId = 0;

const Search = () => {
  // Pull existing query params
  const [searchParams] = useSearchParams();
  const institutionParam = searchParams.get("institution") || "";
  const typeParam = searchParams.get("type") || "Education";
  const researcherParam = searchParams.get("researcher") || "";

  // Convert topic param into an array if comma-separated
  const topicParam = searchParams.get("topic") || "";
  const initialTopicTags = topicParam
    ? topicParam.split(",").map((t) => t.trim()).filter((t) => t.length > 0)
    : [];

  // Keep the new approach to topics as an array
  const [topicTags, setTopicTags] = useState<string[]>(initialTopicTags);

  // The user’s states from HEAD + new code combined
  const [universityName, setUniversityName] = useState(institutionParam);
  const [institutionType, setInstitutionType] = useState(typeParam);
  const [researcherType, setResearcherType] = useState(researcherParam);

  // Additional states from HEAD code: handling a second org, second researcher, CSV uploads
  const [universityName2, setUniversityName2] = useState("");
  const [isAddOrgChecked, setIsAddOrgChecked] = useState(false);
  const [orgList, setOrgList] = useState<File | null>(null);
  const [isAddPersonChecked, setIsAddPersonChecked] = useState(false);
  const [personList, setPersonList] = useState<File | null>(null);
  const orgInputRef = useRef<HTMLInputElement>(null);
  const personInputRef = useRef<HTMLInputElement>(null);

  // Searching states
  const [data, setData] = useState<ResearchDataInterface>(initialValue);
  const [isLoading, setIsLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [suggestedInstitutions, setSuggestedInstitutions] = useState<any[]>([]);
  const [suggestedTopics, setSuggestedTopics] = useState<any[]>([]);

  // Toggle between "list", "graph", or "map"
  const [isNetworkMap, setIsNetworkMap] = useState("list");

  /**
   * Utility function (c371ba2) to get the topic string for the search request
   */
  const getTopicString = () => topicTags.join(",");

  /**
   * This helps build a combined search query for display, if needed
   */
  const combinedSearchQuery = [
    universityName,
    ...topicTags,
    researcherType
  ].filter(Boolean).join(" ");

  // Called when user clicks "Upload Org List" or "Upload Person List"
  const handleListClick = (ref: React.RefObject<HTMLInputElement>) => {
    ref?.current?.click();
  };

  // Called when a CSV file is selected
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

  /**
   * Actually sends the POST request to the backend depending on the search type
   */
  const sendSearchRequest = (search: SearchType) => {
    const requestId = ++latestRequestId;
    fetch(`${baseUrl}/initial-search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        organization: universityName,
        type: institutionType,
        topic: getTopicString(),
        researcher: researcherType
      })
    })
      .then((res) => res.json())
      .then((incoming) => {
        if (requestId !== latestRequestId) return; // Drop stale responses

        // Transform the response into our "data" shape, just like c371ba2
        const dataObj =
          search === "institution"
            ? {
              institution_name: incoming?.metadata?.name,
              is_hbcu: incoming?.metadata?.hbcu,
              cited_count: incoming?.metadata?.cited_count,
              author_count: incoming?.metadata?.author_count,
              works_count: incoming?.metadata?.works_count,
              institution_url: incoming?.metadata?.homepage,
              open_alex_link: incoming?.metadata?.oa_link,
              ror_link: incoming?.metadata?.ror,
              graph: incoming?.graph,
              topics: incoming?.list,
              search
            }
            : search === "topic"
              ? {
                topic_name: incoming?.metadata?.name,
                topic_clusters: incoming?.metadata?.topic_clusters,
                graph: incoming?.graph,
                cited_count: incoming?.metadata?.cited_by_count,
                author_count: incoming?.metadata?.researchers,
                works_count: incoming?.metadata?.work_count,
                open_alex_link: incoming?.metadata?.oa_link,
                organizations: incoming?.list,
                search
              }
              : search === "researcher"
                ? {
                  institution_name: incoming?.metadata?.current_institution,
                  researcher_name: incoming?.metadata?.name,
                  orcid_link: incoming?.metadata?.orcid,
                  cited_count: incoming?.metadata?.cited_by_count,
                  works_count: incoming?.metadata?.work_count,
                  graph: incoming?.graph,
                  open_alex_link: incoming?.metadata?.oa_link,
                  topics: incoming?.list,
                  institution_url: incoming?.metadata?.institution_url,
                  search
                }
                : search === "researcher-institution"
                  ? {
                    graph: incoming?.graph,
                    topics: incoming?.list,
                    institution_url: incoming?.metadata?.homepage,
                    institution_name: incoming?.metadata?.institution_name,
                    researcher_name: incoming?.metadata?.researcher_name,
                    orcid_link: incoming?.metadata?.orcid,
                    works_count: incoming?.metadata?.work_count,
                    cited_count: incoming?.metadata?.cited_by_count,
                    ror_link: incoming?.metadata?.ror,
                    open_alex_link: incoming?.metadata?.institution_oa_link,
                    researcher_open_alex_link: incoming?.metadata?.researcher_oa_link,
                    search
                  }
                  : search === "topic-researcher"
                    ? {
                      graph: incoming?.graph,
                      works: incoming?.list,
                      institution_name: incoming?.metadata?.current_institution,
                      topic_name: incoming?.metadata?.topic_name,
                      researcher_name: incoming?.metadata?.researcher_name,
                      orcid_link: incoming?.metadata?.orcid,
                      works_count: incoming?.metadata?.work_count,
                      cited_count: incoming?.metadata?.cited_by_count,
                      open_alex_link: incoming?.metadata?.topic_oa_link,
                      researcher_open_alex_link: incoming?.metadata?.researcher_oa_link,
                      topic_clusters: incoming?.metadata?.topic_clusters,
                      search
                    }
                    : search === "topic-institution"
                      ? {
                        graph: incoming?.graph,
                        institution_name: incoming?.metadata?.institution_name,
                        topic_name: incoming?.metadata?.topic_name,
                        institution_url: incoming?.metadata?.homepage,
                        cited_count: incoming?.metadata?.cited_by_count,
                        works_count: incoming?.metadata?.work_count,
                        author_count: incoming?.metadata?.people_count,
                        open_alex_link: incoming?.metadata?.institution_oa_link,
                        topic_open_alex_link: incoming?.metadata?.topic_oa_link,
                        ror_link: incoming?.metadata?.ror,
                        topic_clusters: incoming?.metadata?.topic_clusters,
                        authors: incoming?.list,
                        search
                      }
                      : {
                        graph: incoming?.graph,
                        works: incoming?.list,
                        institution_url: incoming?.metadata?.homepage,
                        institution_name: incoming?.metadata?.institution_name,
                        researcher_name: incoming?.metadata?.researcher_name,
                        topic_name: incoming?.metadata?.topic_name,
                        orcid_link: incoming?.metadata?.orcid,
                        works_count: incoming?.metadata?.work_count,
                        cited_count: incoming?.metadata?.cited_by_count,
                        ror_link: incoming?.metadata?.ror,
                        open_alex_link: incoming?.metadata?.institution_oa_link,
                        topic_open_alex_link: incoming?.metadata?.topic_oa_link,
                        researcher_open_alex_link: incoming?.metadata?.researcher_oa_link,
                        topic_clusters: incoming?.metadata?.topic_clusters,
                        search
                      };

        setData({ ...initialValue, ...dataObj });
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

  /**
   * Decide which search type to send based on what the user typed in.
   */
  const handleSearch = () => {
    setIsLoading(true);

    const topicString = getTopicString();
    const hasTopic = topicString.length > 0;
    const hasInstitution = !!universityName;
    const hasResearcher = !!researcherType;

    if (hasTopic && hasInstitution && hasResearcher) {
      sendSearchRequest("all-three-search");
    } else if (
      (hasTopic && hasResearcher) ||
      (hasResearcher && hasInstitution) ||
      (hasTopic && hasInstitution)
    ) {
      if (hasTopic && hasResearcher) sendSearchRequest("topic-researcher");
      else if (hasResearcher && hasInstitution)
        sendSearchRequest("researcher-institution");
      else if (hasTopic && hasInstitution)
        sendSearchRequest("topic-institution");
    } else if (hasTopic || hasInstitution || hasResearcher) {
      if (hasTopic) sendSearchRequest("topic");
      else if (hasInstitution) sendSearchRequest("institution");
      else if (hasResearcher) sendSearchRequest("researcher");
    } else {
      // fallback: get-default-graph
      fetch(`${baseUrl}/get-default-graph`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: null
      })
        .then((res) => res.json())
        .then((incoming) => {
          setData({ ...initialValue, graph: incoming?.graph });
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

  /**
   * Re-run search each time relevant inputs change.
   */
  useEffect(() => {
    handleSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [universityName, institutionType, topicTags, researcherType]);

  return (
    <Box>
      {/* Hamburger icon + "List/Graph/Map" buttons */}
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
        {/* Collapsible sidebar */}
        {showSidebar && (
          <div className="sidebar">
            {/* Institution input */}
            <input
              type="text"
              value={universityName}
              list="institutions"
              onChange={(e) => {
                const val = e.target.value.slice(0, MAX_LENGTH);
                setUniversityName(val);
                handleAutofill(val, false, setSuggestedTopics, setSuggestedInstitutions);
              }}
              placeholder="University Name"
              className="textbox"
              maxLength={MAX_LENGTH}
            />
            <div className="charCountSidebar">
              {MAX_LENGTH - universityName.length} characters remaining
            </div>
            <Suggested suggested={suggestedInstitutions} institutions={true} />

            {/* Optionally add a second org (HEAD code) */}
            {isAddOrgChecked && (
              <>
                <input
                  type="text"
                  value={universityName2}
                  list="institutions"
                  onChange={(e) => {
                    const val = e.target.value.slice(0, MAX_LENGTH);
                    setUniversityName2(val);
                    handleAutofill(
                      val,
                      false,
                      setSuggestedTopics,
                      setSuggestedInstitutions
                    );
                  }}
                  placeholder="Another University"
                  className="textbox"
                  maxLength={MAX_LENGTH}
                />
                <div className="charCountSidebar">
                  {MAX_LENGTH - universityName2.length} characters remaining
                </div>
                <Suggested suggested={suggestedInstitutions} institutions={true} />
              </>
            )}

            {/* Topic tags (merged from c371ba2) */}
            <TopicTagsInput
              topicTags={topicTags}
              setTopicTags={setTopicTags}
              setSuggestedTopics={setSuggestedTopics}
            />

            {/* Just an example: you might want more institutionType options */}
            <select
              value={institutionType}
              onChange={(e) => setInstitutionType(e.target.value)}
              className="dropdown"
            >
              <option value="Education">HBCU</option>
            </select>

            {/* Researcher input */}
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

            {/* Optionally add a second person (HEAD code) */}
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

            {/* Checkboxes for multiple org/person plus CSV uploads (HEAD code) */}
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

        {/* Main content area */}
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
