import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Landing from './pages/Home/Landing';
import DashboardOverview from './pages/Dashboard/DashboardOverview';
import DataQualityPage from './pages/DataQuality/DataQualityPage';
import ExplorationPage from './pages/Exploration/ExplorationPage';
import AIInsightsPage from './pages/AIInsights/AIInsightsPage';
import MLReadinessPage from './pages/MLReadiness/MLReadinessPage';
import EvaluationPage from './pages/Evaluation/EvaluationPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<DashboardOverview />} />
        <Route path="/dashboard/quality" element={<DataQualityPage />} />
        <Route path="/dashboard/exploration" element={<ExplorationPage />} />
        <Route path="/dashboard/insights" element={<AIInsightsPage />} />
        <Route path="/dashboard/ml-readiness" element={<MLReadinessPage />} />
        <Route path="/dashboard/evaluate" element={<EvaluationPage />} />
      </Route>
    </Routes>
  );
}
