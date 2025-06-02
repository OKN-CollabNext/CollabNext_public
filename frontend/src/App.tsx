import React from "react";
import { Routes, Route } from "react-router-dom";
import { Box, ChakraProvider } from "@chakra-ui/react";

import { themeSystem } from "./theme";

import Footer from "./components/Footer";
import Navbar from "./components/Navbar";
import NavbarMobile from "./components/NavbarMobile";
import About from "./pages/About";
import Acknowledgment from "./pages/Acknowledgment";
import ContactUs from "./pages/Contact";
import DataSources from "./pages/DataSources";
import Feedback from "./pages/Feedback";
import Help from "./pages/Help";
import Home from "./pages/Home";
import Search from "./pages/Search";
import Technology from "./pages/Technology";
import Terms from "./pages/Terms";
import TopicSearch from "./pages/TopicSearch";

function App() {
  return (
    <ChakraProvider value={themeSystem}>
      <Box display="flex" flexDirection="column" minH="100vh" overflow="hidden">
        {/* ---------- Navigation ---------- */}
        <Box flexShrink={0}>
          <Box display={{ base: "none", lg: "block" }}>
            <Navbar />
          </Box>
          <Box display={{ lg: "none" }}>
            <NavbarMobile />
          </Box>
        </Box>

        {/* ---------- Page content ---------- */}
        <Box flex={1} overflowY="auto" px={{ base: 2, lg: 4 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/technology" element={<Technology />} />
            <Route path="/search" element={<Search />} />
            <Route path="/topic-search" element={<TopicSearch />} />
            <Route path="/contact" element={<ContactUs />} />
            <Route path="/team" element={<Acknowledgment />} />
            <Route path="/feedback" element={<Feedback />} />
            <Route path="/data" element={<DataSources />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/help" element={<Help />} />
          </Routes>
        </Box>

        {/* ---------- Footer ---------- */}
        <Footer />
      </Box>
    </ChakraProvider>
  );
}

export default App;
