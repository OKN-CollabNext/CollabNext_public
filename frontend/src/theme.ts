// src/theme.ts
import { extendTheme, type ThemeConfig } from "@chakra-ui/react";

/*
  Chakra v2 theming, battle-tested and ready to roll.
  – Works with "@chakra-ui/react": "^2.8.2"
  – Keeps your brand palette & font stack intact
*/

const config: ThemeConfig = {
  initialColorMode: "light",
  useSystemColorMode: false,
};

export const themeSystem = extendTheme({
  config,
  colors: {
    brand: {
      50: "#e3f2ff",
      100: "#b3d4ff",
      200: "#80b5ff",
      300: "#4d96ff",
      400: "#1a78ff",
      500: "#003057", // your navy
    },
  },
  fonts: {
    heading: "'DM Sans', sans-serif",
    body: "'DM Sans', sans-serif",
  },
});

export default themeSystem;
