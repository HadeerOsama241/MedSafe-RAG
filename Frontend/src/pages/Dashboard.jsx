import { Link } from 'react-router-dom'


function Dashboard({ userName = 'User' }) {

  return (

    <div>


      {/* ================= TOP BAR ================= */}

      <header className="topbar">

        <div>

          <span className="page-label">
            DASHBOARD
          </span>

          <h1>
            Welcome back {userName} 👋
          </h1>

          <p>
            Your intelligent health space is ready for you.
          </p>

        </div>


        <div className="top-actions">

          <button className="icon-button">
            ⌕
          </button>

          <button className="icon-button">
            ◔
          </button>

          <div className="user-avatar">
            {userName.charAt(0).toUpperCase()}
          </div>

        </div>

      </header>


      {/* ================= HERO ================= */}

      <section className="hero-card">

        <div className="hero-content">

          <span className="hero-tag">
            ✦ AI POWERED HEALTHCARE
          </span>

          <h2>

            Your health journey,

            <br />

            <span>
              smarter with AI.
            </span>

          </h2>

          <p>

            Explore trusted healthcare information,
            ask questions, and get intelligent answers
            powered by HealthInsight RAG.

          </p>


          <Link
            to="/ai-assistant"
            className="primary-button"
          >

            Start a conversation

            <span>
              →
            </span>

          </Link>

        </div>


        <div className="hero-art">

          <div className="orb orb-one"></div>

          <div className="orb orb-two"></div>

          <div className="medical-symbol">
            ✚
          </div>

          <div className="floating-card">

            <span>
              AI Status
            </span>

            <strong>
              ● Ready
            </strong>

          </div>

        </div>

      </section>


      {/* ================= OVERVIEW ================= */}

      <section className="section">

        <div className="section-heading">

          <div>

            <span className="section-label">
              OVERVIEW
            </span>

            <h2>
              Your health assistant
            </h2>

          </div>

        </div>


        <div className="stats-grid">


          {/* AI Assistant */}

          <Link
            to="/ai-assistant"
            className="stat-card"
          >

            <div className="stat-icon purple">
              ✦
            </div>

            <div>

              <span>
                AI Assistant
              </span>

              <strong>
                Ready
              </strong>

              <small>
                Ask anything
              </small>

            </div>

          </Link>


          {/* WHO Knowledge Base */}

          <Link
            to="/ai-assistant"
            className="stat-card"
          >

            <div className="stat-icon pink">
              📄
            </div>

            <div>

              <span>
                WHO Knowledge Base
              </span>

              <strong>
                Available
              </strong>

              <small>
                Search trusted information
              </small>

            </div>

          </Link>


          {/* Knowledge Base */}

          <div className="stat-card">

            <div className="stat-icon lavender">
              ⌁
            </div>

            <div>

              <span>
                Knowledge Base
              </span>

              <strong>
                Connected
              </strong>

              <small>
                RAG powered
              </small>

            </div>

          </div>


        </div>

      </section>


      {/* ================= BOTTOM SECTION ================= */}

      <section className="bottom-grid">


        {/* Quick Access */}

        <div className="recent-card">

          <div className="card-header">

            <span className="section-label">
              QUICK ACCESS
            </span>

            <h2>
              What would you like to do?
            </h2>

          </div>


          <div className="quick-actions">


            {/* AI Assistant */}

            <Link
              to="/ai-assistant"
              className="quick-item"
            >

              <div className="quick-icon">
                ✦
              </div>

              <div>

                <strong>
                  Ask AI Assistant
                </strong>

                <p>
                  Get answers from our knowledge base
                </p>

              </div>

              <span>
                →
              </span>

            </Link>


            {/* WHO Search */}

            <Link
              to="/ai-assistant"
              className="quick-item"
            >

              <div className="quick-icon pink-bg">
                📄
              </div>

              <div>

                <strong>
                  Search WHO Knowledge
                </strong>

                <p>
                  Find the five most relevant results
                </p>

              </div>

              <span>
                →
              </span>

            </Link>


          </div>

        </div>


        {/* System Status */}

        <div className="status-card">

          <div className="status-top">

            <span className="section-label">
              SYSTEM
            </span>

            <div className="online">

              <span></span>

              Online

            </div>

          </div>


          <div className="status-circle">
            ✦
          </div>


          <h2>
            Everything is ready.
          </h2>


          <p>

            Your AI healthcare assistant is ready
            whenever you need it.

          </p>


          <div className="status-line">

            <span>
              RAG System
            </span>

            <strong>
              Connected
            </strong>

          </div>

        </div>


      </section>


    </div>

  )

}


export default Dashboard