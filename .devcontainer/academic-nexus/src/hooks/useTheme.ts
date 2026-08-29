import { useContext } from 'react';
import { ThemeContext } from '../lib/theme';

const useTheme = () => {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  const { theme, setTheme } = context;

  return { theme, setTheme };
};

export default useTheme;