import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { PrivateRoute } from '@/components/PrivateRoute';
import { LoginPage } from '@/pages/LoginPage';

// Placeholder stubs — replaced by real pages in Plan 04
function DashboardPlaceholder() { return <div>Dashboard</div>; }
function AccountsPlaceholder() { return <div>Accounts</div>; }
function LiabilitiesPlaceholder() { return <div>Liabilities</div>; }
function PensionPlaceholder() { return <div>Pension</div>; }
function HistoryPlaceholder() { return <div>History</div>; }
function ConfigurePlaceholder() { return <div>Configure</div>; }

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
                <Routes>
                  <Route path="/" element={<DashboardPlaceholder />} />
                  <Route path="/accounts" element={<AccountsPlaceholder />} />
                  <Route path="/liabilities" element={<LiabilitiesPlaceholder />} />
                  <Route path="/pension" element={<PensionPlaceholder />} />
                  <Route path="/history" element={<HistoryPlaceholder />} />
                  <Route path="/configure" element={<ConfigurePlaceholder />} />
                </Routes>
              </PrivateRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
