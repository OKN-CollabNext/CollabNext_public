export function TransformTopicClustersForOrb(data, topicClusters) {
  const nodes = [];
  const edges = [];

  const topicNameId = `topic_${data?.topic_name}`;
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
      id,
      start: subfieldNodeId,
      end: topicNameId,
    });
  });
  return {
    nodes,
    edges,
  };
};
