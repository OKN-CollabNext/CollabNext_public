import styles from "../styles/DataSources.module.css";

const DataSources = () => {
    return (
        <div className={styles.container}>
            <section className={styles.heroSection}>
                <h1>Data Sources</h1>
            </section>
            <section className={styles.mainContent}>
                <div className={styles.block}>
                    <h2>Background</h2>
                    <p>
                        We rely on data from{" "}
                        <a
                            href="https://explore.openalex.org/"
                            target="_blank"
                            rel="noreferrer"
                            className={styles.link}
                        >
                            OpenAlex
                        </a>{" "}
                        (formerly{" "}
                        <a
                            href="https://aka.ms/msracad"
                            target="_blank"
                            rel="noreferrer"
                            className={styles.link}
                        >
                            Microsoft Academic Graph
                        </a>
                        ) as our primary data source. OpenAlex is a free, open repository
                        of bibliographic data that includes researchers, institutions,
                        publications, and topics. The{" "}
                        <a
                            href="https://docs.openalex.org/api-entities/sources"
                            target="_blank"
                            rel="noreferrer"
                            className={styles.link}
                        >
                            data sources that OpenAlex uses
                        </a>{" "}
                        are cataloged here and include (but are not limited to):
                    </p>
                    <ul>
                        <li>
                            <a
                                href="https://aka.ms/msracad"
                                target="_blank"
                                rel="noreferrer"
                                className={styles.link}
                            >
                                MAG
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://www.crossref.org/"
                                target="_blank"
                                rel="noreferrer"
                                className={styles.link}
                            >
                                CrossRef
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://orcid.org/"
                                target="_blank"
                                rel="noreferrer"
                                className={styles.link}
                            >
                                ORCID
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://doaj.org/"
                                target="_blank"
                                rel="noreferrer"
                                className={styles.link}
                            >
                                DOAJ
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://unpaywall.org/"
                                target="_blank"
                                rel="noreferrer"
                                className={styles.link}
                            >
                                Unpaywall
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://pubmed.ncbi.nlm.nih.gov/"
                                target="_blank"
                                rel="noreferrer"
                                className={styles.link}
                            >
                                Pubmed
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://www.ncbi.nlm.nih.gov/pmc/"
                                target="_blank"
                                rel="noreferrer"
                                className={styles.link}
                            >
                                Pubmed Central
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://www.issn.org/"
                                target="_blank"
                                rel="noreferrer"
                                className={styles.link}
                            >
                                ISSN International Center
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://archive.org/details/GeneralIndex"
                                target="_blank"
                                rel="noreferrer"
                                className={styles.link}
                            >
                                Internet Archive
                            </a>
                        </li>
                        <li>Web crawls</li>
                        <li>Subject-area and institutional repositories</li>
                    </ul>
                    <p>
                        If you find errors in the data, it is likely an upstream error that
                        needs to be addressed with OpenAlex directly. You can submit data
                        corrections to OpenAlex via their support form.
                    </p>
                    <p>
                        We are also using data from the Center for Measuring University
                        Performance (MUP). MUP provides a well-curated, longitudinal, and
                        broad source of data about universities that draws from public
                        sources and also includes unique data sets.
                    </p>
                </div>

                <div className={styles.block}>
                    <h2>Current State</h2>
                    <p>
                        The{" "}
                        <a
                            href="https://gt-msi-diversifind.azuremicroservices.io/"
                            target="_blank"
                            rel="noreferrer"
                            className={styles.link}
                        >
                            current CollabNext tool
                        </a>{" "}
                        is a very rough proof-of-concept. We are developing future
                        versions, moving from alpha to beta to production over the next
                        three years thanks to funding from NSF. We are part of the{" "}
                        <a
                            href="https://www.proto-okn.net/"
                            target="_blank"
                            rel="noreferrer"
                            className={styles.link}
                        >
                            Prototype Open Knowledge Network
                        </a>
                        .
                    </p>
                </div>

                <div className={styles.block}>
                    <h2>Data and Methodology</h2>
                    <p>
                        All of this MUP data is at the institution level, not the
                        individual researcher level. As CollabNext develops, we plan to
                        add other open data sources—especially those that address gaps in
                        OpenAlex for underrepresented researchers.
                    </p>
                    <p>
                        We are also interested in connecting to research grants data
                        (federal, foundations, state-level, etc.), as it can provide
                        earlier indicators of researcher interests. Patent and startup
                        company data could also add translational-research perspectives.
                        Additionally, we use RDF and RDF-star triples from SemOpenAlex
                        to facilitate linking with other knowledge graphs in the
                        Proto-OKN.
                    </p>
                </div>
            </section>
        </div>
    );
};

export default DataSources;
