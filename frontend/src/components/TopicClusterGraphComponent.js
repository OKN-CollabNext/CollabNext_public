import { useEffect, useRef } from 'react';
import { Orb } from '@memgraph/orb';
import { Box } from '@chakra-ui/react';

const BASE_SIZE = 6;
const SCALE_FACTOR = 2;

const TopicClusterGraphComponent = ({ graphData }) => {
  const graphContainerRef = useRef(null);

  useEffect(() => {
    if (!graphData) return;
    /* If the nodes & edges do render (please do), we have almost 100% data "coverage" and now we can pull in these nodes and edges */
    const { nodes, edges } = graphData;
    /* There we can share the re-annotation of the nodes with linkCount (that is, if we haven't already done so up-stream) */
    const annotated = nodes.map(n => ({
      ...n,
      linkCount:
        typeof n.linkCount === 'number'
          ? n.linkCount
          : edges.filter(e => e.start === n.id).length,
    }));
    /* Notice the Orb has been initialized */
    const orb = new Orb(graphContainerRef.current);
    orb.view.setSettings({
      render: { backgroundColor: '#f4faff', padding: '0', margin: '0' },
    });
    orb.data.setDefaultStyle({
      getNodeStyle(node) {
        /* Makes some executor diameter */
        const count = node.data.linkCount || 0;
        const orbSize = BASE_SIZE + count * SCALE_FACTOR;
        const style = {
          borderColor: '#1d1d1d',
          borderWidth: 0.6,
          color: '#DD2222',
          fontSize: 3,
          label: node.data.label,
          size: orbSize,
        };
        /* maps special highlight style for the core topic */
        if (node.data.type === 'TOPIC') {
          return {
            ...style,
            color: '#44AA99',
            zIndex: 1,
            // bump those just a bit more
            size: orbSize + 4,
          };
        }
        return style;
      },
      getEdgeStyle() {
        return {
          color: '#999999',
          colorSelected: '#1d1d1d',
          width: 0.3,
        };
      },
    });
    orb.data.setup({ nodes: annotated, edges });
    orb.view.render(() => {
      orb.view.recenter();
    });
  }, [graphData]);

  return (
    <Box>
      <div
        ref={graphContainerRef}
        id="graph"
        style={{ height: '500px', width: '100%' }}
      />
    </Box>
  );
};

export default TopicClusterGraphComponent;
