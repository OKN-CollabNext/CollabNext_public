import React from 'react';

import { Box, Button, Flex, Text } from '@chakra-ui/react';

import { ResearchDataInterface } from '../utils/interfaces';

const ResearcherMetadata = ({
  data,
  setTopic,
  currentPage,
  totalPages,
  onPageChange,
}: {
  data: ResearchDataInterface;
  setTopic: React.Dispatch<React.SetStateAction<string>>;
  currentPage: number,
  totalPages: number,
  onPageChange: (page: number) => void;
}) => {
  return (
    <>
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
          <Text fontSize={'18px'} fontWeight={600} w='72%'>
            Topic
          </Text>
          <Text fontSize={'18px'} fontWeight={600} w='26%'>
            No of works
          </Text>
        </Box>
        <Box mt='.5rem'>
          {data?.topics?.map((topic) => (
            <Flex justifyContent={'space-between'}>
              <Text
                fontSize='14px'
                w='72%'
                onClick={() => setTopic(topic[0])}
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

export default ResearcherMetadata;
