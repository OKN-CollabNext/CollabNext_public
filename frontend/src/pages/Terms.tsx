import styles from "../styles/Terms.module.css";

const Terms = () => {
    return (
        <div className={styles.container}>
            <section className={styles.heroSection}>
                <h1>Terms and Conditions</h1>
            </section>

            <section className={styles.mainContent}>
                <ol className={styles.termList}>
                    <li>
                        This web application is free to use.
                    </li>
                    <li>
                        We would greatly appreciate your feedback and suggestions for
                        improvement.
                    </li>
                    <li>
                        Our data sources are described in more detail on our Data Sources
                        page.
                    </li>
                    <li>
                        Our technology stack is described in more detail on our Technology
                        page.
                    </li>
                    <li>
                        The tool was developed as a public open-source project hosted on
                        github.com and is released under the MIT License.
                    </li>
                    <li>
                        The text of this License is included below for reference:
                    </li>
                </ol>

                <div className={styles.licenseBlock}>
                    <p>MIT License</p>
                    <p>Copyright (c) 2021 Georgia Tech Research Corporation</p>
                    <p>
                        Permission is hereby granted, free of charge, to any person
                        obtaining a copy of this software and associated documentation
                        files (the &quot;Software&quot;), to deal in the Software
                        without restriction...
                    </p>
                    <p>
                        THE SOFTWARE IS PROVIDED &quot;AS IS&quot;, WITHOUT WARRANTY OF
                        ANY KIND, EXPRESS OR IMPLIED...
                    </p>
                </div>
            </section>
        </div>
    );
};

export default Terms;
