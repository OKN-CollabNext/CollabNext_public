import React, { useEffect, useState } from "react";
import { Box, Text, Spinner, Table, Thead, Tbody, Tr, Th, Td } from "@chakra-ui/react";
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js/auto';
import { Line } from 'react-chartjs-2';

Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface MUPData {
  institution_name: string;
  institution_mup_id?: string;
}

interface SATData {
  institution_name: string;
  institution_id: string;
  data: Array<{
    year: number;
    sat: number | null;
  }>;
}

interface EndowmentGivingData {
  institution_name: string;
  institution_id: string;
  data: Array<{
    year: number;
    endowment?: number | null;
    giving?: number | null;
  }>;
}

interface MedicalExpenseData {
  institution_name: string;
  institution_mup_id: string;
  data: Array<{
    year: number;
    expenditure: number | null;
  }>;
}

interface DoctoratePostdocData {
  institution_name: string;
  institution_id: string;
  data: Array<{
    year: number;
    num_doctorates: number | null;
    num_postdocs: number | null;
  }>;
}

interface ResearchData {
  institution_name: string;
  institution_id: string;
  data: Array<{
    year: number;
    num_federal_research: number | null;
    num_nonfederal_research: number | null;
    total_research: number | null;
  }>;
}

interface Props {
  institutionName: string;
}

const MUPDataVisualizer = ({ institutionName }: Props) => {
  const [loading, setLoading] = useState(true);
  const [mupData, setMupData] = useState<MUPData | null>(null);
  const [satData, setSatData] = useState<SATData | null>(null);
  const [endowmentData, setEndowmentData] = useState<EndowmentGivingData | null>(null);
  const [medicalData, setMedicalData] = useState<MedicalExpenseData | null>(null);
  const [doctorateData, setDoctorateData] = useState<DoctoratePostdocData | null>(null);
  const [researchData, setResearchData] = useState<ResearchData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const BASE_URL = process.env.REACT_APP_BASE_URL || "";

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        if (!BASE_URL) {
          throw new Error("BASE_URL is not defined");
        }

        // Fetch MUP Data
        const mupResponse = await fetch(`${BASE_URL}/get-mup-id`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ institution_name: institutionName }),
        });

        if (mupResponse.ok) {
          const mupResult = await mupResponse.json();
          setMupData(mupResult);
        } else {
          setError("Failed to fetch MUP data");
        }

        // Fetch SAT Data
        const satResponse = await fetch(`${BASE_URL}/mup-sat-scores`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ institution_name: institutionName }),
        });

        if (satResponse.ok) {
          const satResult = await satResponse.json();
          setSatData(satResult);
        } else {
          setError("Failed to fetch SAT data");
        }

        // Fetch Endowments/Givings Data
        const endowmentResponse = await fetch(`${BASE_URL}/endowments-and-givings`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ institution_name: institutionName }),
        });

        if (endowmentResponse.ok) {
          const endowmentResult = await endowmentResponse.json();
          setEndowmentData(endowmentResult);
        }

        // Fetch Medical Expenses Data
        const medicalResponse = await fetch(`${BASE_URL}/institution_medical_expenses`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ institution_name: institutionName }),
        });

        if (medicalResponse.ok) {
          const medicalResult = await medicalResponse.json();
          setMedicalData(medicalResult);
        }

        // Fetch Doctorates and Postdocs Data
        const doctorateResponse = await fetch(`${BASE_URL}/institution_doctorates_and_postdocs`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ institution_name: institutionName }),
        });

        if (doctorateResponse.ok) {
          const doctorateResult = await doctorateResponse.json();
          setDoctorateData(doctorateResult);
        }

        // Fetch Research Numbers Data
        const researchResponse = await fetch(`${BASE_URL}/institution_num_of_researches`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ institution_name: institutionName }),
        });

        if (researchResponse.ok) {
          const researchResult = await researchResponse.json();
          setResearchData(researchResult);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred while fetching data");
      } finally {
        setLoading(false);
      }
    };

    if (institutionName) {
      fetchData();
    }
  }, [institutionName, BASE_URL]);

  const renderSATTable = (data: SATData) => {
    const sortedData = data.data
      .sort((a, b) => b.year - a.year); // Sort by year descending

    return (
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Year</Th>
            <Th isNumeric>SAT Score</Th>
          </Tr>
        </Thead>
        <Tbody>
          {sortedData.map((item) => (
            <Tr key={item.year}>
              <Td>{item.year}</Td>
              <Td isNumeric>{item.sat ?? 'No data'}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    );
  };

  const renderEndowmentTable = (data: EndowmentGivingData) => {
    const sortedData = data.data
      .sort((a, b) => b.year - a.year);

    const formatValue = (value: number | null | undefined) => {
      if (value == null) return 'No data';
      return `$${(value / 1000000).toFixed(2)}M`;
    };

    return (
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Year</Th>
            <Th isNumeric>Endowment</Th>
            <Th isNumeric>Giving</Th>
          </Tr>
        </Thead>
        <Tbody>
          {sortedData.map((item) => (
            <Tr key={item.year}>
              <Td>{item.year}</Td>
              <Td isNumeric>{formatValue(item.endowment)}</Td>
              <Td isNumeric>{formatValue(item.giving)}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    );
  };

  const renderMedicalTable = (data: MedicalExpenseData) => {
    const sortedData = data.data
      .sort((a, b) => b.year - a.year);

    const formatValue = (value: number | null) => {
      if (value == null) return 'No data';
      return `$${value.toLocaleString()}`;
    };

    return (
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Year</Th>
            <Th isNumeric>Medical Expenditure</Th>
          </Tr>
        </Thead>
        <Tbody>
          {sortedData.map((item) => (
            <Tr key={item.year}>
              <Td>{item.year}</Td>
              <Td isNumeric>{formatValue(item.expenditure)}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    );
  };

  const renderDoctorateTable = (data: DoctoratePostdocData) => {
    const sortedData = data.data
      .sort((a, b) => b.year - a.year);

    return (
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Year</Th>
            <Th isNumeric>Doctorates</Th>
            <Th isNumeric>Postdocs</Th>
          </Tr>
        </Thead>
        <Tbody>
          {sortedData.map((item) => (
            <Tr key={item.year}>
              <Td>{item.year}</Td>
              <Td isNumeric>{item.num_doctorates ?? 'No data'}</Td>
              <Td isNumeric>{item.num_postdocs ?? 'No data'}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    );
  };

  const renderResearchTable = (data: ResearchData) => {
    const sortedData = data.data
      .sort((a, b) => b.year - a.year);

    const formatValue = (value: number | null) => {
      if (value == null) return 'No data';
      return value.toLocaleString();
    };

    return (
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Year</Th>
            <Th isNumeric>Federal Research</Th>
            <Th isNumeric>Non-Federal Research</Th>
            <Th isNumeric>Total Research</Th>
          </Tr>
        </Thead>
        <Tbody>
          {sortedData.map((item) => (
            <Tr key={item.year}>
              <Td>{item.year}</Td>
              <Td isNumeric>{formatValue(item.num_federal_research)}</Td>
              <Td isNumeric>{formatValue(item.num_nonfederal_research)}</Td>
              <Td isNumeric>{formatValue(item.total_research)}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    );
  };

  if (loading) {
    return <Spinner />;
  }

  return (
    <Box mt={8}>
      <Text fontSize="2xl" fontWeight="bold" mb={4}>
        MUP Institution Data for {institutionName}
      </Text>

      {error && (
        <Box mb={4} p={4} bg="red.50" borderRadius="md" boxShadow="sm">
          <Text color="red.500">
            {error === "No MUP ID found"
              ? `${institutionName} is not part of the MUP dataset`
              : `Error: ${error}`}
          </Text>
        </Box>
      )}

      {mupData?.institution_mup_id && (
        <Box mb={4} p={4} bg="white" borderRadius="md" boxShadow="sm">
          <Text>Institution MUP ID: {mupData.institution_mup_id}</Text>
        </Box>
      )}

      {satData && satData.data && satData.data.length > 0 && (
        <Box mt={4} p={4} bg="white" borderRadius="md" boxShadow="sm">
          <Text fontSize="xl" mb={4}>SAT Score History</Text>
          {renderSATTable(satData)}
        </Box>
      )}

      {endowmentData && endowmentData.data && endowmentData.data.length > 0 && (
        <Box mt={4} p={4} bg="white" borderRadius="md" boxShadow="sm">
          <Text fontSize="xl" mb={4}>Endowment and Giving History</Text>
          {renderEndowmentTable(endowmentData)}
        </Box>
      )}

      {medicalData && medicalData.data && medicalData.data.length > 0 && (
        <Box mt={4} p={4} bg="white" borderRadius="md" boxShadow="sm">
          <Text fontSize="xl" mb={4}>Medical Expenditure History</Text>
          {renderMedicalTable(medicalData)}
        </Box>
      )}

      {doctorateData && doctorateData.data && doctorateData.data.length > 0 && (
        <Box mt={4} p={4} bg="white" borderRadius="md" boxShadow="sm">
          <Text fontSize="xl" mb={4}>Doctorates and Postdocs History</Text>
          {renderDoctorateTable(doctorateData)}
        </Box>
      )}

      {researchData && researchData.data && researchData.data.length > 0 && (
        <Box mt={4} p={4} bg="white" borderRadius="md" boxShadow="sm">
          <Text fontSize="xl" mb={4}>Research Numbers History</Text>
          {renderResearchTable(researchData)}
        </Box>
      )}
    </Box>
  );
};

export default MUPDataVisualizer;