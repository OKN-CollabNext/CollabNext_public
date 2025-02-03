import React from 'react';
import { Link } from 'react-router-dom';

import { Flex, Image, Text } from '@chakra-ui/react';

const Navbar = () => {
  return (
    <Flex
      px='3rem'
      justifyContent={'space-between'}
      alignItems={'center'}
      height='20vh'
    >
      <Link to='/'>
        <Flex alignItems={'center'}>
          <Image
            mr='.8rem'
            src='/favicon.png'
            w='52px'
            h='77px'
            objectFit={'cover'}
          />
          <Text
            fontFamily='DM Sans'
            fontSize='20px'
            color='#000000'
            fontWeight={'700'}
          >
            CollabNext
          </Text>
        </Flex>
      </Link>

      <Flex>
        {[
          {text: 'Home', href: '/'},
          {text: 'About Us', href: '/about'},
          {text: 'Team', href: '/team'},
          {text: 'Data Sources', href: '/data'},
          {text: 'Technology', href: '/technology'},
        ].map(({text, href}) => (
          <Text key={text} mr='2.5rem' color='#000000'>
            <Link to={href}>{text}</Link>
          </Text>
        ))}
      </Flex>
      <Text fontSize='20px' color='#000000'></Text>
    </Flex>
  );
};

export default Navbar;
