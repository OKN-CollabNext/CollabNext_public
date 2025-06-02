import React from "react";
import { Box, Text, List } from "@chakra-ui/react";

const Help = () => (
  <Box w={{ lg: "900px" }} mx="auto" mt="1.5rem">
    <Text
      pl={{ base: ".8rem", lg: 0 }}
      fontFamily="DM Sans"
      fontSize={{ lg: "22px" }}
      color="#000000"
    >
      Help
    </Text>

    <Box
      background="linear-gradient(180deg, #003057 0%, rgba(0, 0, 0, 0.5) 100%)"
      borderRadius={{ lg: "6px" }}
      px=".8rem"
      py={{ base: "1.5rem", lg: "2rem" }}
      mt="1rem"
    >
      {/* -------- Intro copy -------- */}
      <Text
        lineHeight="24px"
        color="#FFFFFF"
        fontSize={{ base: "12px", lg: "16px" }}
      >
        This is an alpha version of the CollabNext web application. Since this
        is only an alpha version of a prototype, we are not able to provide any
        direct help or support regarding the use of this tool. However, if you
        need assistance, you are welcome to share your question or comment on
        our{" "}
        <a
          href="https://collabnext.io/feedback"
          target="_blank"
          rel="noreferrer"
          style={{ color: "cornsilk", textDecoration: "underline" }}
        >
          Feedback page
        </a>
        . Be sure to include your name and email so we can follow up.
      </Text>

      {/* -------- Tips -------- */}
      <Box mt="1.7rem">
        <Text
          mt=".45rem"
          lineHeight="24px"
          color="#FFFFFF"
          fontSize={{ base: "12px", lg: "16px" }}
        >
          Here are some tips for using this alpha version of the web
          application:
          <br />
          <br />
          <List.Root ml="1.5rem" styleType="disc">
            <List.Item>
              You can toggle the results of a search between a tabular view
              (called a List Map) or a graphical view (called Network Map).
            </List.Item>
            <List.Item>
              The Explore Topics button on the home page is an experimental,
              graphical approach to exploring the{" "}
              <a
                href="https://docs.google.com/document/d/1bDopkhuGieQ4F8gGNj7sEc8WSE8mvLZS/edit"
                target="_blank"
                rel="noreferrer"
                style={{ color: "cornsilk", textDecoration: "underline" }}
              >
                OpenAlex Topic Classification scheme
              </a>
              . Follow the link for more details on this classification process.
            </List.Item>
            <List.Item>
              Best results are achieved in the current version by searching for
              Institution and/or Topic first, and then using the listed name of
              a person to add a people filter which shows publications. We have
              implemented an auto-complete feature for Institutions and Topics,
              but it is harder to do that with researcher names.
            </List.Item>
          </List.Root>
        </Text>
      </Box>

      {/* -------- Known issues -------- */}
      <Box mt="1.7rem">
        <Text
          mt=".45rem"
          lineHeight="24px"
          color="#FFFFFF"
          fontSize={{ base: "12px", lg: "16px" }}
        >
          Our{" "}
          <a
            href="https://github.com/OKN-CollabNext/CollabNext_public"
            target="_blank"
            rel="noreferrer"
            style={{ color: "cornsilk", textDecoration: "underline" }}
          >
            GitHub project
          </a>{" "}
          has several known issues. These include:
          <br />
          <br />
          <List.Root ml="1.5rem" styleType="disc">
            <List.Item>
              Sometimes a search returns no results when there clearly should be
              some. This appears more often on the first few searches or on
              searches that return a large amount of data. You may be able to
              work around this by hitting the search button a second or third
              time.
            </List.Item>
            <List.Item>
              Counts (researchers, publications, topics) may vary from screen to
              screen because we consider sub-fields as the topic filter, but
              OpenAlex pre-computed counts use topic IDs. A given sub-field has
              multiple topic IDs which we sum, potentially double-counting some
              items.
            </List.Item>
          </List.Root>
        </Text>
      </Box>
    </Box>
  </Box>
);

export default Help;
