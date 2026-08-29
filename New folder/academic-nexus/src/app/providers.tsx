import React, { createContext, useContext, useState } from 'react';

// Create a context for the theme
const ThemeContext = createContext();

// Create a provider component
export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState('dark'); // Default theme

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'dark' ? 'light' : 'dark'));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Create a custom hook to use the ThemeContext
export const useTheme = () => {
  return useContext(ThemeContext);
};

// Create a context for the app state
const AppStateContext = createContext();

// Create a provider component for app state
export const AppStateProvider = ({ children }) => {
  const [state, setState] = useState({}); // Initial state

  return (
    <AppStateContext.Provider value={{ state, setState }}>
      {children}
    </AppStateContext.Provider>
  );
};

// Create a custom hook to use the AppStateContext
export const useAppState = () => {
  return useContext(AppStateContext);
};

// Export a combined provider for easy use
export const AppProviders = ({ children }) => {
  return (
    <ThemeProvider>
      <AppStateProvider>
        {children}
      </AppStateProvider>
    </ThemeProvider>
  );
};