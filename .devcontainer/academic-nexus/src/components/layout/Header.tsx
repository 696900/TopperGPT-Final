import React from 'react';
import { useTheme } from '../../hooks/useTheme';
import { Link } from 'react-router-dom';

const Header: React.FC = () => {
    const { colors } = useTheme();

    return (
        <header style={{ backgroundColor: colors.surface, padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h1 style={{ color: colors.onSurface, fontFamily: 'Inter', fontSize: '24px', fontWeight: '600' }}>
                Academic Nexus
            </h1>
            <nav>
                <Link to="/" style={{ color: colors.onSurface, marginRight: '16px', textDecoration: 'none' }}>Home</Link>
                <Link to="/about" style={{ color: colors.onSurface, textDecoration: 'none' }}>About</Link>
            </nav>
        </header>
    );
};

export default Header;