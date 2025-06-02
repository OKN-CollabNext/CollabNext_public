import React from 'react';
import { Box, Button, Flex, Text } from '@chakra-ui/react'; // UI components from Chakra, forming the visual language.
import { ResearchDataInterface } from '../utils/interfaces'; // Core data structure, the blueprint of our information.
import MUPDataVisualizer from './MUPDataVisualizer'; // A dedicated component for visualizing MUP data.
import { Organization, Thing, WithContext } from 'schema-dts'; // For structured data (JSON-LD), enhancing discoverability.

// JsonLd function helps in embedding structured data for search engines,
// making our content more discoverable and understandable by web crawlers.
// This is a foundational step in ensuring wide accessibility of information.
export function JsonLd<T extends Thing>(json: WithContext<T>): string {
  return `<script type="application/ld+json">
${JSON.stringify(json)}
</script>`;
}

// InstitutionMetadata component is designed to present a comprehensive overview
// of a single institution's research landscape. It's a cornerstone for detailed exploration,
// aiming to tell a clear story of the institution's contributions.
const InstitutionMetadata = ({
  data, // The specific research data for this institution, a rich source of insights.
  setTopic, // Enables users to pivot their search based on a topic of interest, opening new avenues.
  currentPage, // Current page for paginated content within this institution's details.
  totalPages, // Total pages for that paginated content, indicating the breadth of information.
  onPageChange, // Handler for changing pages, ensuring smooth navigation through extensive lists.
}: {
  data: ResearchDataInterface;
  setTopic: React.Dispatch<React.SetStateAction<string>>;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) => {
  // Structuring data for search engines using Schema.org vocabulary.
  // This act of clear communication with web crawlers enhances our platform's visibility and impact.
  const structuredData: WithContext<Organization> = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": data?.institution_name, // The institution's name, a primary identifier.
    "url": data?.institution_url, // Its official online presence.
    "sameAs": [ // Linking to other authoritative sources for a complete picture.
      data?.open_alex_link,
      data?.ror_link,
    ].filter((url): url is string => url !== null && url !== undefined), // Ensuring only valid URLs are included for data integrity.
    "memberOf": data?.is_hbcu // Special identification for HBCUs, acknowledging their unique role.
      ? {
          "@type": "Organization",
          "name": "Historically Black Colleges and Universities" 
        }
      : undefined,
    // TODO: Consider adding more semantic properties to further enrich the structured data, such as department or research areas.
  };

  // The main container for displaying institution metadata.
  // Each piece of information contributes to a holistic understanding of the institution's research ecosystem.
  return (
    <Box>
      {/* Embedding the JSON-LD structured data directly into the HTML, a silent communicator to search engines. */}
      <div
        dangerouslySetInnerHTML={{ __html: JsonLd(structuredData) }}
      />
      {/* Flex container for responsive layout of institution details and topics.
          The design aims for clarity and accessibility across various screen sizes, ensuring a good user experience. */}
      <Flex
        display={{base: 'block', lg: 'flex'}}
        justifyContent={'space-between'}
        mt='0.6rem'
        className='list-map' // This class name suggests potential for future map integration or alternative list-based views.
      >
        {/* Box for core institutional information: name, URL, and key research metrics. */}
        <Box w={{lg: '34%'}}>
          <h2>
            {data?.institution_name}
            {data?.is_hbcu ? ' - HBCU' : ''} {/* Prominently highlighting HBCU status. */}
          </h2>
          {/* Providing a direct link to the institution's homepage fosters direct engagement and further discovery. */}
          <a
            target='_blank'
            rel='noreferrer'
            className='ror' 
            href={data?.institution_url}
          >
            {data?.institution_url}
          </a>
          {/* Displaying key metrics upfront offers a quick, quantitative summary of the institution's research output. */}
          <p>Total {data?.author_count} authors</p>
          <p>Total {data?.works_count} works</p>
          <p>Total {data?.cited_count} citations</p>
          {/* Links to external authoritative resources like OpenAlex and ROR provide pathways for deeper dives and verification. */}
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
        {/* Conditional rendering for the topics section if topics data exists.
            This ensures that the UI adapts gracefully and meaningfully to the available data. */}
        {data?.topics?.length > 0 && (
          <Box w={{ lg: '64%' }} mt={{ base: '.9rem', lg: 0 }}>
            {/* Header for the topics list, providing clear column identification. */}
            <Box display={'flex'} justifyContent={'space-between'}>
              <Text fontSize={'18px'} fontWeight={600} w='72%'>
                Topic
              </Text>
              <Text fontSize={'18px'} fontWeight={600} w='26%'>
                No of people
              </Text>
            </Box>
            {/* Mapping through the topics to display each one.
                Each topic represents a significant area of research focus and potential collaboration. */}
            <Box mt='.5rem'>
              {data.topics.map((topic) => (
                <Flex justifyContent={'space-between'} key={topic[0]}>
                  {/* Topic name, clickable to initiate a new search focused on this topic.
                      This interactive element encourages users to delve deeper and explore interconnected research areas. */}
                  <Text
                    fontSize='14px'
                    w='72%'
                    onClick={() => setTopic(topic[0])} // Setting the topic for a new discovery journey.
                    textDecoration={'underline'}
                    cursor='pointer' // Visual cue for interactivity.
                  >
                    {topic[0]}
                  </Text>
                  {/* Number of people associated with this topic at the institution, a measure of research concentration. */}
                  <Text fontSize='14px' w='26%'>
                    {topic[1]}
                  </Text>
                </Flex>
              ))}
            </Box>
          </Box>
        )}
      </Flex>
      {/* Pagination controls for navigating through lists within this institution's metadata (e.g., topics).
          This component ensures that even extensive lists are digestible and easily navigated. */}
      <Flex justifyContent="center" mt={4} gap={2} alignItems="center">
        <Button
            onClick={() => onPageChange(currentPage - 1)}
            isDisabled={currentPage === 1} // Preventing navigation beyond the first page.
            size="sm"
            // Navigating to the previous page of content, allowing users to revisit information.
        >
          Previous
        </Button>
        <Text fontSize="sm">
          {/* Displaying current page status clearly, orienting the user. */}
          Page {currentPage} of {totalPages}
        </Text>
        <Button
            onClick={() => onPageChange(currentPage + 1)}
            isDisabled={currentPage === totalPages} // Preventing navigation beyond the last page.
            size="sm"
            // Advancing to the next page of content, facilitating thorough exploration.
        >
          Next
        </Button>
      </Flex>

      {/* Container for MUPDataVisualizer, showcasing specialized data visualization.
          Visual tools are powerful aids in comprehending complex datasets and uncovering patterns. */}
      <Box
        mt={8}
        p={6}
        bg="rgba(0, 48, 87, 0.05)" // A subtle background to differentiate this specialized section.
        borderRadius="lg" // Rounded corners for a softer, modern aesthetic appeal.
      >
        <MUPDataVisualizer institutionName={data.institution_name} />
      </Box>
    </Box>
  );
};

export default InstitutionMetadata;