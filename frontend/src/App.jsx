const API_URL = import.meta.env.VITE_API_URL;

import { useEffect, useRef, useState } from "react";
import QueryPanel from "./components/QueryPanel";
import AnswerPanel from "./components/AnswerPanel";
import DocumentManager from "./components/DocumentManager";

const exampleQuestions = [
  "How many casual leave days do employees receive?",
  "What is the process for requesting leave?",
  "What are the working hours and attendance rules?",
];

function MessageIcon({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H7l-4 2 1.5-4A7.5 7.5 0 1 1 20 11.5Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8 11.5h.01M12 11.5h.01M16 11.5h.01" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

function Sidebar({ role, setRole, goHome }) {
  return (
    <aside className="sidebar">
      <button className="brand" onClick={goHome} aria-label="Go to HR Policy Assistant home">
        <span className="brand-mark"><MessageIcon size={20} /></span>
        <span>HR Policy Assistant</span>
      </button>

      <div className="sidebar-content">
        <div className="role-heading">Workspace</div>
        <div className="role-switcher" role="group" aria-label="Choose workspace">
          <button className={`role-option ${role === "employee" ? "active" : ""}`} onClick={() => setRole("employee")}>
            <span className="role-icon">E</span>
            <span><strong>Employee</strong><small>Ask about HR policies</small></span>
          </button>
          <button className={`role-option ${role === "admin" ? "active" : ""}`} onClick={() => setRole("admin")}>
            <span className="role-icon">A</span>
            <span><strong>Admin</strong><small>Manage policy documents</small></span>
          </button>
        </div>
      </div>

      <div className="sidebar-footer">
        <span className="status-dot" />
        <span>Policy knowledge base online</span>
      </div>
    </aside>
  );
}

function App() {
  const [role, setRole] = useState(null);
  const [question, setQuestion] = useState("");
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const conversationEndRef = useRef(null);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation]);

  async function handleAsk(event) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      return;
    }

    const messageId = `${Date.now()}-${Math.random()}`;

    setLoading(true);
    setQuestion("");
    setConversation((currentConversation) => [
      ...currentConversation,
      {
        id: messageId,
        question: trimmedQuestion,
        answer: "",
        citations: [],
        loading: true,
      },
    ]);

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Role": role,
        },
        body: JSON.stringify({
          question: trimmedQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Query failed.");
      }

      setConversation((currentConversation) => currentConversation.map((message) => (
        message.id === messageId
          ? { ...message, answer: data.answer, citations: data.citations, loading: false }
          : message
      )));
    } catch (error) {
      setConversation((currentConversation) => currentConversation.map((message) => (
        message.id === messageId
          ? { ...message, answer: error.message, loading: false }
          : message
      )));
    } finally {
      setLoading(false);
    }
  }
  function goHome() {
    setRole(null);
    setQuestion("");
    setConversation([]);
  }

  return (
    <main className="app-shell">
      <Sidebar role={role} setRole={setRole} goHome={goHome} />
      <section className="main-content">
        {role === "admin" ? (
          <div className="content-wrap admin-content">
            <header className="page-header">
              <div><span className="eyebrow">ADMIN WORKSPACE</span><h1>Policy management</h1><p>Keep the HR knowledge base accurate and up to date.</p></div>
              <span className="header-badge">Administrator</span>
            </header>
            <DocumentManager />
          </div>
        ) : role === "employee" ? (
          <div className="content-wrap assistant-content">
            <header className="page-header">
              <div><span className="eyebrow">EMPLOYEE WORKSPACE</span><h1>How can we help?</h1><p>Ask a question about your workplace policies.</p></div>
              <span className="header-badge"><span className="status-dot" /> Online</span>
            </header>

            {conversation.length === 0 && (
              <div className="empty-state">
                <div className="empty-icon"><MessageIcon size={30} /></div>
                <h2>Your HR questions, answered.</h2>
                <p>Get clear answers from your company&apos;s HR policy documents.</p>
                <div className="example-grid">
                  {exampleQuestions.map((example) => <button key={example} onClick={() => setQuestion(example)} className="example-card"><span>{example}</span><span className="arrow">&#8599;</span></button>)}
                </div>
              </div>
            )}

            {conversation.length > 0 && (
              <div className="conversation-scroll" aria-live="polite">
                {conversation.map((message) => (
                  <article className="conversation-turn" key={message.id}>
                    <div className="user-message">
                      <span className="message-label">You</span>
                      <p>{message.question}</p>
                    </div>
                    <div className="assistant-message">
                      <div className="message-label assistant-label"><span className="assistant-dot">✦</span> HR Policy Assistant</div>
                      {message.loading ? (
                        <div className="thinking-message" role="status"><span className="thinking-indicator" /> Reviewing the relevant policy...</div>
                      ) : (
                        <AnswerPanel answer={message.answer} citations={message.citations} />
                      )}
                    </div>
                  </article>
                ))}
                <div ref={conversationEndRef} />
              </div>
            )}

            <div className="composer-area">
              <QueryPanel question={question} setQuestion={setQuestion} onAsk={handleAsk} loading={loading} />
              <p className="assistant-disclaimer">AI-generated responses may contain mistakes. Check important information against the cited policy.</p>
            </div>
          </div>
        ) : (
          <div className="welcome-state">
            <div className="empty-icon"><MessageIcon size={30} /></div>
            <span className="eyebrow">HR POLICY ASSISTANT</span>
            <h1>Welcome to your HR assistant.</h1>
            <p>Choose a workspace from the sidebar to get started.</p>
          </div>
        )}
      </section>
    </main>
  );
}

export default App;