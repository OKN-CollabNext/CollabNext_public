export function TransformTopicClustersForOrb(data, topicClusters) {
  /* Covers the rest of the edges & nodes */
  const nodes = [];
  const edges = [];
  const topicNameId = `topic_${data.topic_name}`;
  nodes.push({
    id: topicNameId,
    label: data.topic_name,
    type: "TOPIC",
  });
  topicClusters.forEach((topic, id) => {
    const subfieldNodeId = `subfield_${id}`;
    nodes.push({
      id: subfieldNodeId,
      label: topic,
      type: "SUBFIELD",
    });
    edges.push({
      id: `${subfieldNodeId}->${topicNameId}`,
      start: subfieldNodeId,
      end: topicNameId,
    });
  });
  /* Unless nodes have more than one out-going edge..we count them */
  const linkCounts = nodes.reduce((acc, node) => {
    acc[node.id] = edges.filter(e => e.start === node.id).length;
    return acc;
  }, {});
  /* At the end of the day we need to annotate each node with its accompanying linkCount */
  const annotatedNodes = nodes.map(n => ({
    ...n,
    // handles the orb to decide on `node.data.linkCount`
    linkCount: linkCounts[n.id] || 0,
  }));
  return {
    nodes: annotatedNodes,
    edges,
  };
}
