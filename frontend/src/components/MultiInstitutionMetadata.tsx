import React, { useState } from 'react';
import InstitutionMetadata from './InstitutionMetadata'; // Component for displaying individual institution details.
import { ResearchDataInterface } from '../utils/interfaces'; // Core data structure.
import { Box, Button, Flex } from '@chakra-ui/react'; // Chakra UI components for layout and interaction.

// MultiInstitutionMetadata provides a way to navigate through the rich data
// of several institutions when a search yields such diverse results. It's about
// presenting complex information in an accessible, step-by-step manner.
const MultiInstitutionMetadata = ({
  institutionsMetadata, // The collection of metadata for multiple institutions.
  setTopic, // Callback to set the topic, enabling further exploration.
}: {
  institutionsMetadata?: { [key: string]: ResearchDataInterface };
  setTopic: React.Dispatch<React.SetStateAction<string>>;
}) => {
  // The currentIndex helps us keep track of which institution's data is currently being viewed.
  // This state is fundamental to the component's navigation logic.
  const [currentIndex, setCurrentIndex] = useState(0);

  // If there's no metadata for institutions, we render nothing.
  // This ensures the component gracefully handles empty states.
  if (!institutionsMetadata || Object.keys(institutionsMetadata).length === 0) {
    return null;
  }

  // Extracting the names of the institutions to serve as keys for navigation.
  // This array forms the backbone of our institution-switching capability.
  const institutionNames = Object.keys(institutionsMetadata);
  const currentInstitutionName = institutionNames[currentIndex];
  const currentData = institutionsMetadata[currentInstitutionName];

  // handleNext advances to the subsequent institution in the list.
  // It's a simple yet powerful way to explore the breadth of results.
  const handleNext = () => {
    setCurrentIndex((prevIndex) => Math.min(prevIndex + 1, institutionNames.length - 1));
  };

  // handlePrevious allows the user to return to the prior institution's data.
  // Navigation should be intuitive and allow for easy backtracking.
  const handlePrevious = () => {
    setCurrentIndex((prevIndex) => Math.max(prevIndex - 1, 0));
  };

  // If data for the current institution isn't available (e.g. bad key), render null.
  // This is a safeguard for data integrity during display.
  if (!currentData) return null;

  return (
    <Box>
      {/* Navigation buttons are only shown if there's more than one institution to display.
          This enhances clarity and avoids unnecessary UI elements, ensuring a focused user experience. */}
      {institutionNames.length > 1 && (
        <Flex justifyContent="center" alignItems="center" mt={4} gap={2}>
          <Button
            onClick={handlePrevious}
            isDisabled={currentIndex === 0}
            size="sm"
            // This button empowers users to step back and revisit previous findings, fostering a sense of control.
          >
            Previous Institution
          </Button>
          <Box as="span" mx={2} fontSize="sm">
            {/* Displaying the current position helps orient the user within the set of results, making navigation transparent. */}
            Viewing {currentIndex + 1} of {institutionNames.length}
          </Box>
          <Button
            onClick={handleNext}
            isDisabled={currentIndex === institutionNames.length - 1}
            size="sm"
            // The 'Next Institution' button encourages progressive discovery through the dataset.
          >
            Next Institution
          </Button>
        </Flex>
      )}
      {/* The InstitutionMetadata component is reused here to display the details
          of the currently selected institution. This promotes modularity and consistency in our design. */}
      <InstitutionMetadata
        data={currentData}
        setTopic={setTopic}
        // Pagination within InstitutionMetadata is for its own internal lists (topics, authors).
        // Defaults are appropriate here as this component manages inter-institution navigation.
        currentPage={1} 
        totalPages={1}  
        onPageChange={() => {}} 
      />
    </Box>
  );
};

export default MultiInstitutionMetadata;