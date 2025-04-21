import React, { useState, useEffect } from 'react';
import {
  Box,
  Text,
  Collapse,
  Spinner,
  useDisclosure,
} from '@chakra-ui/react';

/**
 * On first open we:
 *   1) look the author up → get their OpenAlex ID
 *   2) pull *all* works for author ∩ topic (sorted by citations)
 */
const ExpandableWorksCell = ({
  authorName,
  topicName,
}: {
  authorName: string;
  topicName: string;
}) => {
  const { isOpen, onToggle } = useDisclosure();
  const [loading, setLoading] = useState(false);
  const [works, setWorks] = useState<{ title: string; cites: number }[]>([]);

  useEffect(() => {
    if (!isOpen || works.length) return;

    const fetchWorks = async () => {
      setLoading(true);
      try {
        /* step 1 – author lookup */
        const aRes = await fetch(
          `https://api.openalex.org/authors?search=${encodeURIComponent(
            authorName,
          )}&per-page=1`,
        );
        const aJson = await aRes.json();
        if (!aJson.results?.length) throw new Error('author not found');
        const authorId = aJson.results[0].id.replace(
          'https://openalex.org/',
          '',
        );
        /* step 2 – works lookup (author ∩ topic) */
        const wRes = await fetch(
          `https://api.openalex.org/works?search=${encodeURIComponent(
            topicName
          )}&filter=authorships.author.id:${authorId}&per-page=200&sort=cited_by_count:desc`
        );
        const wJson = await wRes.json();
        const ws =
          wJson.results?.map((w: any) => ({
            title: w.display_name,
            cites: w.cited_by_count,
          })) ?? [];
        if (!ws.length) {
          setWorks([{ title: 'No works found for this topic', cites: 0 }]);
          return;
        }
        setWorks(ws);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchWorks();
  }, [isOpen]);

  return (
    <Box w="32%">
      <Text
        fontSize="14px"
        cursor="pointer"
        textDecoration="underline"
        onClick={onToggle}
      >
        {isOpen ? 'hide articles' : 'show articles'}
      </Text>

      <Collapse in={isOpen} animateOpacity>
        {loading ? (
          <Spinner size="sm" mt="4px" />
        ) : (
          <Box mt="4px">
            {works.slice(0, 30).map(w => (
              <Text key={w.title} fontSize="13px" mb="2px">
                • {w.title} ({w.cites})
              </Text>
            ))}
            {works.length > 30 && (
              <Text fontSize="12px" mt="2px">
                …showing first 30 of {works.length}
              </Text>
            )}
          </Box>
        )}
      </Collapse>
    </Box>
  );
};

export default ExpandableWorksCell;
