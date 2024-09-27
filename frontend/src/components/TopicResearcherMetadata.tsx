import React from 'react';

import { Box, Flex, Text } from '@chakra-ui/react';

import { ResearchDataInterface } from '../utils/interfaces';

const TopicResearcherMetadata = ({data}: {data: ResearchDataInterface}) => {
  return (
    <Flex
      display={{base: 'block', lg: 'flex'}}
      justifyContent={'space-between'}
      mt='0.6rem'
      className='list-map'
    >
      <Box w={{lg: '34%'}}>
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
            Topic Clusters
          </Text>
          <Box ml='2rem'>
            {data?.topic_clusters?.map((cluster) => (
              <Text mt='0.3rem'>{cluster}</Text>
            ))}
          </Box>
        </Box>
        <a target='_blank' rel='noreferrer' href={data?.open_alex_link}>
          View Topic on OpenAlex
        </a>
        <a
          target='_blank'
          rel='noreferrer'
          href={data?.researcher_open_alex_link}
        >
          View Researcher on OpenAlex
        </a>
      </Box>
      <Box w={{lg: '64%'}} mt={{base: '.9rem', lg: 0}}>
        <Box display={'flex'} justifyContent={'space-between'}>
          <Box w='72%'>
            <Text fontSize={'18px'} fontWeight={600}>
              Work
            </Text>
            <Box mt='.5rem'>
              {data?.works?.map((topic) => (
                <Text key={topic[0]} fontSize={'14px'}>
                  {topic[0]}
                </Text>
              ))}
            </Box>
          </Box>
          <Box w='26%'>
            <Text fontSize={'18px'} fontWeight={600}>
              No of citations
            </Text>
            <Box mt='.5rem'>
              {data?.works?.map((topic) => (
                <Text key={topic[0]} fontSize={'14px'}>
                  {topic[1]}
                </Text>
              ))}
            </Box>
          </Box>
        </Box>
      </Box>
    </Flex>
  );
};

export default TopicResearcherMetadata;
