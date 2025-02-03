import React from 'react';

import { Box, Text, Link } from '@chakra-ui/react';

const DataSources = () => {
    return (
        <Box w={{ lg: '900px' }} mx='auto' mt='1.5rem'>
            <Text
                pl={{ base: '.8rem', lg: 0 }}
                fontFamily='DM Sans'
                fontSize={{ lg: '22px' }}
                color='#000000'
            >
                Data Sources
            </Text>
            <Box
                background='linear-gradient(180deg, #003057 0%, rgba(0, 0, 0, 0.5) 100%)'
                borderRadius={{ lg: '6px' }}
                px='.8rem'
                py={{ base: '1.5rem', lg: '2rem' }}
                mt='1rem'
            >
                <Box>
                    <Text
                        fontSize={{ base: '17px', lg: '24px' }}
                        color='#FFFFFF'
                        fontWeight={'bold'}
                    >
                        Background
                    </Text>
                    <Text
                        mt='.45rem'
                        lineHeight='24px'
                        color='#FFFFFF'
                        fontSize={{ base: '12px', lg: '16px' }}
                    >
                        We rely on data from
                        {' '}
                        <a
                            href='https://explore.openalex.org/'
                            target='_blank'
                            rel='noreferrer'
                            style={{ color: 'cornsilk', textDecoration: 'underline' }}
                        >
                            OpenAlex
                        </a>{' '}

                        (formerly
                        {' '}
                        <a
                            href='https://aka.ms/msracad'
                            target='_blank'
                            rel='noreferrer'
                            style={{ color: 'cornsilk', textDecoration: 'underline' }}
                        >
                            Microsoft Academic Graph
                        </a>{' '}

                        ) as our primary data
                        source. OpenAlex is a free, open repository of bibliographic data that includes researchers,
                        institutions, publications, and topics. The

                        {' '}
                        <a
                            href='https://docs.openalex.org/api-entities/sources'
                            target='_blank'
                            rel='noreferrer'
                            style={{ color: 'cornsilk', textDecoration: 'underline' }}
                        >
                            data sources that OpenAlex uses are cataloged here
                        </a>{' '}

                        and

                        {' '}
                        <a
                            href='https://help.openalex.org/hc/en-us/articles/24397285563671-About-the-data'
                            target='_blank'
                            rel='noreferrer'
                            style={{ color: 'cornsilk', textDecoration: 'underline' }}
                        >
                            include
                        </a>{' '}
                        (but are not limited to):
                        <Text style={{ fontSize: 20 }}>
                            {" "}
                            <Link
                                variant="underline"
                                href="https://aka.ms/msracad"
                            >
                                MAG
                            </Link>{" "}
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            {" "}
                            <Link
                                variant="underline"
                                href="https://www.crossref.org/"
                            >
                                CrossRef
                            </Link>{" "}
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            {" "}
                            <Link
                                variant="underline"
                                href="https://orcid.org/"
                            >
                                ORCID
                            </Link>{" "}
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            {" "}
                            <Link
                                variant="underline"
                                href="https://doaj.org/"
                            >
                                DOAJ
                            </Link>{" "}
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            {" "}
                            <Link
                                variant="underline"
                                href="https://unpaywall.org/"
                            >
                                Unpaywall
                            </Link>{" "}
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            {" "}
                            <Link
                                variant="underline"
                                href="https://pubmed.ncbi.nlm.nih.gov/"
                            >
                                Pubmed
                            </Link>{" "}
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            {" "}
                            <Link
                                variant="underline"
                                href="https://www.ncbi.nlm.nih.gov/pmc/"
                            >
                                Pubmed Central
                            </Link>{" "}
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            {" "}
                            <Link
                                variant="underline"
                                href="https://www.issn.org/"
                            >
                                The ISSN International Center
                            </Link>{" "}
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            {" "}
                            <Link
                                variant="underline"
                                href="https://archive.org/details/GeneralIndex"
                            >
                                Internet Archive
                            </Link>{" "}
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            Web crawls
                        </Text>
                        <Text style={{ fontSize: 20 }}>
                            Subject - area and institutional repositories from arXiv to Zenodo and more
                        </Text>
                    </Text>
                </Box>
                <Box mt='1.7rem'>
                    <Text
                        fontSize={{ base: '17px', lg: '24px' }}
                        color='#FFFFFF'
                        fontWeight={'bold'}
                    >

                    </Text>
                    <Text
                        mt='.45rem'
                        lineHeight='24px'
                        color='#FFFFFF'
                        fontSize={{ base: '12px', lg: '16px' }}
                    >
                        if you find errors in the data, it is likely an upstream error that needs to be addressed with OpenAlex directly.  You can submit suggested data corrections to OpenAlex via their support form.
                    </Text>
                    <Text
                        mt='.45rem'
                        lineHeight='24px'
                        color='#FFFFFF'
                        fontSize={{ base: '12px', lg: '16px' }}
                    >
                        We are also using data from the Center for Measuring University Performance (MUP).
                        MUP provides a well-curated, longitudinal, and broad source of data about universities that draws from public sources and also has had captured data including:
                    </Text>
                </Box>
                <Box mt='1.7rem'>
                    <Text
                        fontSize={{ base: '17px', lg: '24px' }}
                        color='#FFFFFF'
                        fontWeight={'bold'}
                    >
                        Current State
                    </Text>
                    <Text
                        mt='.45rem'
                        lineHeight='24px'
                        color='#FFFFFF'
                        fontSize={{ base: '12px', lg: '16px' }}
                    >
                        The{' '}
                        <a
                            href='https://gt-msi-diversifind.azuremicroservices.io/'
                            target='_blank'
                            rel='noreferrer'
                            style={{ color: 'cornsilk', textDecoration: 'underline' }}
                        >
                            current CollabNext tool
                        </a>{' '}
                        is a very rough proof-of-concept. We are developing future versions,
                        moving from alpha to beta to production over the next three years
                        thanks to funding from the NSF. We are part of the{' '}
                        <a
                            href='https://www.proto-okn.net/'
                            target='_blank'
                            rel='noreferrer'
                            style={{ color: 'cornsilk', textDecoration: 'underline' }}
                        >
                            Prototype Open Knowledge Network
                        </a>{' '}
                        (aka ProtoOKN).
                    </Text>
                </Box>
                <Box mt='1.7rem'>
                    <Text
                        fontSize={{ base: '17px', lg: '24px' }}
                        color='#FFFFFF'
                        fontWeight={'bold'}
                    >
                        Data and Methodology
                    </Text>
                    <Text
                        mt='.45rem'
                        lineHeight='24px'
                        color='#FFFFFF'
                        fontSize={{ base: '12px', lg: '16px' }}
                    >
                        All of this MUP data is not at the individual researcher level, but rather at the institution level, and therefore it will mostly exist in our knowledge graph as data connected to institutions.

                        As the CollabNext project developes, we plan to add other open data sources. In particular, we will explore gaps in OpenAlex with respect to underrepresented and emerging researchers. This might include adding data sources for conference proceedings from various MSI and professional societies that are not typically indexed. We are also interested in connecting to Masters and PhD thesis data. Another good source of connecting people to topics are institutional repositories.

                        Other data sources of interest are related to research grants (federal government agencies, foundations, state level, etc.). Ideally, we would work to capture what people are funded on which projects (eg PIs, co-PIs, Senior Personnel). This connection of people to topics is useful because, unlike publications and citations which are delayed, lagging indicators of researcher interest, grants and research funding happens earlier in the research pipeline. Finally, we mention that patent data and startup company data gives additional translational research perspectives on researcher interests and potential commercial viability of research areas.

                        We note that our data is not actually pulled directly from the OpenAlex API.  In order to improve connectivity to other knowledge graphs in the Proto-OKN, we are leveraging RDF Triples from SemOpenAlex. This is a project with over 26 billion RDF & RDF-star triples, built upon OpenAlex data.


                    </Text>
                </Box>
            </Box>
        </Box >
    );
};

export default DataSources;
