import React, { useEffect, useState } from "react";
import { Box, Text, Spinner, Table, Thead, Tbody, Tr, Th, Td, Select, HStack, Button, Tooltip as ChakraTooltip } from "@chakra-ui/react";
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
import zoomPlugin from 'chartjs-plugin-zoom';
import { FiZoomOut } from 'react-icons/fi';

Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  zoomPlugin
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

interface YearData {
  year: number;
  [key: string]: any;
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
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
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
          '#003057',  // Primary blue
          '#DD6B20',  // Orange
          '#38A169',  // Green
          '#805AD5',  // Purple
        ][index % 4],
        tension: 0.1,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6,
      }))
    };
  };

  const getAvailableYears = (): number[] => {
    const yearsSet = new Set<number>();
    
    [satData?.data, endowmentData?.data, medicalData?.data, doctorateData?.data, researchData?.data]
      .filter(Boolean)
      .forEach(dataset => {
        dataset?.forEach((item: YearData) => yearsSet.add(item.year));
      });

    return Array.from(yearsSet).sort((a, b) => b - a);
  };

  const resetZoom = () => {
    const charts = document.querySelectorAll('canvas');
    charts.forEach(canvas => {
      const chart = Chart.getChart(canvas);
      chart?.resetZoom();
    });
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          padding: 20,
          font: {
            size: 12,
            family: "'Inter', sans-serif",
          },
          usePointStyle: true,
          pointStyle: 'circle',
        },
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#1A202C',
        bodyColor: '#4A5568',
        borderColor: '#E2E8F0',
        borderWidth: 1,
        padding: 12,
        bodyFont: {
          size: 13,
          family: "'Inter', sans-serif",
        },
        titleFont: {
          size: 14,
          family: "'Inter', sans-serif",
          weight: 'bold',
        },
        callbacks: {
          title: (tooltipItems: any) => {
            return `Year: ${tooltipItems[0].parsed.x}`;
          },
        }
      },
      zoom: {
        pan: {
          enabled: true,
          mode: 'x',
        },
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true,
          },
          mode: 'x',
        },
      },
    },
    scales: {
      x: {
        type: 'linear',
        display: true,
        title: {
          display: true,
          text: 'Year',
          font: {
            size: 14,
            weight: 'bold',
          },
        },
        ticks: {
          stepSize: 1,
          font: {
            family: "'Inter', sans-serif",
          },
          callback: function(value: number) {
            return Math.floor(value);
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          font: {
            family: "'Inter', sans-serif",
          },
        },
      },
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
      <div style={{ height: '100%', width: '100%', position: 'relative' }}>
        <Line data={chartData} options={chartOptions} />
      </div>
    );
  };

  const renderEndowmentChart = (data: EndowmentGivingData) => {
    const chartData = createChartData(
      'Endowment and Giving',
      data.data,
      ['endowment', 'giving'],
      ['Endowment', 'Giving']
    );

    const endowmentOptions = {
      ...chartOptions,
      scales: {
        ...chartOptions.scales,
        y: {
          ...chartOptions.scales.y,
          ticks: {
            ...chartOptions.scales.y.ticks,
            callback: (value: number) => `$${(value / 1000).toFixed(0)}K`,
          },
        },
      },
    };

    return (
      <div style={{ height: '100%', width: '100%', position: 'relative' }}>
        <Line data={chartData} options={endowmentOptions} />
      </div>
    );
  };

  const renderMedicalChart = (data: MedicalExpenseData) => {
    const chartData = createChartData(
      'Medical Expenditure',
      data.data,
      ['expenditure'],
      ['Medical Expenditure']
    );

    const medicalOptions = {
      ...chartOptions,
      scales: {
        x: {
          type: 'category',
          display: true,
          title: {
            display: true,
            text: 'Year',
            font: {
              size: 14,
              weight: 'bold',
            },
          },
          ticks: {
            font: {
              family: "'Inter', sans-serif",
            },
          },
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
          },
          ticks: {
            callback: (value: number) => `$${(value / 1000).toFixed(1)}K`,
          },
        },
      },
    };

    return (
      <div style={{ height: '100%', width: '100%', position: 'relative' }}>
        <Line data={chartData} options={medicalOptions} />
      </div>
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

    const researchOptions = {
      ...chartOptions,
      scales: {
        x: {
          type: 'category',
          display: true,
          title: {
            display: true,
            text: 'Year',
            font: {
              size: 14,
              weight: 'bold',
            },
          },
          ticks: {
            font: {
              family: "'Inter', sans-serif",
            },
          },
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
          },
          ticks: {
            callback: (value: number) => `$${(value / 1000).toFixed(1)}K`,
          },
        },
      },
      plugins: {
        ...chartOptions.plugins,
        tooltip: {
          ...chartOptions.plugins.tooltip,
          callbacks: {
            label: function(context: any) {
              const value = context.raw;
              if (typeof value === 'number') {
                return `${context.dataset.label}: $${(value / 1000).toFixed(1)}K`;
              }
              return context.dataset.label;
            }
          }
        }
      }
    };

    return (
      <div style={{ height: '100%', width: '100%', position: 'relative' }}>
        <Line data={chartData} options={researchOptions} />
      </div>
    );
  };

  const renderYearSummary = (year: number) => {
    if (!year) return null;

    return (
      <Box 
        mt={4} 
        p={6} 
        bg="blue.50" 
        borderRadius="xl" 
        boxShadow="sm"
        transition="all 0.2s"
        _hover={{ transform: 'translateY(-2px)', boxShadow: 'md' }}
      >
        <Text fontSize="xl" fontWeight="bold" mb={4} color="blue.800">
          Data Summary for {year}
        </Text>
        <Box 
          display="grid" 
          gridTemplateColumns={{base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(3, 1fr)"}} 
          gap={6}
        >
          {satData?.data.find(d => d.year === year) && (
            <ChakraTooltip label="Average SAT score" placement="top">
              <Box 
                p={5} 
                bg="white" 
                borderRadius="lg"
                boxShadow="sm"
                transition="all 0.2s"
                _hover={{ transform: 'translateY(-2px)', boxShadow: 'md' }}
              >
                <Text fontWeight="semibold" color="gray.600" mb={2}>SAT Score</Text>
                <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                  {satData.data.find(d => d.year === year)?.sat?.toLocaleString() || 'N/A'}
                </Text>
              </Box>
            </ChakraTooltip>
          )}
          
          {endowmentData?.data.find(d => d.year === year) && (
            <ChakraTooltip label="Endowment amount" placement="top">
              <Box 
                p={5} 
                bg="white" 
                borderRadius="lg"
                boxShadow="sm"
                transition="all 0.2s"
                _hover={{ transform: 'translateY(-2px)', boxShadow: 'md' }}
              >
                <Text fontWeight="semibold" color="gray.600" mb={2}>Endowment</Text>
                <Text fontSize="2xl" fontWeight="bold" color="green.600">
                  ${(endowmentData.data.find(d => d.year === year)?.endowment || 0).toLocaleString()}K
                </Text>
              </Box>
            </ChakraTooltip>
          )}

          {doctorateData?.data.find(d => d.year === year) && (
            <ChakraTooltip label="Number of doctorates and postdocs" placement="top">
              <Box 
                p={5} 
                bg="white" 
                borderRadius="lg"
                boxShadow="sm"
                transition="all 0.2s"
                _hover={{ transform: 'translateY(-2px)', boxShadow: 'md' }}
              >
                <Text fontWeight="semibold" color="gray.600" mb={2}>Doctorates/Postdocs</Text>
                <Text fontSize="2xl" fontWeight="bold" color="purple.600">
                  {doctorateData.data.find(d => d.year === year)?.num_doctorates || 0} / {doctorateData.data.find(d => d.year === year)?.num_postdocs || 0}
                </Text>
              </Box>
            </ChakraTooltip>
          )}
        </Box>
      </Box>
    );
  };

  if (loading) {
    return <Spinner />;
  }

  return (
    <Box mt={8} maxWidth="1200px" mx="auto" px={4}>
      <Box 
        mb={8} 
        textAlign="center"
        animation="fadeIn 0.5s ease-in"
      >
        <Text 
          fontSize={{base: "2xl", md: "3xl"}} 
          fontWeight="bold" 
          color="gray.800"
          mb={2}
        >
          {institutionName}
        </Text>
        <Text fontSize="lg" color="gray.600">
          MUP Institution Data Analysis
        </Text>
      </Box>

      {error && (
        <Box 
          mb={6} 
          p={5} 
          bg="red.50" 
          borderRadius="xl" 
          boxShadow="sm"
          border="1px solid"
          borderColor="red.100"
        >
          <Text color="red.600" textAlign="center" fontSize="lg">
            {error === "No MUP ID found"
              ? `${institutionName} is not part of the MUP dataset`
              : `Error: ${error}`}
          </Text>
        </Box>
      )}

      <HStack 
        spacing={4} 
        mb={6} 
        justifyContent="center"
        bg="white"
        p={4}
        borderRadius="lg"
        boxShadow="sm"
      >
        <Select 
          placeholder="Select year for summary"
          value={selectedYear || ''}
          onChange={(e) => setSelectedYear(Number(e.target.value))}
          maxW="250px"
          size="lg"
          borderColor="gray.300"
          _hover={{ borderColor: "gray.400" }}
        >
          {getAvailableYears().map(year => (
            <option key={year} value={year}>{year}</option>
          ))}
        </Select>
        <Button 
          colorScheme="blue" 
          variant="outline" 
          onClick={resetZoom}
          size="lg"
          leftIcon={<FiZoomOut />}
        >
          Reset Zoom
        </Button>
      </HStack>

      {selectedYear && renderYearSummary(selectedYear)}

      <Box 
        display="grid" 
        gridTemplateColumns={{base: "1fr", lg: "repeat(2, 1fr)"}} 
        gap={8}
        mt={8}
      >
        {satData && satData.data && satData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="xl" 
            boxShadow="sm"
            transition="all 0.3s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
            height="400px"
            position="relative"
            overflow="hidden"
          >
            <Text 
              fontSize="xl" 
              fontWeight="semibold" 
              mb={4} 
              textAlign="center"
              color="gray.700"
            >
              SAT Score History
            </Text>
            {renderSATChart(satData)}
          </Box>
        )}

        {endowmentData && endowmentData.data && endowmentData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="xl" 
            boxShadow="sm"
            transition="all 0.3s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
            height="400px"
            position="relative"
            overflow="hidden"
          >
            <Text 
              fontSize="xl" 
              fontWeight="semibold" 
              mb={4} 
              textAlign="center"
              color="gray.700"
            >
              Endowment and Giving History
            </Text>
            {renderEndowmentChart(endowmentData)}
          </Box>
        )}

        {medicalData && medicalData.data && medicalData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="xl" 
            boxShadow="sm"
            transition="all 0.3s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
            height="400px"
            position="relative"
            overflow="hidden"
          >
            <Text 
              fontSize="xl" 
              fontWeight="semibold" 
              mb={4} 
              textAlign="center"
              color="gray.700"
            >
              Medical Expenditure History
            </Text>
            {renderMedicalChart(medicalData)}
          </Box>
        )}

        {doctorateData && doctorateData.data && doctorateData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="xl" 
            boxShadow="sm"
            transition="all 0.3s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
            height="400px"
            position="relative"
            overflow="hidden"
          >
            <Text 
              fontSize="xl" 
              fontWeight="semibold" 
              mb={4} 
              textAlign="center"
              color="gray.700"
            >
              Doctorates and Postdocs History
            </Text>
            {renderDoctorateChart(doctorateData)}
          </Box>
        )}

        {researchData && researchData.data && researchData.data.length > 0 && (
          <Box 
            p={6} 
            bg="white" 
            borderRadius="xl" 
            boxShadow="sm"
            gridColumn={{base: "1", lg: "1 / -1"}}
            transition="all 0.3s"
            _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
            height="400px"
            position="relative"
            overflow="hidden"
          >
            <Text 
              fontSize="xl" 
              fontWeight="semibold" 
              mb={4} 
              textAlign="center"
              color="gray.700"
            >
              Research Numbers History
            </Text>
            {renderResearchChart(researchData)}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default MUPDataVisualizer;