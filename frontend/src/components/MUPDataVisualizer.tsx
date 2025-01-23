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

  const createChartData = (label: string, data: Array<{year: number, [key: string]: any}>, valueKeys: string[], valueLabels: string[]) => {
    const sortedData = [...data].sort((a, b) => a.year - b.year);
    return {
      labels: sortedData.map(item => item.year),
      datasets: valueKeys.map((key, index) => ({
        label: valueLabels[index],
        data: sortedData.map(item => item[key]),
        borderColor: [
          '#003057',  // Blue
          '#DD6B20',  // Orange
          '#38A169',  // Green
          '#805AD5',  // Purple
        ][index % 4],
        tension: 0.1,
        fill: false,
      }))
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      }
    },
  };

  const renderSATChart = (data: SATData) => {
    const chartData = createChartData(
      'SAT Scores',
      data.data,
      ['sat'],
      ['SAT Score']
    );

    return (
      <Line data={chartData} options={chartOptions} />
    );
  };

  const renderEndowmentChart = (data: EndowmentGivingData) => {
    const chartData = createChartData(
      'Endowment and Giving',
      data.data,
      ['endowment', 'giving'],
      ['Endowment', 'Giving']
    );

    return (
      <Line data={chartData} options={{
        ...chartOptions,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value: number) => `$${(value / 1000).toFixed(0)}K`
            }
          }
        }
      }} />
    );
  };

  const renderMedicalChart = (data: MedicalExpenseData) => {
    const chartData = createChartData(
      'Medical Expenditure',
      data.data,
      ['expenditure'],
      ['Medical Expenditure']
    );

    return (
      <Line data={chartData} options={{
        ...chartOptions,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value: number) => `$${(value / 1000).toFixed(0)}K`
            }
          }
        }
      }} />
    );
  };

  const renderDoctorateChart = (data: DoctoratePostdocData) => {
    const chartData = createChartData(
      'Doctorates and Postdocs',
      data.data,
      ['num_doctorates', 'num_postdocs'],
      ['Doctorates', 'Postdocs']
    );

    return (
      <Line data={chartData} options={chartOptions} />
    );
  };

  const renderResearchChart = (data: ResearchData) => {
    const chartData = createChartData(
      'Research Numbers',
      data.data,
      ['num_federal_research', 'num_nonfederal_research', 'total_research'],
      ['Federal Research', 'Non-Federal Research', 'Total Research']
    );

    return (
      <Line data={chartData} options={{
        ...chartOptions,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value: number) => value.toLocaleString()
            }
          }
        }
      }} />
    );
  };

  if (loading) {
    return <Spinner />;
  }

  return (
    <Box mt={8} maxWidth="1200px" mx="auto" px={4}>
      <Text fontSize="2xl" fontWeight="bold" mb={6} textAlign="center">
        MUP Institution Data for {institutionName}
      </Text>

      {error && (
        <Box mb={6} p={4} bg="red.50" borderRadius="lg" boxShadow="md">
          <Text color="red.500" textAlign="center">
            {error === "No MUP ID found"
              ? `${institutionName} is not part of the MUP dataset`
              : `Error: ${error}`}
          </Text>
        </Box>
      )}

      {mupData?.institution_mup_id && (
        <Box mb={6} p={4} bg="white" borderRadius="lg" boxShadow="md" textAlign="center">
          <Text>Institution MUP ID: {mupData.institution_mup_id}</Text>
        </Box>
      )}

      <Box 
        display="grid" 
        gridTemplateColumns={{base: "1fr", lg: "repeat(2, 1fr)"}} 
        gap={6}
      >
        {satData && satData.data && satData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="lg" 
            boxShadow="md" 
            transition="transform 0.2s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
          >
            <Text fontSize="xl" mb={4} textAlign="center">SAT Score History</Text>
            {renderSATChart(satData)}
          </Box>
        )}

        {endowmentData && endowmentData.data && endowmentData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="lg" 
            boxShadow="md"
            transition="transform 0.2s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
          >
            <Text fontSize="xl" mb={4} textAlign="center">Endowment and Giving History</Text>
            {renderEndowmentChart(endowmentData)}
          </Box>
        )}

        {medicalData && medicalData.data && medicalData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="lg" 
            boxShadow="md"
            transition="transform 0.2s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
          >
            <Text fontSize="xl" mb={4} textAlign="center">Medical Expenditure History</Text>
            {renderMedicalChart(medicalData)}
          </Box>
        )}

        {doctorateData && doctorateData.data && doctorateData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="lg" 
            boxShadow="md"
            transition="transform 0.2s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
          >
            <Text fontSize="xl" mb={4} textAlign="center">Doctorates and Postdocs History</Text>
            {renderDoctorateChart(doctorateData)}
          </Box>
        )}

        {researchData && researchData.data && researchData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="lg" 
            boxShadow="md"
            gridColumn={{base: "1", lg: "1 / -1"}}
            transition="transform 0.2s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
          >
            <Text fontSize="xl" mb={4} textAlign="center">Research Numbers History</Text>
            {renderResearchChart(researchData)}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default MUPDataVisualizer;