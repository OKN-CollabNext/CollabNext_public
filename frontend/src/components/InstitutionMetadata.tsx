import React, { useState, useEffect } from 'react';

import { Box, Button, Flex, Text, Input } from '@chakra-ui/react';

import { ResearchDataInterface } from '../utils/interfaces';
import MUPDataVisualizer from './MUPDataVisualizer';
import { Organization, Thing, WithContext } from 'schema-dts';

export function JsonLd<T extends Thing>(json: WithContext<T>): string {
  return `<script type="application/ld+json">
${JSON.stringify(json)}
</script>`;
}
interface InstitutionMetadataProps {
  data: ResearchDataInterface;
  setTopic: React.Dispatch<React.SetStateAction<string>>;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  sortMode: 'count' | 'alpha';
  setSortMode: React.Dispatch<React.SetStateAction<'count' | 'alpha'>>;
}

const InstitutionMetadata: React.FC<InstitutionMetadataProps> = ({
  data,
  setTopic,
  currentPage,
  totalPages,
  onPageChange,
  sortMode,
  setSortMode,
}: {
  data: ResearchDataInterface;
  setTopic: React.Dispatch<React.SetStateAction<string>>;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) => {
  const [inputPage, setInputPage] = useState<number>(currentPage);
  useEffect(() => {
    setInputPage(currentPage);
  }, [currentPage]);
  const structuredData: WithContext<Organization> = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": data?.institution_name,
    "url": data?.institution_url,
    "sameAs": [
      data?.open_alex_link,
      data?.ror_link,
    ].filter((url): url is string => url !== null && url !== undefined),
    "memberOf": data?.is_hbcu
      ? {
          "@type": "Organization",
          "name": "Historically Black Colleges and Universities"
        }
      : undefined,
    // TODO: Add more properties
  };
  const sortedTopics = data?.topics
    ?.slice()
    .sort(([aName, aCount], [bName, bCount]) => {
      if (sortMode === 'count') {
        return bCount - aCount || aName.localeCompare(bName);
      }
      return aName.localeCompare(bName);
    });
  return (
    <Box>
      <div
        dangerouslySetInnerHTML={{ __html: JsonLd(structuredData) }}
      />
      <Flex
        display={{base: 'block', lg: 'flex'}}
        justifyContent={'space-between'}
        mt='0.6rem'
        className='list-map'
      >
        <Box w={{lg: '34%'}}>
          <h2>
            {data?.institution_name}
            {data?.is_hbcu ? ' - HBCU' : ''}
          </h2>
          <a
            target='_blank'
            rel='noreferrer'
            className='ror'
            href={data?.institution_url}
          >
            {data?.institution_url}
          </a>
          <p>Total {data?.author_count} authors</p>
          <p>Total {data?.works_count} works</p>
          <p>Total {data?.cited_count} citations</p>
          <a target='_blank' rel='noreferrer' href={data?.open_alex_link}>
            View on OpenAlex
          </a>
          <a
            target='_blank'
            rel='noreferrer'
            className='ror'
            href={data?.ror_link}
          >
            RORID -{' '}
            {data?.ror_link?.split('/')[data?.ror_link?.split('/')?.length - 1]}
          </a>
        </Box>
        <Box w={{lg: '64%'}} mt={{base: '.9rem', lg: 0}}>
          <Box display={'flex'} justifyContent={'space-between'}>
            <Text fontSize={'18px'} fontWeight={600} w='72%'>
              Topic
            </Text>
            <Text fontSize={'18px'} fontWeight={600} w='26%'>
              No of people
            </Text>
          </Box>
          <Flex mt='.5rem' mb='.5rem' gap={2}>
            <Button
              size='xs'
              onClick={() => setSortMode('alpha')}
              bgGradient={
                sortMode === 'alpha'
                  ? 'linear(to-b, #053257, #7e7e7e)'
                  : undefined
              }
              color={sortMode === 'alpha' ? 'white' : undefined}
              _hover={
                sortMode === 'alpha'
                  ? { bgGradient: 'linear(to-b, #053257, #7e7e7e)' }
                  : undefined
              }
            >
              A-Z
            </Button>
            <Button
              size='xs'
              onClick={() => setSortMode('count')}
              bgGradient={
                sortMode === 'count'
                  ? 'linear(to-b, #053257, #7e7e7e)'
                  : undefined
              }
              color={sortMode === 'count' ? 'white' : undefined}
              _hover={
                sortMode === 'count'
                  ? { bgGradient: 'linear(to-b, #053257, #7e7e7e)' }
                  : undefined
              }
            >
              No of people
            </Button>
          </Flex>
          <Box>
            {sortedTopics?.map(([topicName, count]) => (
              <Flex key={topicName} justifyContent='space-between'>
                <Text
                  fontSize='14px'
                  w='72%'
                  onClick={() => setTopic(topicName)}
                  textDecoration='underline'
                  cursor='pointer'
                >
                  {topicName}
                </Text>
                <Text fontSize='14px' w='26%'>
                  {count}
                </Text>
              </Flex>
            ))}
          </Box>
        </Box>
      </Flex>
      <Flex justifyContent='center' mt={4} gap={2} alignItems='center'>
        <Button onClick={() => onPageChange(currentPage - 1)} isDisabled={currentPage === 1} size='sm'>Previous</Button>
        <Input
          type='number'
          min={1}
          max={totalPages}
          value={inputPage === 0 ? '' : inputPage}
          onChange={e => setInputPage(Number(e.target.value))}
          onBlur={() => {
            const p = Math.min(totalPages, Math.max(1, inputPage));
            onPageChange(p);
          }}
          onKeyDown={e => {
            if (e.key === 'Enter') {
              const p = Math.min(totalPages, Math.max(1, inputPage));
              onPageChange(p);
            }
          }}
          size='sm'
          width='4rem'
          textAlign='center'
        />
        <Text fontSize='sm'>/ {totalPages}</Text>
        <Button onClick={() => onPageChange(currentPage + 1)} isDisabled={currentPage === totalPages} size='sm'>Next</Button>
      </Flex>

      <Box 
        mt={8} 
        p={6} 
        bg="rgba(0, 48, 87, 0.05)" 
        borderRadius="lg"
      >
        <MUPDataVisualizer institutionName={data.institution_name} />
      </Box>
    </Box>
  );
};

export default InstitutionMetadata;