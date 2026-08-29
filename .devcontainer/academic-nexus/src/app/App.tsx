import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider } from '../lib/theme';
import { AuthProvider } from '../features/auth';
import { ChatProvider } from '../features/chat';
import { StudyProvider } from '../features/study';
import { BillingProvider } from '../features/billing';
import Routes from './routes';
import Sidebar from '../components/layout/Sidebar';
import Header from '../components/layout/Header';
import MobileNav from '../components/layout/MobileNav';

const App = () => {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <ChatProvider>
            <StudyProvider>
              <BillingProvider>
                <div className="app-container">
                  <Sidebar />
                  <Header />
                  <MobileNav />
                  <main>
                    <Routes />
                  </main>
                </div>
              </BillingProvider>
            </StudyProvider>
          </ChatProvider>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
};

export default App;