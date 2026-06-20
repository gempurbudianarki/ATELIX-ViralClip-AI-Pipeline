import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { VideoDetail } from "./pages/VideoDetail";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/video/:videoId" element={<VideoDetail />} />
      </Route>
    </Routes>
  );
}
