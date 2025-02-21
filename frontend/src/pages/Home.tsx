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
  'CollabNext is part of the the Prototype Open Knowledge Network. We are developing a knowledge graph with entities consisting of people, organizations, and research topics. We are adopting an intentional design approach, initially prioritizing HBCUs and emerging researchers in a deliberate effort to counterbalance the Matthew effect, a naturally accumulated advantage of well-resourced research organizations.';

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
    <Box w={{lg: '700px'}} mx='auto' mt='1rem'>
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
        </Text>
      </Box>

      <Text
        pl={{base: '1rem', lg: 0}}
        fontFamily='DM Sans'
        fontSize={{lg: '22px'}}
        color='#000000'
        marginTop={{lg:'50px'}}
      >
        What are you searching for?
      </Text>

      <Box
        background='linear-gradient(180deg, #003057 0%, rgba(0, 0, 0, 0.5) 100%)'
        borderRadius={{lg: '6px'}}
        px={{base: '1.5rem', lg: '2.5rem'}}
        py={{base: '1.5rem', lg: '2rem'}}
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
            navigate(
              `search?institution=${institution}&type=${type}&topic=${topic}&researcher=${researcher}`,
            );
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
                  <Box key={text}>
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
                                fontSize={{lg: '20px'}}
                                textAlign={'center'}
                                list='institutions'
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
