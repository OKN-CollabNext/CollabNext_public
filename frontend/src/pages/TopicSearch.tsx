import React, { useEffect, useState, useCallback } from "react";
import { Circles } from "react-loader-spinner";
import { Box, Button } from "@chakra-ui/react";
import GraphComponent from "../components/GraphComponent";
import { baseUrl } from "../utils/constants";
import { FaCaretDown, FaCaretRight, FaSearch } from "react-icons/fa";
import "../styles/Search.css";
import "../styles/TopicSearch.css";

const MAX_TOPIC_TAGS = 6;

interface TopicTagsProps {
  topicTags: string[];
  setTopicTags: React.Dispatch<React.SetStateAction<string[]>>;
}

const TopicTagsInput: React.FC<TopicTagsProps> = ({ topicTags, setTopicTags }) => {
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
    <div className="topicSearchTagsWrapper">
      <p className="tagInstructionsTopic">Press Space or Comma after each keyword</p>
      <ul className="tagListTopic">
        {topicTags.map((tag, index) => (
          <li key={index} className="tagItemTopic">
            {tag}
            <span
              onClick={() => handleRemoveTag(tag)}
              className="removeIconTopic"
            >
              &times;
            </span>
          </li>
        ))}
        {topicTags.length < MAX_TOPIC_TAGS && (
          <li className="inputItemTopic">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              className="tagInputTopic"
              placeholder="Type a topic keyword..."
            />
          </li>
        )}
      </ul>
      <div className="tagDetailsTopic">
        <p>
          <span>{MAX_TOPIC_TAGS - topicTags.length}</span> tags remaining
        </p>
      </div>
    </div>
  );
};

const TopicSearch = () => {
  const [topicTags, setTopicTags] = useState<string[]>([]);
  const [data, setData] = useState<{ graph?: { nodes: any[]; edges: any[] } }>(
    {}
  );
  const [isLoading, setIsLoading] = useState(false);

  const [collapsed, setCollapsed] = useState(false);

  const getTopicString = () => topicTags.join(",");

  const toggleCollapse = () => {
    setCollapsed((prev) => !prev);
  };

  const handleSearch = useCallback(() => {
    const topicStr = getTopicString();
    setIsLoading(true);

    if (!topicStr) {
      fetch(`${baseUrl}/get-topic-space-default-graph`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: null,
      })
        .then((res) => res.json())
        .then((data) => {
          setData({
            graph: data?.graph,
          });
          setIsLoading(false);
        })
        .catch((error) => {
          setIsLoading(false);
          setData({});
          console.log(error);
        });
      return;
    }

    fetch(`${baseUrl}/search-topic-space`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic: topicStr,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setData({
          graph: data?.graph,
        });
        setIsLoading(false);
      })
      .catch((error) => {
        setIsLoading(false);
        setData({});
        console.log(error);
      });
  }, [topicTags]);

  useEffect(() => {
    handleSearch();
  }, []);

  return (
    <div className="topicSearchContainer">
      <div className="topicDropdownColumn">
        <div className="columnHeader" onClick={toggleCollapse}>
          {collapsed ? <FaCaretRight /> : <FaCaretDown />}
          <div>By Topic Keyword</div>
        </div>
        {!collapsed && (
          <div className="columnBody">
            <TopicTagsInput topicTags={topicTags} setTopicTags={setTopicTags} />
            <Button
              leftIcon={<FaSearch />}
              width="100%"
              marginTop="10px"
              backgroundColor="transparent"
              color="white"
              border="2px solid white"
              isLoading={isLoading}
              onClick={handleSearch}
            >
              Search
            </Button>
          </div>
        )}
      </div>

      <div className="topicSearchContent">
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
          <Box fontSize={{ lg: "20px" }} fontWeight={"bold"}>
            No result
          </Box>
        ) : (
          <div className="network-map">
            <button className="topButton">Network Map</button>
            <GraphComponent graphData={data?.graph} />
          </div>
        )}
      </div>
    </div>
  );
};

export default TopicSearch;
