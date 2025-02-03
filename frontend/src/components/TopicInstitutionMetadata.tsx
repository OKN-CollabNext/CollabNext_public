import React from 'react';

import { Box, Flex, Text } from '@chakra-ui/react';

import { ResearchDataInterface } from '../utils/interfaces';

const TopicInstitutionMetadata = ({
  data,
  setResearcher,
}: {
  data: ResearchDataInterface;
  setResearcher: React.Dispatch<React.SetStateAction<string>>;
}) => {
  return (
    <Flex
      display={{base: 'block', lg: 'flex'}}
      justifyContent={'space-between'}
      mt='0.6rem'
      className='list-map'
    >
      <Box w={{lg: '34%'}}>
        <button className='topButton'>List Map</button>
        <h2>{data?.institution_name}</h2>
        <h2>{data?.topic_name}</h2>
        <a target='_blank' rel='noreferrer' href={data?.institution_url}>
          {data?.institution_url}
        </a>
        <p>Total {data?.author_count} authors</p>
        <p>Total {data?.works_count} works</p>
        <p>Total {data?.cited_count} citations</p>
        <a target='_blank' rel='noreferrer' href={data?.open_alex_link}>
          View Institution on OpenAlex
        </a>
        <a target='_blank' rel='noreferrer' href={data?.topic_open_alex_link}>
          View Keyword on OpenAlex
        </a>
        <a target='_blank' rel='noreferrer' href={data?.ror_link}>
          RORID -{' '}
          {data?.ror_link?.split('/')[data?.ror_link?.split('/')?.length - 1]}
        </a>
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
      </Box>
      <Box w={{lg: '64%'}} mt={{base: '.9rem', lg: 0}}>
        <Box display={'flex'} justifyContent={'space-between'}>
          <Text fontSize={'18px'} fontWeight={600} w='72%'>
            Person
          </Text>
          <Text fontSize={'18px'} fontWeight={600} w='26%'>
            No of works
          </Text>
        </Box>
        <Box mt='.5rem'>
          {data?.authors?.map((topic) => (
            <Flex justifyContent={'space-between'}>
              <Text
                fontSize='14px'
                w='72%'
                onClick={() => setResearcher(topic[0])}
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
      </Box>
    </Flex>
  );
};

export default TopicInstitutionMetadata;
