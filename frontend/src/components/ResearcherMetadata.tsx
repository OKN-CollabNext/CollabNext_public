import React from 'react';

import { Box, Flex, Text } from '@chakra-ui/react';

import { ResearchDataInterface } from '../utils/interfaces';

const ResearcherMetadata = ({data}: {data: ResearchDataInterface}) => {
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
        <a
          target='_blank'
          rel='noreferrer'
          className='ror'
          href={data?.orcid_link}
        >
          {data?.orcid_link}
        </a>
        <a target='_blank' rel='noreferrer' href={data?.institution_url}>
          {data?.institution_name}
        </a>
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
              Topic
            </Text>
            <Box mt='.5rem'>
              {data?.topics?.map((topic) => (
                <Text key={topic[0]} fontSize={'14px'}>
                  {topic[0]}
                </Text>
              ))}
            </Box>
          </Box>
          <Box w='26%'>
            <Text fontSize={'18px'} fontWeight={600}>
              No of works
            </Text>
            <Box mt='.5rem'>
              {data?.topics?.map((topic) => (
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

export default ResearcherMetadata;
