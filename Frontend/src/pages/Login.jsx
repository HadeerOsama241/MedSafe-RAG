import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import './Login.css'

function Login() {

  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')


  const handleLogin = (event) => {

    event.preventDefault()

    setError('')


    if (!email.trim() || !password.trim()) {

      setError(
        'Please enter your email and password.'
      )

      return
    }


    const savedAccount = JSON.parse(
      localStorage.getItem('healthInsightAccount') || 'null'
    )


    if (savedAccount) {

      if (
        email.trim().toLowerCase() !==
          savedAccount.email.toLowerCase() ||
        password !== savedAccount.password
      ) {

        setError(
          'Incorrect email or password.'
        )

        return
      }

    }


    localStorage.setItem(
      'healthInsightUser',
      email.trim()
    )


    navigate('/dashboard')

  }


  return (

    <div className="login-page">

      <div className="login-card">


        <div className="login-logo">
          ✦
        </div>


        <span className="section-label">
          HEALTHINSIGHT
        </span>


        <h1>
          Welcome back
        </h1>


        <p className="login-subtitle">
          Sign in to continue to your intelligent
          health space.
        </p>


        <form onSubmit={handleLogin}>


          <div className="form-group">

            <label>
              Email
            </label>

            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
            />

          </div>


          <div className="form-group">

            <label>
              Password
            </label>

            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
            />

          </div>


          {error && (

            <p className="login-error">
              {error}
            </p>

          )}


          <button
            type="submit"
            className="login-button"
          >

            Sign In

            <span>
              →
            </span>

          </button>


        </form>


        <p className="signup-text">

          Don't have an account?

          {' '}

          <Link to="/signup">
            Sign Up
          </Link>

        </p>


        <p className="login-footer">
          HealthInsight AI Healthcare
        </p>


      </div>

    </div>

  )

}


export default Login