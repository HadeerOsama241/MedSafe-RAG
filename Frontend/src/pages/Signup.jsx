import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'


function Signup() {

  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')


  const handleSignup = (event) => {

    event.preventDefault()

    setError('')


    if (
      !name.trim() ||
      !email.trim() ||
      !password.trim() ||
      !confirmPassword.trim()
    ) {

      setError(
        'Please fill in all fields.'
      )

      return
    }


    if (password !== confirmPassword) {

      setError(
        'Passwords do not match.'
      )

      return
    }


    if (password.length < 6) {

      setError(
        'Password must be at least 6 characters.'
      )

      return
    }


    const user = {

      name: name.trim(),

      email: email.trim(),

      password: password

    }


    localStorage.setItem(
      'healthInsightAccount',
      JSON.stringify(user)
    )


    navigate('/')

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
          Create account
        </h1>


        <p className="login-subtitle">
          Create your account to start your intelligent
          health journey.
        </p>


        <form onSubmit={handleSignup}>


          <div className="form-group">

            <label>
              Full Name
            </label>

            <input
              type="text"
              placeholder="Enter your name"
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
            />

          </div>


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
              placeholder="Create a password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
            />

          </div>


          <div className="form-group">

            <label>
              Confirm Password
            </label>

            <input
              type="password"
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(event.target.value)
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

            Create Account

            <span>
              →
            </span>

          </button>


        </form>


        <p
          className="signup-link"
          style={{
            textAlign: 'center',
            marginTop: '20px',
            color: '#777285'
          }}
        >

          Already have an account?

          {' '}

          <button
            type="button"
            onClick={() => navigate('/')}
            style={{
              border: 'none',
              background: 'transparent',
              color: '#7654d6',
              fontWeight: '600',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >

            Sign In

          </button>

        </p>


        <p className="login-footer">
          HealthInsight AI Healthcare
        </p>


      </div>

    </div>

  )

}


export default Signup