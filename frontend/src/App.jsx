import { useState } from "react";
import QueryPanel from "./components/QueryPanel";
import AnswerPanel from "./components/AnswerPanel";
import DocumentManager from "./components/DocumentManager";

function App() {
  const [role, setRole] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleAsk(event) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      return;
    }

    setLoading(true);
    setAnswer("");
    setCitations([]);

    try {
      const response = await fetch("http://127.0.0.1:8000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Role": "employee",
        },
        body: JSON.stringify({
          question: trimmedQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Query failed.");
      }

      setAnswer(data.answer);
      setCitations(data.citations);
    } catch (error) {
      setAnswer(error.message);
    } finally {
      setLoading(false);
    }
  }
  function goHome() {
    setRole(null);
    setQuestion("");
    setAnswer("");
    setCitations([]);
  }

  if (role === "employee") {
    return (
      <main className="min-h-screen bg-gray-100">
        <div className="mx-auto max-w-4xl px-6 py-6">
          <button
            onClick={goHome}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            ← Back
          </button>

          <header className="mt-8">
            <h1 className="text-3xl font-bold text-gray-900">
              Employee HR Assistant
            </h1>

            <p className="mt-2 text-base text-gray-600">
              Ask questions based on the available HR policies.
            </p>
          </header>

          <QueryPanel
            question={question}
            setQuestion={setQuestion}
            onAsk={handleAsk}
            loading={loading}
          />

          <AnswerPanel answer={answer} citations={citations} />
        </div>
      </main>
    );
  }

  if (role === "admin") {
    return (
      <main className="min-h-screen bg-gray-100">
        <div className="mx-auto max-w-4xl px-6 py-6">
          <button
            onClick={goHome}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            ← Back
          </button>

          <header className="mt-8">
            <h1 className="text-3xl font-bold text-gray-900">
              Admin Dashboard
            </h1>

            <p className="mt-2 text-base text-gray-600">
              Manage HR policies and ask policy questions.
            </p>
          </header>

          <DocumentManager />

          <QueryPanel
            question={question}
            setQuestion={setQuestion}
            onAsk={handleAsk}
            loading={loading}
          />

          <AnswerPanel answer={answer} citations={citations} />
        </div>
      </main>
    );
  }
  return (
    <main className="min-h-screen bg-gray-100">
      <div className="mx-auto max-w-4xl px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900">
          HR Policy Assistant
        </h1>

        <p className="mt-2 text-gray-600">
          Select how you want to access the assistant.
        </p>

        <section className="mt-8 rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900">
            Continue as
          </h2>

          <div className="mt-6 flex gap-4">
            <button
              onClick={() => setRole("employee")}
              className="rounded-lg bg-gray-900 px-6 py-3 text-white hover:bg-gray-800"
            >
              Employee
            </button>

            <button
              onClick={() => setRole("admin")}
              className="rounded-lg border border-gray-300 bg-white px-6 py-3 text-gray-900 hover:bg-gray-50"
            >
              Admin
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}

export default App;