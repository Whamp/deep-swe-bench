import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App";
import Overview from "./pages/overview";
import RunDetail from "./pages/run-detail";
import Compare from "./pages/compare";
import Leaderboard from "./pages/leaderboard";
import Trajectory from "./pages/trajectory";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<App />}>
            <Route index element={<Overview />} />
            <Route path="run/:runId" element={<RunDetail />} />
            <Route path="leaderboard" element={<Leaderboard />} />
            <Route path="compare" element={<Compare />} />
            <Route path="trajectory" element={<Trajectory />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
