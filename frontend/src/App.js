import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Photo from "./Photo";
import Diary from "./Diary";

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Photo />} />
                <Route path="/diary" element={<Diary />} />
            </Routes>
        </Router>
    );
}

export default App;