import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Chat from '../components/chat/ChatThread';
import Analytics from '../components/analytics/LockedAnalytics';
import TrialCounter from '../components/cards/TrialCounter';
import PaywallModal from '../components/analytics/PaywallModal';
import TopicCard from '../components/cards/TopicCard';
import Auth from '../features/auth/index';
import Study from '../features/study/index';

const Routes = () => {
  return (
    <Router>
      <Switch>
        <Route path="/" exact component={Chat} />
        <Route path="/analytics" component={Analytics} />
        <Route path="/trial-counter" component={TrialCounter} />
        <Route path="/paywall" component={PaywallModal} />
        <Route path="/topics" component={TopicCard} />
        <Route path="/auth" component={Auth} />
        <Route path="/study" component={Study} />
      </Switch>
    </Router>
  );
};

export default Routes;