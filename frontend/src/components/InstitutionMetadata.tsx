import React from 'react';

import { Box, Flex, Text } from '@chakra-ui/react';

import { ResearchDataInterface, InstitutionDesignations } from '../utils/interfaces';

import { Organization, Thing, WithContext } from 'schema-dts';

export function JsonLd<T extends Thing>(json: WithContext<T>): string {
  return `<script type="application/ld+json">
${JSON.stringify(json)}
</script>`;
}

const InstitutionMetadata = ({
  data,
  setTopic,
  institutionDesignations,
}: {
  data: ResearchDataInterface;
  institutionDesignations: InstitutionDesignations;
  setTopic: React.Dispatch<React.SetStateAction<string>>;
}) => {
  const memberOf = [];
  if (data?.is_hbcu) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "Historically Black Colleges and Universities"
    });
  }
  if (institutionDesignations?.is_r1) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "R1 Doctoral Universities"
    });
  }
  if (institutionDesignations?.is_r2) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "R2 Doctoral Universities"
    });
  }
  if (institutionDesignations?.is_tcu) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "Tribal Colleges and Universities"
    });
  }
  if (institutionDesignations?.is_non_msi) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "Non Minority Serving Institutions"
    });
  }
  if (institutionDesignations?.is_aanapisi) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "Asian American Native American Pacific Islander Serving Institutions"
    });
  }
  if (institutionDesignations?.is_pbi) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "Predominantly Black Institutions"
    });
  }
  if (institutionDesignations?.is_hsi) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "Hispanic Serving Institutions"
    });
  }
  if (institutionDesignations?.is_nasnti) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "Native American-Serving Non-Tribal Institutions"
    });
  }
  if (institutionDesignations?.is_aanh) {
    memberOf.push({
      "@type": "Organization" as const,
      "name": "Alaska Native and Native Hawaiian Serving Institutions"
    });
  }

  const structuredData: WithContext<Organization> = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": data?.institution_name,
    "url": data?.institution_url,
    "sameAs": [
      data?.open_alex_link,
      data?.ror_link,
    ].filter((url): url is string => url !== null && url !== undefined),
    ...(memberOf.length > 0 && { memberOf })
    // TODO: Add more properties
  };
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
          <button className='topButton'>List Map</button>
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
    </Box>
  );
};

export default InstitutionMetadata;
