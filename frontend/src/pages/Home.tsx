import {Field, Form, Formik} from 'formik';
import React, {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import * as Yup from 'yup';

import {
  Box,
  Button,
  Flex,
  FormControl,
  FormErrorMessage,
  Input,
  Select,
  SimpleGrid,
  Text,
} from '@chakra-ui/react';

import Suggested from '../components/Suggested';
import {baseUrl, handleAutofill} from '../utils/constants';

const validateSchema = Yup.object().shape({
  institution: Yup.string().notRequired(),
  type: Yup.string().notRequired(),
  topic: Yup.string().notRequired(),
  researcher: Yup.string().notRequired(),
});

const DESCRIPTION_TEXT =
  'FAIR WARNING!  This tool is still in a pre-beta stage and is being actively developed. We ask for your patience since we expect you will run into bugs, data errors, and other issues. We welcome your feedback using the link at the bottom of this page.';
const DESCRIPTION_TEXT2 =
  'CollabNext is part of the Prototype Open Knowledge Network. We are developing a knowledge graph with entities consisting of people, organizations, and research topics that can help to answer questions such as: "Who is working on what research topic and where are they?"'
const DESCRIPTION_TEXT3 = 'We are adopting an intentional design approach, initially prioritizing HBCUs and emerging researchers in a deliberate effort to counterbalance the Matthew effect, a naturally accumulated advantage of well - resourced research organizations.';

const initialValues = {
  institution: '',
  type: '',
  topic: '',
  researcher: '',
};

const Home = () => {
  const navigate = useNavigate();
  const [suggestedInstitutions, setSuggestedInstitutions] = useState([]);
  const [suggestedTopics, setSuggestedTopics] = useState([]);
  const institutionTypes = [
    'HBCU',
    'AANAPISI',
    'ANNH',
    'Carnegie R1',
    'Carnegie R2',
    'Emerging',
    'HSI',
    'MSI',
    'NASNTI',
    'PBI',
    'TCU',
  ];
  // const toast = useToast();

  console.log(suggestedTopics);
  return (
    <Box w={{lg: '800px'}} mx='auto'>
      <Box
        background='linear-gradient(180deg, #003057 0%, rgba(0, 0, 0, 0.5) 100%)'
        borderRadius={{lg: '6px'}}
        px={{base: '1.5rem', lg: '2.5rem'}}
        py={{base: '1.5rem', lg: '2rem'}}
      >
        <Text
          fontFamily='DM Sans'
          fontSize={{base: '12px', lg: '16px'}}
          color='#FFFFFF'
          lineHeight='1.6'
        >
          {DESCRIPTION_TEXT}
          <br /><br />{DESCRIPTION_TEXT2}
          <br /><br />{DESCRIPTION_TEXT3}
        </Text>
      </Box>

      <Text
        pl={{base: '1rem', lg: 0}}
        fontFamily='DM Sans'
        fontSize={{lg: '22px'}}
        color='#000000'
      >
        What are you searching for?
      </Text>

      <Box
        background='linear-gradient(180deg, #003057 0%, rgba(0, 0, 0, 0.5) 100%)'
        borderRadius={{lg: '6px'}}
        px={{base: '2rem', lg: '2rem'}}
        py={{base: '1rem', lg: '1.5rem'}}
        mt='1rem'
      >
        <Formik
          initialValues={initialValues}
          enableReinitialize
          validationSchema={validateSchema}
          onSubmit={async ({institution, type, topic, researcher}) => {
            console.log(`institution: ${institution}`);
            console.log(`type: ${type}`);
            console.log(`topic: ${topic}`);
            console.log(`researcher: ${researcher}`);
            // if (!institution && !topic && !researcher) {
            //   toast({
            //     title: 'Error',
            //     description: 'All 3 fields cannot be empty',
            //     status: 'error',
            //     duration: 8000,
            //     isClosable: true,
            //     position: 'top-right',
            //   });
            //   return;
            // }
            const params = new URLSearchParams(window.location.search);
            if (institution) params.set('institution', institution);
            if (type) params.set('type', type);
            if (topic) params.set('topic', topic);
            if (researcher) params.set('researcher', researcher);
            navigate(`search?${params.toString()}`);
          }}
        >
          {(props) => (
            <Form>
              <SimpleGrid
                columns={{base: 1, lg: 2}}
                spacing={{base: 7, lg: '90px'}}
              >
                {[
                  {text: 'Organization (eg. University)', key: 'institution'},
                  {text: 'Type', key: 'type'},
                ].map(({text, key}) => (
                  <Box key={text} w={{base: '100%', lg:'auto'}}>
                    <Field name={key}>
                      {({field, form}: any) => (
                        <FormControl
                          isInvalid={form.errors[key] && form.touched[key]}
                        >
                          {text === 'Organization (eg. University)' ? (
                            <>
                              <Input
                                variant={'flushed'}
                                focusBorderColor='white'
                                borderBottomWidth={'2px'}
                                color='white'
                                fontSize={{ lg: '20px'}}
                                textAlign={'center'}
                                list='institutions'
                                w={'100%'}
                                maxW={'100%'}
                                {...field}
                                onChange={(e) => {
                                  field.onChange(e);
                                  handleAutofill(
                                    field.value,
                                    false,
                                    setSuggestedTopics,
                                    setSuggestedInstitutions,
                                  );
                                }}
                              />
                              <Suggested
                                suggested={suggestedInstitutions}
                                institutions={true}
                              />
                            </>
                          ) : (
                            <Select
                              variant={'flushed'}
                              focusBorderColor='white'
                              borderBottomWidth={'2px'}
                              color='white'
                              fontSize={{lg: '20px'}}
                              textAlign={'center'}
                              {...field}
                              sx={{
                                textAlignLast: 'center',
                                paddingLeft: '25px'
                              }}
                            >
                              <option value='' style={{color: 'black'}}>
                                Select an institution type
                              </option>
                              {institutionTypes.map((type) => (
                                <option
                                  style={{color: 'black'}}
                                  key={type}
                                  value={type}
                                >
                                  {type}
                                </option>
                              ))}
                            </Select>
                          )}
                          <FormErrorMessage>
                            {form.errors[key]}
                          </FormErrorMessage>
                        </FormControl>
                      )}
                    </Field>
                    <Text
                      fontSize={{base: '12px', lg: '15px'}}
                      color='#FFFFFF'
                      textAlign={'center'}
                      mt='.7rem'
                    >
                      {text}
                    </Text>
                  </Box>
                ))}
              </SimpleGrid>
              <SimpleGrid
                mt={{base: '1.35rem', lg: '1rem'}}
                columns={{base: 1, lg: 2}}
                spacing={{base: 7, lg: '90px'}}
              >
                {[
                  {text: 'Topic Keyword', key: 'topic'},
                  {text: 'Researcher Name', key: 'researcher'},
                ].map(({text, key}) => (
                  <Box key={text}>
                    <Field name={key}>
                      {({field, form}: any) => (
                        <FormControl
                          isInvalid={form.errors[key] && form.touched[key]}
                        >
                          <Input
                            variant={'flushed'}
                            focusBorderColor='white'
                            borderBottomWidth={'2px'}
                            color='white'
                            fontSize={{lg: '20px'}}
                            textAlign={'center'}
                            list={key === 'topic' && 'topics'}
                            {...field}
                            onChange={
                              key === 'topic'
                                ? (e) => {
                                    field.onChange(e);
                                    handleAutofill(
                                      field.value,
                                      true,
                                      setSuggestedTopics,
                                      setSuggestedInstitutions,
                                    );
                                  }
                                : field.onChange
                            }
                          />
                          <Suggested
                            suggested={suggestedTopics}
                            institutions={false}
                          />
                          <FormErrorMessage>
                            {form.errors[key]}
                          </FormErrorMessage>
                        </FormControl>
                      )}
                    </Field>
                    <Text
                      fontSize={{base: '12px', lg: '15px'}}
                      color='#FFFFFF'
                      textAlign={'center'}
                      mt='.7rem'
                    >
                      {text}
                    </Text>
                  </Box>
                ))}
              </SimpleGrid>
              <Flex justifyContent={'flex-end'} mt={'3rem'}>
                <Button
                  width={{base: '165px', lg: '205px'}}
                  height='41px'
                  background='#000000'
                  borderRadius={{base: '4px', lg: '6px'}}
                  fontSize={{base: '13px', lg: '18px'}}
                  color='#FFFFFF'
                  fontWeight={'500'}
                  type='submit'
                >
                  Search
                </Button>
              </Flex>
            </Form>
          )}
        </Formik>
      </Box>
      <Flex justifyContent={'center'} mt='1.5rem'>
        <Button
          width={{base: '165px', lg: '205px'}}
          height='41px'
          background='linear-gradient(180deg, #003057 0%, rgba(0, 0, 0, 0.5) 100%)'
          borderRadius={{base: '4px', lg: '6px'}}
          fontSize={{base: '13px', lg: '18px'}}
          color='#FFFFFF'
          fontWeight={'500'}
          onClick={() => {
            navigate(`topic-search`);
          }}
        >
          Explore Topics
        </Button>
      </Flex>
    </Box>
  );
};

export default Home;
