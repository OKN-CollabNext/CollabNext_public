import React, { useState } from 'react';

import { Box, Button, Flex, Text } from '@chakra-ui/react';

import { ResearchDataInterface } from '../utils/interfaces';

import { TransformTopicClustersForOrb } from './TransformTopicCluster.js';
import TopicClusterGraphComponent from './TopicClusterGraphComponent';

const TopicResearcherMetadata = ({
  data,
  currentPage,
  totalPages,
  onPageChange
}: {
  data: ResearchDataInterface,
  currentPage: number,
  totalPages: number,
  onPageChange: (page: number) => void;
}) => {

  const [showTopicClusterGraph, setTopicClusterGraph] = useState(false);
  const handleTopicClusterClick = () => {
    setTopicClusterGraph(!showTopicClusterGraph);
  }

  return (
    <>
      <Flex
        display={{ base: 'block', lg: 'flex' }}
        justifyContent={'space-between'}
        mt='0.6rem'
        className='list-map'
      >
        <Box w={{ lg: '34%' }}>
          <button className='topButton'>List Map</button>
          <h2>{data?.researcher_name}</h2>
          <h2>{data?.topic_name}</h2>
          <a
            target='_blank'
            rel='noreferrer'
            className='ror'
            href={data?.orcid_link}
          >
            {data?.orcid_link}
          </a>
          <p>{data?.institution_name}</p>
          <p>Total {data?.works_count} works</p>
          <p>Total {data?.cited_count} citations</p>
          <Box mt='0.4rem'>
            <Text fontSize={'17px'} fontWeight={'600'}>
              <a style={{ cursor: 'pointer', textDecoration: 'underline' }} onClick={handleTopicClusterClick}>
                Topic Clusters
              </a>
            </Text>
          </Box>
          <a target='_blank' rel='noreferrer' href={data?.open_alex_link}>
            View Keyword on OpenAlex
          </a>
          <a
            target='_blank'
            rel='noreferrer'
            href={data?.researcher_open_alex_link}
          >
            View Researcher on OpenAlex
          </a>
        </Box>
        <Box w={{ lg: '64%' }} mt={{ base: '.9rem', lg: 0 }}>
          <Box display={'flex'} justifyContent={'space-between'}>
            <Text fontSize={'18px'} fontWeight={600} w='72%'>
              Work
            </Text>
            <Text fontSize={'18px'} fontWeight={600} w='26%'>
              No of citations
            </Text>
          </Box>
          {showTopicClusterGraph ? (
            <Box mt='1rem' w={{ lg: '70%' }} mx='auto'>
              <TopicClusterGraphComponent graphData={TransformTopicClustersForOrb(data, data?.topic_clusters)} />
            </Box>
          ) : (
            <Box mt='.5rem'>
              {data?.works?.map((topic) => (
                <Flex justifyContent={'space-between'}>
                  <Text fontSize='14px' w='72%'>
                    {topic[0]}
                  </Text>
                  <Text fontSize='14px' w='26%'>
                    {topic[1]}
                  </Text>
                </Flex>
              ))}
            </Box>
          )}
        </Box>
      </Flex>
      <Flex justifyContent="center" mt={4} gap={2} alignItems="center">
        <Button
          onClick={() => onPageChange(currentPage - 1)}
          isDisabled={currentPage === 1}
          size="sm"
        >
          Previous
        </Button>
        <Text fontSize="sm">
          Page {currentPage} of {totalPages}
        </Text>
        <Button
          onClick={() => onPageChange(currentPage + 1)}
          isDisabled={currentPage === totalPages}
          size="sm"
        >
          Next
        </Button>
      </Flex>
    </>
  );
};

export default TopicResearcherMetadata;
