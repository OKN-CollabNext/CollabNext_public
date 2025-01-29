import React, { useEffect, useRef } from 'react';
import { Orb } from '@memgraph/orb';
import { Box } from '@chakra-ui/react';

const TopicClusterGraphComponent = ({ graphData }) => {
  const graphContainerRef = useRef(null);

  useEffect(() => {
    if (!graphData) {
      return; // Exit early if no data is provided
    }

    const { nodes, edges } = graphData;
    const container = graphContainerRef.current;
    const orb = new Orb(container);

    orb.view.setSettings({
      render: {
        backgroundColor: '#f4faff',
        padding: '0',
        margin: '0',
      },
    });

    orb.data.setDefaultStyle({
      getNodeStyle(node) {
        const basicStyle = {
          borderColor: '#1d1d1d',
          borderWidth: 0.6,
          color: '#DD2222',
          fontSize: 3,
          label: node.data.label,
          size: 6,
        };

        if (node.data.type === 'TOPIC') {
          return {
            ...basicStyle,
            size: 10,
            color: '#44AA99',
            zIndex: 1,
          };
        }
        return basicStyle;
      },
      getEdgeStyle() {
        return {
          color: '#999999',
          colorSelected: '#1d1d1d',
          width: 0.3,
        };
      },
    });

    orb.data.setup({ nodes, edges });

    orb.view.render(() => {
      orb.view.recenter();
    });
  }, [graphData]);

  return (
    <Box>
      <div ref={graphContainerRef} id="graph" style={{ height: '500px', width: '100%' }} />
    </Box>
  );
};

export default TopicClusterGraphComponent;
