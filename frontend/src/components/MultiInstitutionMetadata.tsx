import React, { useState } from 'react';
import InstitutionMetadata from './InstitutionMetadata';
import { ResearchDataInterface } from '../utils/interfaces';
import { Box, Button, Flex, Text } from '@chakra-ui/react';
import { Organization, Thing, WithContext } from 'schema-dts';

export function JsonLd<T extends Thing>(json: WithContext<T>): string {
  return `<script type="application/ld+json">
${JSON.stringify(json)}
</script>`;
}

const MultiInstitutionMetadata = ({
  institutionsMetadata,
  setTopic,
  currentPage,
  totalPages,
  onPageChange,
}: {
  institutionsMetadata?: { [key: string]: ResearchDataInterface };
  setTopic: React.Dispatch<React.SetStateAction<string>>;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!institutionsMetadata) return null;

  const institutionNames = Object.keys(institutionsMetadata);
  const currentInstitution = institutionNames[currentIndex];
  const currentData = institutionsMetadata[currentInstitution];

  const handleNext = () => {
    setCurrentIndex((prev) => Math.min(prev + 1, institutionNames.length - 1));
  };

  const handlePrevious = () => {
    setCurrentIndex((prev) => Math.max(prev - 1, 0));
  };
  return (
    <Box>
      {institutionNames.length > 1 && (
        <Flex justifyContent="center" mt={4} gap={2}>
          <Button
            onClick={handlePrevious}
            isDisabled={currentIndex === 0}
            size="sm"
          >
            Previous Institution
          </Button>
          <Button
            onClick={handleNext}
            isDisabled={currentIndex === institutionNames.length - 1}
            size="sm"
          >
            Next Institution
          </Button>
        </Flex>
      )}
      <InstitutionMetadata
        data={currentData}
        setTopic={setTopic}
        currentPage={1}
        totalPages={1}
        onPageChange={() => {}}
      />
    </Box>
  );
};

export default MultiInstitutionMetadata;
