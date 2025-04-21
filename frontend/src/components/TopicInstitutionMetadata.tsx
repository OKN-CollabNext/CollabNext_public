import React, { useState } from 'react';
import { Box, Button, Flex, Text } from '@chakra-ui/react';
import { ResearchDataInterface } from '../utils/interfaces';
import TopicClusterGraphComponent from './TopicClusterGraphComponent';
import { TransformTopicClustersForOrb } from './TransformTopicCluster.js';
import ExpandableWorksCell from './ExpandableWorksCell';

const TopicInstitutionMetadata = ({
  data,
  setResearcher,
  currentPage,
  totalPages,
  onPageChange,
}: {
  data: ResearchDataInterface;
  setResearcher: React.Dispatch<React.SetStateAction<string>>;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) => {
  const [showTopicClusterGraph, setTopicClusterGraph] = useState(false);
  const handleTopicClusterClick = () => setTopicClusterGraph(prev => !prev);
  /* filter out any entries we don't want to preserve with no author name or zero works */
  const authorsRaw = data?.authors ?? [];
  const authors = Array.isArray(authorsRaw)
    ? authorsRaw.filter(
      ([person, works]) => Boolean(person) && works > 0
    )
    : [];

  return (
    <>
      <Flex
        display={{ base: 'block', lg: 'flex' }}
        justifyContent="space-between"
        mt="0.6rem"
        className="list-map"
      >
        <Box w={{ lg: '34%' }}>
          <button className="topButton">List Map</button>
          <h2>{data?.institution_name}</h2>
          <h2>{data?.topic_name}</h2>
          <a target="_blank" rel="noreferrer" href={data?.institution_url}>
            {data?.institution_url}
          </a>
          <p>Total {data?.author_count} authors</p>
          <p>Total {data?.works_count} works</p>
          <p>Total {data?.cited_count} citations</p>
          <a target="_blank" rel="noreferrer" href={data?.open_alex_link}>
            View Institution on OpenAlex
          </a>
          <a target="_blank" rel="noreferrer" href={data?.topic_open_alex_link}>
            View Keyword on OpenAlex
          </a>
          {data?.ror_link && (
            <a target="_blank" rel="noreferrer" href={data.ror_link}>
              RORID – {data.ror_link.split('/').pop()}
            </a>
          )}
          <Box mt="0.4rem">
            <Text fontSize="17px" fontWeight="600">
              <span
                style={{ cursor: 'pointer', textDecoration: 'underline' }}
                onClick={handleTopicClusterClick}
              >
                Topic Clusters
              </span>
            </Text>
          </Box>
        </Box>
        {showTopicClusterGraph ? (
          <Box mt="1rem" w={{ lg: '70%' }} mx="auto">
            <TopicClusterGraphComponent
              graphData={TransformTopicClustersForOrb(
                data,
                data?.topic_clusters,
              )}
            />
          </Box>
        ) : (
          <Box w={{ lg: '64%' }} mt={{ base: '.9rem', lg: 0 }}>
            <Box display="flex" justifyContent="space-between">
              <Text fontSize="18px" fontWeight={600} w="32%">
                Person
              </Text>
              <Text fontSize="18px" fontWeight={600} w="32%">
                # of Works
              </Text>
              <Text fontSize="18px" fontWeight={600} w="32%">
                Articles
              </Text>
            </Box>

            <Box mt=".5rem">
              {authors.length === 0 ? (
                <Box p={4} textAlign="center">
                  <Text fontSize="16px" color="gray.500">
                    No authors (doesn't mean they've been eliminated) publish on “{data.topic_name}” at {data.institution_name}.
                  </Text>
                </Box>
              ) : (
                authors.map(([person, works], i) => (
                  <Flex
                    justifyContent="space-between"
                    key={`${person}-${i}`}
                    mb="4px"
                  >
                    <Text
                      fontSize="14px"
                      w="32%"
                      onClick={() => setResearcher(person)}
                      textDecoration="underline"
                      cursor="pointer"
                    >
                      {person}
                    </Text>
                    <Text fontSize="14px" w="32%">
                      {works}
                    </Text>
                    <ExpandableWorksCell
                      authorName={person}
                      topicName={data?.topic_name ?? ''}
                    />
                  </Flex>
                ))
              )}
            </Box>
          </Box>
        )}
      </Flex>
      {authors.length > 0 && (
        <Flex justifyContent="center" mt={4} gap={2} alignItems="center">
          <Button
            onClick={() => onPageChange(currentPage - 1)}
            isDisabled={currentPage === 1}
            size="sm"
          >
            Previous
          </Button>
          <Text fontSize="sm">
            Page {currentPage} of {totalPages}
          </Text>
          <Button
            onClick={() => onPageChange(currentPage + 1)}
            isDisabled={currentPage === totalPages}
            size="sm"
          >
            Next
          </Button>
        </Flex>
      )}
    </>
  );
};

export default TopicInstitutionMetadata;
