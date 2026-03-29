import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Upload from "./pages/Upload";
import Result from "./pages/Result";
import Dashboard from "./pages/Dashboard";
import Register from "./pages/Register";
import History from "./pages/History";

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <div className="app-shell">
      <video className="app-bg-video" autoPlay loop muted playsInline>
        <source src="/lung.mp4" type="video/mp4" />
      </video>
      <div className="app-bg-overlay" />

      <div className="app-content">
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Upload />
                </PrivateRoute>
              }
            />

            <Route
              path="/dashboard"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />

            <Route
              path="/result"
              element={
                <PrivateRoute>
                  <Result />
                </PrivateRoute>
              }
            />

            <Route
              path="/history"
              element={
                <PrivateRoute>
                  <History />
                </PrivateRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </div>
    </div>
  );
}

export default App;
