import React from 'react';

import {Box, Flex, Text} from '@chakra-ui/react';

import {ResearchDataInterface} from '../utils/interfaces';

const TopicMetadata = ({data}: {data: ResearchDataInterface}) => {
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
            Topic Clusters
          </Text>
          <Box ml='2rem'>
            {data?.topic_clusters?.map((cluster) => (
              <Text mt='0.3rem'>{cluster}</Text>
            ))}
          </Box>
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
          <Box w='72%'>
            <Text fontSize={'18px'} fontWeight={600}>
              Organization
            </Text>
            <Box mt='.5rem'>
              {data?.organizations?.map((topic) => (
                <Text key={topic[0]} fontSize={'14px'}>
                  {topic[0]}
                </Text>
              ))}
            </Box>
          </Box>
          <Box w='26%'>
            <Text fontSize={'18px'} fontWeight={600}>
              No of people
            </Text>
            <Box mt='.5rem'>
              {data?.organizations?.map((topic) => (
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

export default TopicMetadata;
