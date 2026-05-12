import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { PrivateRoute } from '@/components/PrivateRoute';
import { AppLayout } from '@/components/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { AccountsPage } from '@/pages/AccountsPage';
import { LiabilitiesPage } from '@/pages/LiabilitiesPage';
import { PensionPage } from '@/pages/PensionPage';
import { HistoryPage } from '@/pages/HistoryPage';
import { ConfigurePage } from '@/pages/ConfigurePage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <AppLayout />
              </PrivateRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="accounts" element={<AccountsPage />} />
            <Route path="liabilities" element={<LiabilitiesPage />} />
            <Route path="pension" element={<PensionPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="configure" element={<ConfigurePage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
