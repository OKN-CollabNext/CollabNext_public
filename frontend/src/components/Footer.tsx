import React from 'react';
import { Link } from 'react-router-dom';

import { Flex, Text } from '@chakra-ui/react';

const Footer = () => {
  return (
    <Flex alignItems={'center'} justifyContent={'center'} height={'11vh'}>
      {[
        {text: 'Contact Us', href: '/contact'},
        {text: 'Terms and Conditions', href: '/terms'},
        {text: 'Help', href: '/help'},
        {text: 'Provide Feedback', href: '/feedback'},
      ].map(({text, href}) => (
        <Text
          key={text}
          fontSize={{base: '8px', lg: '16px'}}
          mr={{base: '1.3rem', lg: '2.5rem'}}
          color='#000000'
        >
          <Link to={href}>{text}</Link>
        </Text>
      ))}
    </Flex>
  );
};

export default Footer;
