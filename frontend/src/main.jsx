import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import App from './App.jsx'
import BusDashboard from './pages/BusDashboard.jsx'
import ManageRoute from './pages/ManageRoute.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<BusDashboard />} />
          <Route path="manage-route" element={<ManageRoute />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
