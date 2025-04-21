import { useEffect, useRef, useState } from 'react';
import { Orb } from '@memgraph/orb';
import {
  Box,
  Modal,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  useDisclosure,
} from '@chakra-ui/react';

const BASE_SIZE = 6;
const SCALE_FACTOR = 1.5;

const GraphComponent = ({ graphData, setInstitution, setTopic, setResearcher }) => {
  const graphContainerRef = useRef(null);
  const loaderOverlayRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const { isOpen, onOpen, onClose } = useDisclosure();

  useEffect(() => {
    if (!graphData) return;
    let { nodes, edges } = graphData;
    /* Every once in a while annotate the nodes with the outgoing-link counts */
    const annotated = nodes.map(n => ({
      ...n,
      linkCount:
        typeof n.linkCount === 'number'
          ? n.linkCount
          : edges.filter(e => e.start === n.id).length,
    }));
    /* Every once in a while initialize the orb itself! */
    const orb = new Orb(graphContainerRef.current);
    orb.view.setSettings({
      render: { backgroundColor: '#f4faff', padding: '0', margin: '0' },
    });
    orb.data.setDefaultStyle({
      getNodeStyle(node) {
        const count = node.data.linkCount || 0;
        const orbSize = BASE_SIZE + count * SCALE_FACTOR;
        const baseStyle = {
          borderColor: '#1d1d1d',
          borderWidth: 0.6,
          color: '#DD2222',
          colorHover: '#e7644e',
          colorSelected: '#e7644e',
          fontSize: 3,
          label: node.data.label,
          size: orbSize,
        };
        // color‑code by type as a follow-up, but keep dynamic sizing
        switch (node.data.type) {
          case 'AUTHOR':
            return { ...baseStyle, color: '#332288', zIndex: 1 };
          case 'WORK':
            return { ...baseStyle, color: '#117733', zIndex: 1 };
          case 'TOPIC':
            return { ...baseStyle, color: '#44AA99', zIndex: 1 };
          case 'INSTITUTION':
            return { ...baseStyle, color: '#88CCEE', zIndex: 1 };
          case 'DOMAIN':
            return { ...baseStyle, color: '#DDCC77', zIndex: 1 };
          case 'FIELD':
            return { ...baseStyle, color: '#CC6677', zIndex: 1 };
          case 'SUBFIELD':
            return { ...baseStyle, color: '#AA4499', zIndex: 1 };
          default:
            return baseStyle;
        }
      },
      getEdgeStyle(edge) {
        return {
          color: '#999999',
          colorHover: '#1d1d1d',
          colorSelected: '#1d1d1d',
          fontSize: 3,
          width: edge.data.connecting_authors
            ? edge.data.connecting_authors / 100
            : 0.3,
          widthHover: 0.9,
          widthSelected: 0.9,
          label: edge.data.label,
        };
      },
    });
    // Want to show loading
    if (loaderOverlayRef.current) {
      loaderOverlayRef.current.style.display = 'flex';
    }
    orb.data.setup({ nodes: annotated, edges });
    orb.events.on('node-click', event => {
      const d = event.node.data;
      setSelectedNode(d);
      if (d.type === 'INSTITUTION') setInstitution(d.label);
      if (d.type === 'TOPIC') setTopic(d.label);
      if (d.type === 'AUTHOR') setResearcher(d.label);
    });
    orb.events.on('edge-click', event => {
      const e = event.edge.data;
      setSelectedNode(e);
      if (e.connecting_works) onOpen();
    });
    orb.view.render(() => {
      if (loaderOverlayRef.current) {
        loaderOverlayRef.current.style.display = 'none';
      }
      orb.view.recenter();
    });
  }, [graphData, onOpen, setInstitution, setTopic, setResearcher]);

  const renderDetails = () => {
    if (!selectedNode) return null;
    let html = '';
    if (selectedNode.type === 'INSTITUTION' || selectedNode.type === 'AUTHOR' || selectedNode.type === 'TOPIC') {
      html = `<a href="${selectedNode.id}" target="_blank"><b>View on OpenAlex:</b> ${selectedNode.id}</a>`;
    } else if (selectedNode.start_type === 'AUTHOR' && selectedNode.end_type === 'TOPIC') {
      html = `<b>Connecting Works:</b> ${selectedNode.connecting_works}`;
    } else if (selectedNode.start_type === 'INSTITUTION' && selectedNode.end_type === 'SUBFIELD') {
      html = `<b>Connecting Authors:</b> ${selectedNode.connecting_authors}`;
    }
    return (
      <div
        className={selectedNode.start_type === 'AUTHOR' && selectedNode.end_type === 'TOPIC' ? undefined : 'ror'}
        style={selectedNode.start_type === 'AUTHOR' && selectedNode.end_type === 'TOPIC'
          ? { marginTop: '10px', color: 'black', fontWeight: 'bold' }
          : { textDecoration: 'underline', marginTop: '10px' }
        }
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  };

  return (
    <div>
      <div ref={loaderOverlayRef} id="loader-overlay" style={{ display: 'none' }}>
        Loading...
      </div>
      <div ref={graphContainerRef} id="graph" style={{ height: '500px', width: '100%' }} />
      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>More Details</ModalHeader>
          <Box mx="1.5rem" mb="2rem" className="details">
            {renderDetails()}
          </Box>
          <ModalCloseButton />
        </ModalContent>
      </Modal>
    </div>
  );
};

export default GraphComponent;
