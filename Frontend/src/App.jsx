import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  Navigate,
  useNavigate
} from 'react-router-dom'

import './App.css'

import Dashboard from './pages/Dashboard'
import AIAssistant from './pages/AIAssistant'
import Login from './pages/Login'
import Signup from './pages/Signup'


function MainLayout() {

  const navigate = useNavigate()

  const user = JSON.parse(
    localStorage.getItem('healthInsightAccount') || 'null'
  )

  const isLoggedIn =
    localStorage.getItem('healthInsightUser')


  const handleLogout = () => {

    localStorage.removeItem('healthInsightUser')

    navigate('/')

  }


  if (!isLoggedIn) {

    return (
      <Navigate
        to="/"
        replace
      />
    )

  }


  return (

    <div className="app">


      {/* ================= SIDEBAR ================= */}

      <aside className="sidebar">


        {/* Logo */}

        <div className="brand">

          <div className="brand-icon">
            ✦
          </div>

          <div>

            <h2>
              HealthInsight
            </h2>

            <span>
              AI Healthcare
            </span>

          </div>

        </div>


        {/* Menu Title */}

        <div className="menu-title">
          MAIN MENU
        </div>


        {/* Navigation */}

        <nav className="nav-menu">


          {/* Dashboard */}

          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              isActive
                ? 'nav-item active'
                : 'nav-item'
            }
          >

            <span>
              ⌂
            </span>

            Dashboard

          </NavLink>


          {/* AI Assistant */}

          <NavLink
            to="/ai-assistant"
            className={({ isActive }) =>
              isActive
                ? 'nav-item active'
                : 'nav-item'
            }
          >

            <span>
              ✦
            </span>

            AI Assistant

          </NavLink>


        </nav>


        {/* ================= SIDEBAR BOTTOM ================= */}

        <div className="sidebar-bottom">


          {/* Help Card */}

          <div className="help-card">

            <div className="help-icon">
              ?
            </div>

            <div>

              <strong>
                Need help?
              </strong>

              <p>
                Ask our AI assistant
              </p>

            </div>

          </div>


          {/* Profile */}

          <div className="profile">

            <div className="avatar">

              {user?.name
                ? user.name.charAt(0).toUpperCase()
                : 'U'}

            </div>


            <div>

              <strong>
                {user?.name || 'User'}
              </strong>

              <span>
                Health Explorer
              </span>

            </div>


            <span className="dots">
              •••
            </span>

          </div>


          {/* Logout */}

          <button
            onClick={handleLogout}
            className="logout-button"
          >

            <span>
              ↪
            </span>

            Logout

          </button>


        </div>


      </aside>


      {/* ================= MAIN CONTENT ================= */}

      <main className="main-content">

        <Routes>


          {/* Dashboard */}

          <Route
            path="/dashboard"
            element={
              <Dashboard
                userName={user?.name || 'User'}
              />
            }
          />


          {/* AI Assistant */}

          <Route
            path="/ai-assistant"
            element={
              <AIAssistant />
            }
          />


          {/* Unknown Page */}

          <Route
            path="*"
            element={
              <Navigate
                to="/dashboard"
                replace
              />
            }
          />


        </Routes>

      </main>


    </div>

  )

}


/* =========================
   APP
========================= */

function App() {

  return (

    <BrowserRouter>

      <Routes>


        {/* ================= LOGIN ================= */}

        <Route
          path="/"
          element={
            <Login />
          }
        />


        {/* ================= SIGN UP ================= */}

        <Route
          path="/signup"
          element={
            <Signup />
          }
        />


        {/* ================= MAIN APP ================= */}

        <Route
          path="/*"
          element={
            <MainLayout />
          }
        />


      </Routes>

    </BrowserRouter>

  )

}


export default App