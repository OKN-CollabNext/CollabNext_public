import React, { useState } from 'react';
import { Box, Flex, Text } from '@chakra-ui/react';
import { ResearchDataInterface } from '../utils/interfaces';
import { TransformTopicClustersForOrb } from './TransformTopicCluster.js';
import TopicClusterGraphComponent from './TopicClusterGraphComponent';

import styles from '../styles/SearchHighlight.module.css';

interface TopicMetadataProps {
  data: ResearchDataInterface;
  setInstitution: React.Dispatch<React.SetStateAction<string>>;
  searchQuery?: string;
}

function highlightText(text: string, query?: string) {
  if (!text) return '';
  if (!query) return text;
  const parts = text.split(new RegExp(`(${query})`, 'gi'));
  return parts.map((part, i) =>
    part.toLowerCase() === query.toLowerCase() ? (
      <span key={i} className={styles.highlight}>
        {part}
      </span>
    ) : (
      part
    )
  );
}

const TopicMetadata: React.FC<TopicMetadataProps> = ({
  data,
  setInstitution,
  searchQuery
}) => {
  const [showTopicClusterGraph, setTopicClusterGraph] = useState(false);

  const handleTopicClusterClick = () => {
    setTopicClusterGraph(!showTopicClusterGraph);
  };

  return (
    <Flex
      display={{ base: 'block', lg: 'flex' }}
      justifyContent={'space-between'}
      mt='0.6rem'
      className='list-map'
    >
      <Box w={{ lg: '34%' }}>
        <button className='topButton'>List Map</button>
        <h2>{highlightText(data?.topic_name || '', searchQuery)}</h2>

        <Box mt='0.4rem'>
          <Text fontSize={'17px'} fontWeight={'600'}>
            <a
              style={{ cursor: 'pointer', textDecoration: 'underline' }}
              onClick={handleTopicClusterClick}
            >
              Topic Clusters
            </a>
          </Text>
        </Box>

        <p>
          {highlightText(`Total ${data?.author_count} authors`, searchQuery)}
        </p>
        <p>
          {highlightText(`Total ${data?.works_count} works`, searchQuery)}
        </p>
        <p>
          {highlightText(`Total ${data?.cited_count} citations`, searchQuery)}
        </p>
        <a target='_blank' rel='noreferrer' href={data?.open_alex_link}>
          {highlightText('View on OpenAlex', searchQuery)}
        </a>
      </Box>

      <Box w={{ lg: '64%' }} mt={{ base: '.9rem', lg: 0 }}>
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
            <TopicClusterGraphComponent
              graphData={TransformTopicClustersForOrb(data, data?.topic_clusters)}
            />
          </Box>
        ) : (
          <Box mt='.5rem'>
            {data?.organizations?.map((topic, idx) => (
              <Flex justifyContent={'space-between'} key={idx}>
                <Text
                  fontSize='14px'
                  w='72%'
                  onClick={() => setInstitution(topic[0])}
                  textDecoration={'underline'}
                  cursor='pointer'
                >
                  {highlightText(topic[0] || '', searchQuery)}
                </Text>
                <Text fontSize='14px' w='26%'>
                  {highlightText(String(topic[1] || ''), searchQuery)}
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
