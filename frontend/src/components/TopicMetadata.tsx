import React, { useState } from 'react';

import { Box, Flex, Text } from '@chakra-ui/react';

import { ResearchDataInterface } from '../utils/interfaces';

import { TransformTopicClustersForOrb } from './TransformTopicCluster.js';
import TopicClusterGraphComponent from './TopicClusterGraphComponent';

const TopicMetadata = ({
  data,
  setInstitution,
}: {
  data: ResearchDataInterface;
  setInstitution: React.Dispatch<React.SetStateAction<string>>;
}) => {
  const [showTopicClusterGraph, setTopicClusterGraph] = useState(false);
  const handleTopicClusterClick = () => {
    setTopicClusterGraph(!showTopicClusterGraph);
  }
  return (
    <Flex
      display={{base: 'block', lg: 'flex'}}
      justifyContent={'space-between'}
      mt='0.6rem'
      className='list-map'
    >
      <Box w={{lg: '34%'}}>
        <button className='topButton'>List Map</button>
        <h2>{data?.topic_name}</h2>
        <Box mt='0.4rem'>
          <Text fontSize={'17px'} fontWeight={'600'}>
            <a style={{ cursor: 'pointer', textDecoration: 'underline' }} onClick={handleTopicClusterClick}>
              Topic Clusters
            </a>
          </Text>
        </Box>
        <p>Total {data?.author_count} authors</p>
        <p>Total {data?.works_count} works</p>
        <p>Total {data?.cited_count} citations</p>
        <a target='_blank' rel='noreferrer' href={data?.open_alex_link}>
          View on OpenAlex
        </a>
      </Box>
      <Box w={{lg: '64%'}} mt={{base: '.9rem', lg: 0}}>
        <Box display={'flex'} justifyContent={'space-between'}>
          <Text fontSize={'18px'} fontWeight={600} w='72%'>
            Organization
          </Text>
          <Text fontSize={'18px'} fontWeight={600} w='26%'>
            No of people
          </Text>
        </Box>
        {showTopicClusterGraph ? (
          <Box mt='1rem' w={{ lg: '70%' }} mx='auto'>
            <TopicClusterGraphComponent graphData={TransformTopicClustersForOrb(data, data?.topic_clusters)} />
          </Box>
        ) : (
          <Box mt='.5rem'>
          {data?.organizations?.map((topic) => (
            <Flex justifyContent={'space-between'}>
              <Text
                fontSize='14px'
                w='72%'
                onClick={() => setInstitution(topic[0])}
                textDecoration={'underline'}
                cursor='pointer'
              >
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
  );
};

export default TopicMetadata;
