import React, {useEffect, useRef, useState} from 'react';
import {Orb} from '@memgraph/orb';
import {
  Box,
  Modal,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  useDisclosure,
} from '@chakra-ui/react';

const GraphComponent = ({graphData}) => {
  const graphContainerRef = useRef(null);
  const loaderOverlayRef = useRef(null);
  // const detailsRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const {isOpen, onOpen, onClose} = useDisclosure();

  useEffect(() => {
    if (!graphData) {
      return; // Exit early if no data is provided
    }

    const {nodes, edges} = graphData; // Destructure nodes and edges from graphData

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
          colorHover: '#e7644e',
          colorSelected: '#e7644e',
          fontSize: 3,
          label: node.data.label,
          size: 6,
        };

        if (node.data.type === 'AUTHOR') {
          return {
            ...basicStyle,
            size: 10,
            color: '#332288',
            zIndex: 1,
          };
        }

        if (node.data.type === 'WORK') {
          return {
            ...basicStyle,
            size: 10,
            color: '#117733',
            zIndex: 1,
          };
        }

        if (node.data.type === 'TOPIC') {
          return {
            ...basicStyle,
            size: 10,
            color: '#44AA99',
            zIndex: 1,
          };
        }

        if (node.data.type === 'INSTITUTION') {
          return {
            ...basicStyle,
            size: 10,
            color: '#88CCEE',
            zIndex: 1,
          };
        }

        if (node.data.type === 'DOMAIN') {
          return {
            ...basicStyle,
            size: 10,
            color: '#DDCC77',
            zIndex: 1,
          };
        }

        if (node.data.type === 'FIELD') {
          return {
            ...basicStyle,
            size: 10,
            color: '#CC6677',
            zIndex: 1,
          };
        }

        if (node.data.type === 'SUBFIELD') {
          return {
            ...basicStyle,
            size: 10,
            color: '#AA4499',
            zIndex: 1,
          };
        }

        if (node.data.type === 'KEYWORD') {
          return {
            ...basicStyle,
            size: 10,
            color: '#882255',
            zIndex: 1,
          };
        }

        return {
          ...basicStyle,
        };
      },
      getEdgeStyle(edge) {
        console.log(edge?.data?.connecting_authors);
        return {
          color: '#999999',
          colorHover: '#1d1d1d',
          colorSelected: '#1d1d1d',
          fontSize: 3,
          width: edge?.data?.connecting_authors
            ? edge?.data?.connecting_authors / 100
            : 0.3,
          widthHover: 0.9,
          widthSelected: 0.9,
          label: edge.data.label,
        };
      },
    });

    if (loaderOverlayRef.current) {
      loaderOverlayRef.current.style.display = 'flex';
    }

    orb.data.setup({nodes, edges});

    orb.events.on('node-click', (event) => {
      handleNodeClick(event);
    });

    orb.events.on('edge-click', (event) => {
      handleEdgeClick(event);
    });

    function handleNodeClick(event) {
      const nodeData = event.node.data;
      console.log('Selected Node:', nodeData); // Log the selected node to the console
      setSelectedNode(nodeData);
      nodeData?.type !== 'DOMAIN' && onOpen();
    }

    function handleEdgeClick(event) {
      const edgeData = event.edge.data;
      console.log('Selected Edge:', edgeData);
      setSelectedNode(edgeData);
      edgeData?.connecting_works && onOpen();
    }

    orb.view.render(() => {
      if (loaderOverlayRef.current) {
        loaderOverlayRef.current.style.display = 'none';
      }
      // if (detailsRef.current) {
      //   detailsRef.current.style.display = 'block';
      // }
      orb.view.recenter();
    });
  }, [graphData, onOpen]);

  const renderDetails = () => {
    if (!selectedNode) return null;

    console.log('selectedNode', selectedNode);

    let html = '';

    if (selectedNode.type === 'INSTITUTION') {
      // html += `<a href="${selectedNode.id}" target="_blank">View on OpenAlex</a>`;
      html += `<a href="${selectedNode.id}" target="_blank"><b>View on OpenAlex:</b> ${selectedNode.id}</a>`;
    } else if (selectedNode.type === 'AUTHOR') {
      html += `<a href="${selectedNode.id}" target="_blank"><b>View on OpenAlex:</b> ${selectedNode.id}</a>`;
    } else if (selectedNode.type === 'TOPIC') {
      // html += `<a href="${selectedNode.id}" target="_blank">View on OpenAlex</a>`;
      html += `<a href="${selectedNode.id}" target="_blank"><b>View on OpenAlex:</b> ${selectedNode.id}</a>`;
    } else if (selectedNode.start_type === 'AUTHOR') {
      if (selectedNode.end_type === 'TOPIC') {
        html += `<b>Connecting Works:</b> ${selectedNode.connecting_works}`;
      }
    } else if (selectedNode.start_type === "INSTITUTION") {
      if (selectedNode.end_type === "SUBFIELD") {
        html += `<b>Connecting Authors:</b> ${selectedNode.connecting_authors}`;
      }
    }

    return (
      <div
        className={
          selectedNode.start_type === 'AUTHOR' &&
          selectedNode.end_type === 'TOPIC'
            ? undefined
            : 'ror'
        }
        style={
          selectedNode.start_type === 'AUTHOR' &&
          selectedNode.end_type === 'TOPIC'
            ? {marginTop: '10px', color: 'black', fontWeight: 'bold'}
            : {
                textDecoration: 'underline',
                marginTop: '10px',
              }
        }
        dangerouslySetInnerHTML={{__html: html}}
      />
    );
  };

  return (
    <div>
      <div ref={loaderOverlayRef} id='loader-overlay' style={{display: 'none'}}>
        Loading...
      </div>
      <div
        ref={graphContainerRef}
        id='graph'
        style={{height: '500px', width: '100%'}}
      />
      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>More Details</ModalHeader>
          <Box mx='1.5rem' mb='2rem' className='details'>
            {renderDetails()}
          </Box>
          <ModalCloseButton />
        </ModalContent>
      </Modal>
      {/* <div ref={detailsRef} className='details' style={{display: 'none'}}>
        {renderDetails()}
      </div> */}
    </div>
  );
};

export default GraphComponent;
