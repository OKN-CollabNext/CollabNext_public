import React, { useEffect, useState } from "react";
import { Box, Text, Spinner, Table, Thead, Tbody, Tr, Th, Td, Select, HStack, Button, Tooltip as ChakraTooltip, Flex } from "@chakra-ui/react";
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
import { FiZoomOut, FiInfo } from 'react-icons/fi';

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

interface FacultyAwardsData {
  institution_name: string;
  institution_id: string;
  data: Array<{
    nae: number | null;
    nam: number | null;
    nas: number | null;
    num_fac_awards: number | null;
  }>;
}

interface YearData {
  year: number;
  [key: string]: any;
}

interface RAndDData {
  institution_name: string;
  institution_id: string;
  data: Array<{
    category: string;
    federal: number | null;
    percent_federal: number | null;
    total: number | null;
    percent_total: number | null;
  }>;
}

interface Props {
  institutionName: string;
}

const ChartHeader = ({ title, description }: { title: string, description: string }) => (
  <Flex 
    fontSize="xl" 
    fontWeight="semibold" 
    mb={4} 
    textAlign="center"
    color="gray.700"
    justifyContent="center"
    alignItems="center"
    gap={2}
  >
    {title}
    <ChakraTooltip 
      label={description} 
      placement="top" 
      hasArrow
      bg="gray.700"
      color="white"
      p={2}
      borderRadius="md"
    >
      <Box as="span" cursor="help">
        <FiInfo size={16} />
      </Box>
    </ChakraTooltip>
  </Flex>
);

const MUPDataVisualizer = ({ institutionName }: Props) => {
  const [loading, setLoading] = useState(true);
  const [mupData, setMupData] = useState<MUPData | null>(null);
  const [satData, setSatData] = useState<SATData | null>(null);
  const [endowmentData, setEndowmentData] = useState<EndowmentGivingData | null>(null);
  const [medicalData, setMedicalData] = useState<MedicalExpenseData | null>(null);
  const [doctorateData, setDoctorateData] = useState<DoctoratePostdocData | null>(null);
  const [researchData, setResearchData] = useState<ResearchData | null>(null);
  const [facultyAwardsData, setFacultyAwardsData] = useState<FacultyAwardsData | null>(null);
  const [rAndDData, setRAndDData] = useState<RAndDData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [fetchErrors, setFetchErrors] = useState<{[key: string]: string}>({});
  const BASE_URL = process.env.REACT_APP_BASE_URL || "";

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        if (!BASE_URL) {
          throw new Error("BASE_URL is not defined");
        }

        const mupIdResponse = await fetch(`${BASE_URL}/get-mup-id`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ institution_name: institutionName }),
        });
        const mupIdData = await mupIdResponse.json();
        
        const mupId = mupIdData.institution_mup_id;

        const fetchPromises = [
          fetch(`${BASE_URL}/mup-sat-scores`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ institution_name: institutionName }),
          }).then(res => res.json()).catch(() => {
            setFetchErrors(prev => ({...prev, sat: "SAT score data not available for this institution"}));
            return null;
          }),

          fetch(`${BASE_URL}/endowments-and-givings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ institution_name: institutionName }),
          }).then(res => res.json()).catch(() => {
            setFetchErrors(prev => ({...prev, endowment: "Endowment data not available for this institution"}));
            return null;
          }),

          mupId ? fetch(`${BASE_URL}/institution_medical_expenses`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ institution_name: institutionName }),
          }).then(res => res.json()).catch(() => {
            setFetchErrors(prev => ({...prev, medical: "Medical expense data not available for this institution"}));
            return null;
          }) : Promise.resolve(null),

          fetch(`${BASE_URL}/institution_doctorates_and_postdocs`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ institution_name: institutionName }),
          }).then(res => res.json()).catch(() => {
            setFetchErrors(prev => ({...prev, doctorate: "Doctorate/Postdoc data not available for this institution"}));
            return null;
          }),

          fetch(`${BASE_URL}/institution_num_of_researches`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ institution_name: institutionName }),
          }).then(res => res.json()).catch(() => {
            setFetchErrors(prev => ({...prev, research: "Research data not available for this institution"}));
            return null;
          }),

          fetch(`${BASE_URL}/mup-faculty-awards`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ institution_name: institutionName }),
          }).then(res => res.json()).catch(() => {
            setFetchErrors(prev => ({...prev, faculty: "Faculty awards data not available for this institution"}));
            return null;
          }),

          fetch(`${BASE_URL}/mup-r-and-d`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ institution_name: institutionName }),
          }).then(res => res.json()).catch(() => {
            setFetchErrors(prev => ({...prev, rAndD: "R&D data not available for this institution"}));
            return null;
          }),
        ];

        const [satData, endowmentData, medicalData, doctorateData, researchData, facultyAwardsData, rAndDData] = await Promise.all(fetchPromises);

        if (satData && !satData.error) setSatData(satData);
        if (endowmentData && !endowmentData.error) setEndowmentData(endowmentData);
        if (medicalData && !medicalData.error) setMedicalData(medicalData);
        if (doctorateData && !doctorateData.error) setDoctorateData(doctorateData);
        if (researchData && !researchData.error) setResearchData(researchData);
        if (facultyAwardsData && !facultyAwardsData.error) setFacultyAwardsData(facultyAwardsData);
        if (rAndDData && !rAndDData.error) setRAndDData(rAndDData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (institutionName) {
      fetchData();
    }
  }, [institutionName, BASE_URL]);

  const createChartData = (label: string, data: Array<{year: number, [key: string]: any}>, valueKeys: string[], valueLabels: string[], xAxis?: string) => {
    const sortedData = [...data].sort((a, b) => a.year - b.year);
    
    return {
      labels: sortedData.map(item => item[xAxis || 'year']),
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
    // Filter out null values and sort by year
    const validData = data.data
      .filter(d => d.sat !== null)
      .sort((a, b) => a.year - b.year);

    const chartData = {
      labels: validData.map(d => d.year),
      datasets: [{
        label: 'SAT Score',
        data: validData.map(d => d.sat),
        borderColor: '#003057',
        tension: 0.1,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6,
        spanGaps: true,
      }]
    };

    const satOptions = {
      ...chartOptions,
      scales: {
        x: {
          type: 'category' as const,
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
            font: {
              family: "'Inter', sans-serif",
            },
          },
        },
      },
      plugins: {
        ...chartOptions.plugins,
        tooltip: {
          ...chartOptions.plugins.tooltip,
          callbacks: {
            title: function(tooltipItems: any) {
              return tooltipItems[0].label;
            },
            label: function(context: any) {
              return `SAT Score: ${context.raw}`;
            }
          }
        }
      }
    };

    return (
      <div style={{ height: '100%', width: '100%', position: 'relative' }}>
        <Line data={chartData} options={satOptions} />
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

  const renderFacultyAwardsChart = (data: FacultyAwardsData) => {
    const chartData = createChartData(
      'Faculty Awards',
      data.data,
      ['nae', 'nam', 'nas', 'num_fac_awards'],
      ['National Academy of Engineering', 'National Academy of Medicine', 'National Academy of Sciences', 'Total Faculty Awards']
    );

    const facultyOptions = {
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
            font: {
              family: "'Inter', sans-serif",
            },
            stepSize: 1,
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
                return `${context.dataset.label}: ${value}`;
              }
              return context.dataset.label;
            }
          }
        }
      }
    };

    return (
      <div style={{ height: '100%', width: '100%', position: 'relative' }}>
        <Line data={chartData} options={facultyOptions} />
      </div>
    );
  };

  const renderRAndDChart = (data: RAndDData) => {
    const filteredData = data.data.filter(d => d.category !== '"sum"').map(d => ({
      ...d,
      category: d.category.replace(/"/g, '').split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    }));
    
    const chartData = createChartData(
      'R&D Numbers',
      filteredData,
      ['federal', 'total'],
      ['Federal Numbers', 'Total Numbers'],
      'category'
    );

    const rAndDOptions = {
      ...chartOptions,
      scales: {
        x: {
          type: 'category',
          display: true,
          title: {
            display: true,
            text: 'Category',
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
            font: {
              family: "'Inter', sans-serif",
            },
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
              const percent = context.dataset.label === 'Federal Numbers' 
                ? filteredData[context.dataIndex].percent_federal
                : filteredData[context.dataIndex].percent_total;
              return `${context.dataset.label}: ${value.toLocaleString()} (${(percent * 100).toFixed(1)}%)`;
            }
          }
        }
      }
    };

    return (
      <div style={{ height: '100%', width: '100%', position: 'relative' }}>
        <Line data={chartData} options={rAndDOptions} />
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

  const renderChartWithError = (chartData: any, errorKey: string, title: string) => {
    if (fetchErrors[errorKey]) {
      return (
        <Box
          height="100%"
          width="100%"
          display="flex"
          alignItems="center"
          justifyContent="center"
          textAlign="center"
          p={4}
        >
          <Text color="gray.500">
            {fetchErrors[errorKey]}
          </Text>
        </Box>
      );
    }
    
    if (!chartData) {
      return (
        <Box
          height="100%"
          width="100%"
          display="flex"
          alignItems="center"
          justifyContent="center"
          textAlign="center"
          p={4}
        >
          <Text color="gray.500">No data available</Text>
        </Box>
      );
    }

    return chartData;
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
          MUP Institution Data
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
          <ChartHeader 
            title="SAT Score by Year"
            description="Shows the average SAT scores of admitted students over time."
          />
          {renderChartWithError(
            satData && satData.data && satData.data.length > 0 ? renderSATChart(satData) : null,
            'sat',
            'SAT Score by Year'
          )}
        </Box>

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
          <ChartHeader 
            title="Endowment and Giving by Year"
            description="Shows the institution's endowment value and annual giving over time."
          />
          {renderChartWithError(
            endowmentData && endowmentData.data && endowmentData.data.length > 0 ? renderEndowmentChart(endowmentData) : null,
            'endowment',
            'Endowment and Giving by Year'
          )}
        </Box>

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
          <ChartHeader 
            title="Medical Expenditure by Year"
            description="Shows the institution's medical expenses over time."
          />
          {renderChartWithError(
            medicalData && medicalData.data && medicalData.data.length > 0 ? renderMedicalChart(medicalData) : null,
            'medical',
            'Medical Expenditure by Year'
          )}
        </Box>

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
          <ChartHeader 
            title="Doctorates and Postdocs Numbers by Year"
            description="Shows the number of doctorates and postdocs awarded over time."
          />
          {renderChartWithError(
            doctorateData && doctorateData.data && doctorateData.data.length > 0 ? renderDoctorateChart(doctorateData) : null,
            'doctorate',
            'Doctorates and Postdocs Numbers by Year'
          )}
        </Box>

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
          <ChartHeader 
            title="Research Numbers by Year"
            description="Shows the number of research projects over time."
          />
          {renderChartWithError(
            researchData && researchData.data && researchData.data.length > 0 ? renderResearchChart(researchData) : null,
            'research',
            'Research Numbers by Year'
          )}
        </Box>

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
          <ChartHeader 
            title="Faculty Awards by Year"
            description="Shows the number of prestigious faculty awards (NAE, NAM, NAS) received."
          />
          {renderChartWithError(
            facultyAwardsData && facultyAwardsData.data && facultyAwardsData.data.length > 0 ? renderFacultyAwardsChart(facultyAwardsData) : null,
            'faculty',
            'Faculty Awards by Year'
          )}
        </Box>

        <Box 
          p={6} 
          bg="white" 
          borderRadius="xl" 
          boxShadow="sm"
          transition="all 0.3s"
          _hover={{ transform: 'translateY(-4px)', boxShadow: 'lg' }}
          height="500px"
          position="relative"
          overflow="hidden"
        >
          <ChartHeader 
            title="R&D Numbers by Category"
            description="Shows the breakdown of research and development numbers by category."
          />
          {renderChartWithError(
            rAndDData && rAndDData.data && rAndDData.data.length > 0 ? renderRAndDChart(rAndDData) : null,
            'rAndD',
            'R&D Numbers by Category'
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default MUPDataVisualizer;