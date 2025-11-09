import Navbar from "./components/ui/navbar";
import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Track from "./pages/Track";

export function App() {
  return (
    <div className="min-h-screen min-w-screen flex flex-col">
      <Navbar />
      <main className="w-full h-full flex flex-col items-center justify-center"></main>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/track/:id" element={<Track />} />
      </Routes>
    </div>
  );
}
