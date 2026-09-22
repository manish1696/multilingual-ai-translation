import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./layout";
import Home from "./pages/Home";
import Results from "./pages/Results";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/results" element={<Results />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
