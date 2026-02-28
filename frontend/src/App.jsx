import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Documents from "./pages/Documents";
import Summary from "./pages/Summary";
import Analysis from "./pages/Analysis";
import Negotiate from "./pages/Negotiate";
import Chat from "./pages/Chat";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <div className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/summary/:fileName" element={<Summary />} />
            <Route path="/analysis/:fileName" element={<Analysis />} />
            <Route path="/negotiate" element={<Negotiate />} />
            <Route path="/chat/:fileName" element={<Chat />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
