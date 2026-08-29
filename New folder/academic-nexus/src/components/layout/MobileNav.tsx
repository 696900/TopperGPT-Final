import React from 'react';
import { Link } from 'react-router-dom';
import { useMediaQuery } from '../../hooks/useMediaQuery';
import { useTheme } from '../../hooks/useTheme';

const MobileNav: React.FC = () => {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const { colors } = useTheme();

  return (
    <nav
      style={{
        backgroundColor: colors.surface,
        padding: '16px',
        borderRadius: '0.25rem',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)',
        display: isMobile ? 'flex' : 'none',
        flexDirection: 'column',
        position: 'fixed',
        bottom: '0',
        width: '100%',
        zIndex: 1000,
      }}
    >
      <Link to="/" style={{ color: colors.onSurface, margin: '8px 0' }}>
        Home
      </Link>
      <Link to="/topics" style={{ color: colors.onSurface, margin: '8px 0' }}>
        Topics
      </Link>
      <Link to="/analytics" style={{ color: colors.onSurface, margin: '8px 0' }}>
        Analytics
      </Link>
      <Link to="/settings" style={{ color: colors.onSurface, margin: '8px 0' }}>
        Settings
      </Link>
    </nav>
  );
};

export default MobileNav;