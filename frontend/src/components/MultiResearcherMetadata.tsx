import React, { useState } from 'react';
import ResearcherMetadata from './ResearcherMetadata';
import { ResearchDataInterface } from '../utils/interfaces';
import { Box, Button, Flex, Text } from '@chakra-ui/react';
import { Organization, Thing, WithContext } from 'schema-dts';

const MultiResearcherMetadata = ({
  researchersMetadata,
  setTopic,
  currentPage,
  totalPages,
  onPageChange,
}: {
  researchersMetadata?: { [key: string]: ResearchDataInterface };
  setTopic: React.Dispatch<React.SetStateAction<string>>;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!researchersMetadata) return null;
  const researcherNames = Object.keys(researchersMetadata);
  const currentResearcher = researcherNames[currentIndex];
  const currentData = researchersMetadata[currentResearcher];

  const handleNext = () => {
    setCurrentIndex((prev) => Math.min(prev + 1, researcherNames.length - 1));
  };

  const handlePrevious = () => {
    setCurrentIndex((prev) => Math.max(prev - 1, 0));
  };
  return (
    <Box>
      {researcherNames.length > 1 && (
        <Flex justifyContent="center" mt={4} gap={2}>
          <Button
            onClick={handlePrevious}
            isDisabled={currentIndex === 0}
            size="sm"
          >
            Previous Researcher
          </Button>
          <Button
            onClick={handleNext}
            isDisabled={currentIndex === researcherNames.length - 1}
            size="sm"
          >
            Next Researcher
          </Button>
        </Flex>
      )}
      <ResearcherMetadata
        data={currentData}
        setTopic={setTopic}
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={onPageChange}
      />
    </Box>
  );
};

export default MultiResearcherMetadata;
