import { BrowserRouter, Routes, Route, Navigate} from "react-router-dom";
import { UserWelcome } from "./pages/UserWelcome";
import { OptimalData } from "./pages/OptimalData";

function App() {
  return (
    <BrowserRouter>
      <div className="container mx-auto">
        <Routes>
          <Route path="/" element={<Navigate to="/user-welcome" />} />
          <Route path="/user-welcome" element={<UserWelcome />} />
          <Route path="/optimal-data" element={<OptimalData />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App