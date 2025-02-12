import React, { useState, useCallback } from "react";
import { Field, Form, Formik } from "formik";
import { useNavigate } from "react-router-dom";
import * as Yup from "yup";
import Suggested from "../components/Suggested";
import { handleAutofill } from "../utils/constants";
import styles from "../styles/Home.module.css";
import { FaBell, FaSearch } from "react-icons/fa";

/**
 * Reuse the new approach for topic tags in Home.
 * If you prefer a simpler approach, remove it—but here we preserve the new logic.
 */
const MAX_TOPIC_TAGS = 6;
const MAX_INPUT_LENGTH = 60;

interface TopicTagsInputProps {
  tags: string[];
  setTags: React.Dispatch<React.SetStateAction<string[]>>;
  suggestedTopics: any[];
  setSuggestedTopics: React.Dispatch<React.SetStateAction<any[]>>;
  setFieldValue: (field: string, value: any) => void;
}

const TopicTagsInput: React.FC<TopicTagsInputProps> = ({
  tags,
  setTags,
  suggestedTopics,
  setSuggestedTopics,
  setFieldValue,
}) => {
  const [inputValue, setInputValue] = useState("");

  const handleRemoveTag = useCallback(
    (tagToRemove: string) => {
      const newTags = tags.filter((t) => t !== tagToRemove);
      setTags(newTags);
      setFieldValue("topic", newTags.join(","));
    },
    [tags, setTags, setFieldValue]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    handleAutofill(e.target.value, true, setSuggestedTopics, () => { });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if ((e.key === " " || e.key === ",") && inputValue.trim()) {
      e.preventDefault();
      addTag(inputValue.trim());
    } else if (e.key === "Backspace" && !inputValue) {
      if (tags.length > 0) {
        handleRemoveTag(tags[tags.length - 1]);
      }
    }
  };

  const addTag = (newTag: string) => {
    const lowerTag = newTag.toLowerCase();
    if (tags.length < MAX_TOPIC_TAGS && !tags.includes(lowerTag)) {
      const newTags = [...tags, lowerTag];
      setTags(newTags);
      setFieldValue("topic", newTags.join(","));
    }
    setInputValue("");
  };

  const handleSuggestionClick = (suggestion: string) => {
    addTag(suggestion);
  };

  return (
    <div className={styles.topicTagsWrapper}>
      <div className={styles.topicTagsHeader}>
        <p>Topic Keywords</p>
        <p className={styles.tagInstructions}>Press Space or Comma after each tag</p>
      </div>

      <ul className={styles.tagList}>
        {tags.map((tag, index) => (
          <li key={index} className={styles.tagItem}>
            {tag}
            <span
              onClick={() => handleRemoveTag(tag)}
              className={styles.removeIcon}
            >
              &times;
            </span>
          </li>
        ))}
        {tags.length < MAX_TOPIC_TAGS && (
          <li className={styles.inputItem}>
            <input
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              className={styles.tagInput}
              placeholder="Type a keyword..."
            />
          </li>
        )}
      </ul>

      {suggestedTopics.length > 0 && (
        <div className={styles.suggestionsContainer}>
          {suggestedTopics.map((suggestion: any, idx: number) => (
            <div
              key={idx}
              className={styles.suggestionItem}
              onClick={() => handleSuggestionClick(suggestion.value)}
            >
              {suggestion.value}
            </div>
          ))}
        </div>
      )}

      <div className={styles.tagDetails}>
        <p>
          <span>{MAX_TOPIC_TAGS - tags.length}</span> tags remaining
        </p>
      </div>
    </div>
  );
};

const validateSchema = Yup.object().shape({
  institution: Yup.string().notRequired(),
  type: Yup.string().notRequired(),
  topic: Yup.string().notRequired(),
  researcher: Yup.string().notRequired(),
});

// Combined description from c371ba2
const DESCRIPTION_TEXT =
  "CollabNext is part of the Prototype Open Knowledge Network. We are developing a knowledge graph consisting of people, organizations, and research topics. Our design approach prioritizes HBCUs and emerging researchers to counterbalance the Matthew effect.";

const initialValues = {
  institution: "",
  type: "Education",
  topic: "",
  researcher: "",
};

const Home = () => {
  const navigate = useNavigate();
  const [suggestedInstitutions, setSuggestedInstitutions] = useState<any[]>([]);
  const [suggestedTopics, setSuggestedTopics] = useState<any[]>([]);
  const [topicTags, setTopicTags] = useState<string[]>([]); // new approach with multiple topics
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);

  const onSubmitHandler = (values: typeof initialValues) => {
    const { institution, type, researcher } = values;
    // turn your array of tags into a comma-separated string
    const topic = topicTags.join(",");
    navigate(
      `search?institution=${institution}&type=${type}&topic=${topic}&researcher=${researcher}`
    );
  };

  const handleInputSuggestions = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>, fieldOnChange: any) => {
      fieldOnChange(e);
      handleAutofill(
        e.target.value,
        false,
        setSuggestedTopics,
        setSuggestedInstitutions
      );
    },
    [setSuggestedTopics, setSuggestedInstitutions]
  );

  return (
    <div className={styles.container}>
      <section className={styles.heroSection}>
        <h1 className={styles.heroTitle}>CollabNext</h1>
        <p className={styles.heroSubtitle}>{DESCRIPTION_TEXT}</p>
      </section>

      <section className={styles.searchSection}>
        <h2 className={styles.searchTitle}>What are you searching for?</h2>
        <div
          className={styles.dropdownToggle}
          onClick={() => setShowSearchDropdown(!showSearchDropdown)}
        >
          <FaBell className={styles.bellIcon} />
          <span>Search Options</span>
        </div>

        {showSearchDropdown && (
          <div className={styles.dropdownContainer}>
            <Formik
              initialValues={initialValues}
              validationSchema={validateSchema}
              onSubmit={onSubmitHandler}
            >
              {({ values, setFieldValue }) => (
                <Form className={styles.searchForm}>
                  <div className={styles.inputRow}>
                    {/* Institution Field */}
                    <div className={styles.formControl}>
                      <Field name="institution">
                        {({ field }: any) => (
                          <>
                            <input
                              type="text"
                              className={styles.inputField}
                              placeholder="Organization (e.g. University)"
                              {...field}
                              maxLength={MAX_INPUT_LENGTH}
                              onChange={(e) => handleInputSuggestions(e, field.onChange)}
                            />
                            <div className={styles.charCount}>
                              {MAX_INPUT_LENGTH - field.value.length} characters remaining
                            </div>
                          </>
                        )}
                      </Field>
                    </div>

                    {/* Type Select */}
                    <div className={styles.formControl}>
                      <Field name="type">
                        {({ field }: any) => (
                          <select {...field} className={styles.inputField}>
                            {/* Hard-coded sample from c371ba2; adapt as needed */}
                            <option value="Education">HBCU</option>
                          </select>
                        )}
                      </Field>
                    </div>
                  </div>

                  <div className={styles.inputRow}>
                    {/* New multi-topic input */}
                    <div className={styles.formControl}>
                      <TopicTagsInput
                        tags={topicTags}
                        setTags={setTopicTags}
                        suggestedTopics={suggestedTopics}
                        setSuggestedTopics={setSuggestedTopics}
                        setFieldValue={setFieldValue}
                      />
                    </div>

                    {/* Researcher Field */}
                    <div className={styles.formControl}>
                      <Field name="researcher">
                        {({ field }: any) => (
                          <>
                            <input
                              type="text"
                              className={styles.inputField}
                              placeholder="Researcher Name"
                              {...field}
                              maxLength={MAX_INPUT_LENGTH}
                            />
                            <div className={styles.charCount}>
                              {MAX_INPUT_LENGTH - field.value.length} characters remaining
                            </div>
                          </>
                        )}
                      </Field>
                    </div>
                  </div>

                  <Field type="hidden" name="topic" />
                  <Suggested suggested={suggestedInstitutions} institutions={true} />

                  <button type="submit" className={styles.searchButton}>
                    <FaSearch className={styles.searchButtonIcon} />
                    <span>Search</span>
                  </button>
                </Form>
              )}
            </Formik>
          </div>
        )}

        <div className={styles.exploreContainer}>
          <button
            className={styles.exploreButton}
            onClick={() => navigate("topic-search")}
          >
            Explore Topics
          </button>
        </div>
      </section>
    </div>
  );
};

export default Home;
