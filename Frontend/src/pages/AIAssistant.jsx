import { useState } from 'react'
import './AIAssistant.css'

function AIAssistant() {

  // =====================================================
  // STATES
  // =====================================================

  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')


  // =====================================================
  // USER
  // =====================================================

  const user = JSON.parse(
    localStorage.getItem('healthInsightAccount') || 'null'
  )

  const userName = user?.name || 'User'


  // =====================================================
  // SEND QUESTION
  // =====================================================

  const sendMessage = async (text = question) => {

    if (!text.trim() || loading) {
      return
    }

    const userQuestion = text.trim()

    // Clear input
    setQuestion('')

    // Clear global error
    setError('')

    // ===================================================
    // ADD QUESTION
    // ===================================================

    const newMessage = {
      id: Date.now(),
      question: userQuestion,
      answer: null,
      results: [],
      loading: true,
      error: null,
      confidence: 'insufficient',
      citations: [],
      refused: false,
      topDistance: null
    }

    setMessages(prev => [
      ...prev,
      newMessage
    ])

    setLoading(true)


    try {

      // =================================================
      // BACKEND REQUEST
      // =================================================

      const response = await fetch(
        'https://consoles-nickname-mechanics-dinner.trycloudflare.com/api/chat',
        {
          method: 'POST',

          headers: {
            'Content-Type': 'application/json'
          },

          body: JSON.stringify({
            question: userQuestion
          })
        }
      )


      // =================================================
      // READ RESPONSE
      // =================================================

      const data = await response.json()

      console.log(
        'BACKEND RESPONSE:',
        data
      )


      // =================================================
      // CHECK RESPONSE
      // =================================================

      if (!response.ok) {

        throw new Error(
          data.error ||
          'Something went wrong'
        )

      }


      // =================================================
      // RESULTS
      // =================================================

      const retrievedResults =
        Array.isArray(data.results)
          ? data.results
          : []


      // =================================================
      // DETERMINE REFUSAL
      // =================================================

      const isRefused =
        data.refused === true ||
        data.confidence === 'insufficient'


      // =================================================
      // UPDATE MESSAGE
      // =================================================

      setMessages(prev =>
        prev.map(message => {

          if (message.id !== newMessage.id) {
            return message
          }

          return {
            ...message,

            answer:
              data.recommendation || null,

            results:
              isRefused
                ? []
                : retrievedResults.slice(0, 5),

            confidence:
              data.confidence ||
              'insufficient',

            citations:
              Array.isArray(data.citations)
                ? data.citations
                : [],

            refused:
              isRefused,

            topDistance:
              typeof data.top_distance === 'number'
                ? data.top_distance
                : null,

            loading: false,

            error: null
          }

        })
      )

    } catch (err) {

      console.error(
        'AI Assistant Error:',
        err
      )

      const errorMessage =
        'Sorry, I could not connect to the HealthInsight backend.'


      setError(
        errorMessage
      )


      // =================================================
      // UPDATE MESSAGE WITH ERROR
      // =================================================

      setMessages(prev =>
        prev.map(message => {

          if (message.id !== newMessage.id) {
            return message
          }

          return {
            ...message,

            loading: false,

            error:
              errorMessage

          }

        })
      )

    } finally {

      setLoading(false)

    }

  }


  // =====================================================
  // ENTER KEY
  // =====================================================

  const handleKeyDown = (event) => {

    if (event.key === 'Enter') {

      event.preventDefault()

      sendMessage()

    }

  }


  // =====================================================
  // SUGGESTION
  // =====================================================

  const handleSuggestion = (text) => {

    sendMessage(text)

  }


  // =====================================================
  // GET ANSWER
  // =====================================================

  const getAnswer = (result) => {

    return (
      result?.answer ||
      result?.document_text ||
      result?.text ||
      result?.content ||
      'No result text available.'
    )

  }


  // =====================================================
  // GET PAGE
  // =====================================================

  const getPage = (result) => {

    return (
      result?.page ??
      result?.page_number ??
      result?.metadata?.page_number ??
      'N/A'
    )

  }


  // =====================================================
  // GET SECTION
  // =====================================================

  const getSection = (result) => {

    return (
      result?.section ??
      result?.metadata?.section ??
      'N/A'
    )

  }


  // =====================================================
  // GET SOURCE
  // =====================================================

  const getSource = (result) => {

    return (
      result?.source ??
      result?.source_pdf ??
      result?.metadata?.source_pdf ??
      'WHO-UHC-SDS-2019.11-eng.pdf'
    )

  }


  // =====================================================
  // GET DISTANCE
  // =====================================================

  const getDistance = (result) => {

    if (
      typeof result?.distance === 'number'
    ) {

      return result.distance

    }

    return null

  }


  // =====================================================
  // RENDER RESULT CARD
  // =====================================================

  const renderResult = (result, index) => {

    const answer =
      getAnswer(result)

    const page =
      getPage(result)

    const section =
      getSection(result)

    const source =
      getSource(result)

    const distance =
      getDistance(result)


    return (

      <div
        className="result-card"
        key={`${result?.chunk_id || index}-${index}`}
      >

        {/* RANK */}

        <div className="result-rank">

          #{index + 1}

        </div>


        {/* CONTENT */}

        <div className="result-content">


          {/* ANSWER */}

          <div className="result-answer">

            {answer}

          </div>


          {/* METADATA */}

          <div className="result-source">


            {/* PAGE */}

            <div className="source-item">

              <span className="source-icon">
                📄
              </span>

              <div>

                <small>
                  PAGE
                </small>

                <strong>
                  {page}
                </strong>

              </div>

            </div>


            {/* SECTION */}

            <div className="source-item">

              <span className="source-icon">
                📑
              </span>

              <div>

                <small>
                  SECTION
                </small>

                <strong>
                  {section}
                </strong>

              </div>

            </div>


            {/* SOURCE */}

            <div className="source-item source-name">

              <span className="source-icon">
                🔗
              </span>

              <div>

                <small>
                  SOURCE
                </small>

                <strong>
                  {source}
                </strong>

              </div>

            </div>


            {/* RELEVANCE */}

            <div className="source-item">

              <span className="source-icon">
                ≈
              </span>

              <div>

                <small>
                  RELEVANCE
                </small>

                <strong>

                  {typeof distance === 'number'
                    ? distance.toFixed(4)
                    : 'N/A'}

                </strong>

              </div>

            </div>


          </div>

        </div>

      </div>

    )

  }


  // =====================================================
  // RENDER ONE MESSAGE
  // =====================================================

  const renderMessage = (message) => {

    const hasResults =
      message.results &&
      message.results.length > 0


    return (

      <div
        className="chat-message-block"
        key={message.id}
      >


        {/* =================================================
            USER QUESTION
        ================================================= */}

        <div className="question-box">

          <div className="question-label">
            YOUR QUESTION
          </div>

          <div className="question-text">

            {message.question}

          </div>

        </div>


        {/* =================================================
            LOADING
        ================================================= */}

        {message.loading && (

          <div className="loading-box">

            <div className="ai-message-avatar">
              ✦
            </div>

            <div>

              <strong>
                HealthInsight AI
              </strong>

              <p>
                Searching the knowledge base...
              </p>

              <div className="thinking">

                <span></span>
                <span></span>
                <span></span>

              </div>

            </div>

          </div>

        )}


        {/* =================================================
            ERROR
        ================================================= */}

        {message.error && (

          <div className="ai-error">

            {message.error}

          </div>

        )}


        {/* =================================================
            AI ANSWER / REFUSAL
        ================================================= */}

        {!message.loading &&
          !message.error &&
          message.answer && (

          <div className="ai-answer-box">

            {/* AI HEADER */}

            <div className="ai-answer-header">

              <div className="ai-message-avatar">
                ✦
              </div>

              <div>

                <strong>
                  HealthInsight AI
                </strong>

                <span>
                  {message.refused
                    ? 'No Answer Available'
                    : 'AI Answer'}
                </span>

              </div>

            </div>


            {/* ANSWER */}

            <div className="ai-answer-text">

              {message.answer}

            </div>


            {/* CONFIDENCE */}

            <div className="ai-answer-meta">

              <span>
                Confidence:
              </span>

              <strong>
                {message.confidence || 'insufficient'}
              </strong>

            </div>

          </div>

        )}


        {/* =================================================
            RESULTS
        ================================================= */}

        {!message.loading &&
          !message.error &&
          hasResults && (

          <div className="results-container">


            {/* HEADER */}

            <div className="results-header">

              <div>

                <span>
                  SEARCH RESULTS
                </span>

                <h2>
                  Top 5 Relevant Results
                </h2>

              </div>


              <div className="result-count">

                {message.results.length} Results

              </div>

            </div>


            {/* RESULTS */}

            {message.results.map(
              (result, index) =>
                renderResult(result, index)
            )}

          </div>

        )}


      </div>

    )

  }


  // =====================================================
  // RETURN
  // =====================================================

  return (

    <div className="ai-page">


      {/* =================================================
          HEADER
      ================================================= */}

      <div className="ai-header">

        <div>

          <span className="ai-label">
            INTELLIGENT HEALTHCARE
          </span>

          <h1>
            HealthInsight <span>AI</span>
          </h1>

          <p>
            Search trusted healthcare knowledge
            and explore the most relevant results.
          </p>

        </div>


        <div className="ai-online">

          <span></span>

          AI Online

        </div>

      </div>


      {/* =================================================
          MAIN LAYOUT
      ================================================= */}

      <div className="ai-layout">


        {/* =================================================
            CHAT CARD
        ================================================= */}

        <div className="ai-chat-card">


          {/* =================================================
              TOP BAR
          ================================================= */}

          <div className="ai-chat-top">

            <div className="ai-chat-title">

              <div className="ai-big-icon">
                ✦
              </div>

              <div>

                <strong>
                  HealthInsight AI
                </strong>

                <p>
                  Retrieval-Augmented Generation
                </p>

              </div>

            </div>


            <div className="ai-badge">
              TOP 5 RESULTS
            </div>

          </div>


          {/* =================================================
              CONVERSATION
          ================================================= */}

          <div className="ai-conversation">


            {/* WELCOME */}

            {messages.length === 0 &&
              !error && (

              <div className="ai-welcome">

                <div className="ai-welcome-icon">
                  ✦
                </div>

                <h2>
                  Hi {userName}, how can I help?
                </h2>

                <p>
                  Ask a healthcare question and
                  get the most relevant results
                  from the trusted WHO knowledge base.
                </p>

              </div>

            )}


            {/* ALL MESSAGES */}

            {messages.map(
              message =>
                renderMessage(message)
            )}


            {/* GLOBAL ERROR */}

            {error && messages.length === 0 && (

              <div className="ai-error">
                {error}
              </div>

            )}

          </div>


          {/* =================================================
              SUGGESTIONS
          ================================================= */}

          <div className="ai-suggestions">

            <span className="suggestion-title">
              Try asking
            </span>


            <div className="suggestion-buttons">


              <button
                onClick={() =>
                  handleSuggestion(
                    'What is medication safety?'
                  )
                }
                disabled={loading}
              >

                💊 Medication Safety

              </button>


              <button
                onClick={() =>
                  handleSuggestion(
                    'What is medication without harm?'
                  )
                }
                disabled={loading}
              >

                🛡 Medication Without Harm

              </button>


              <button
                onClick={() =>
                  handleSuggestion(
                    'Tell me about patient safety'
                  )
                }
                disabled={loading}
              >

                ♡ Patient Safety

              </button>


            </div>

          </div>


          {/* =================================================
              INPUT
          ================================================= */}

          <div className="ai-input">

            <input

              type="text"

              value={question}

              onChange={(event) =>
                setQuestion(event.target.value)
              }

              onKeyDown={handleKeyDown}

              placeholder="Ask HealthInsight AI anything..."

              disabled={loading}

            />


            <button

              onClick={() =>
                sendMessage()
              }

              disabled={
                loading ||
                !question.trim()
              }

            >

              {loading
                ? '...'
                : '→'}

            </button>

          </div>


          {/* =================================================
              DISCLAIMER
          ================================================= */}

          <p className="ai-disclaimer">

            Results are retrieved from the trusted
            healthcare knowledge base. Always consult
            a qualified healthcare professional for
            medical advice.

          </p>

        </div>


        {/* =================================================
            RIGHT PANEL
        ================================================= */}

        <aside className="ai-info-card">


          <div className="ai-info-icon">
            ✦
          </div>


          <span className="ai-label">
            ABOUT THE SEARCH
          </span>


          <h2>
            Find the most relevant information.
          </h2>


          <p>

            HealthInsight AI uses Retrieval-Augmented
            Generation technology to search the
            trusted healthcare knowledge base.

          </p>


          <div className="ai-info-divider"></div>


          {/* TOP 5 */}

          <div className="ai-feature">

            <div className="feature-icon">
              1
            </div>

            <div>

              <strong>
                Top 5 Retrieval
              </strong>

              <small>
                Shows up to five closest results
                to your question.
              </small>

            </div>

          </div>


          {/* PAGE */}

          <div className="ai-feature">

            <div className="feature-icon">
              📄
            </div>

            <div>

              <strong>
                Page Citation
              </strong>

              <small>
                Every result shows its
                document page.
              </small>

            </div>

          </div>


          {/* SECTION */}

          <div className="ai-feature">

            <div className="feature-icon">
              📑
            </div>

            <div>

              <strong>
                Section
              </strong>

              <small>
                Shows the section where
                the result was found.
              </small>

            </div>

          </div>


          {/* SOURCE */}

          <div className="ai-feature">

            <div className="feature-icon">
              🔗
            </div>

            <div>

              <strong>
                Source
              </strong>

              <small>
                See which document the
                result came from.
              </small>

            </div>

          </div>


          {/* NOTE */}

          <div className="ai-info-note">

            <span>
              !
            </span>

            <p>
              Results are based only on the
              information stored in the
              HealthInsight knowledge base.
            </p>

          </div>


        </aside>


      </div>

    </div>

  )

}


export default AIAssistant