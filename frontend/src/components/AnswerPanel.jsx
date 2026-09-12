function AnswerPanel({ answer, citations }) {
  return (
    <section className="answer-panel">
      <div className="answer-heading"><span className="answer-icon">✦</span><h2>Answer</h2></div>

      {answer ? (
        <p className="answer-copy">
          {answer}
        </p>
      ) : (
        <p className="answer-copy empty-answer">
          Ask a question to see an answer.
        </p>
      )}

      {citations.length > 0 && (
        <div className="citations">
          <h3 className="citations-heading">
            Sources
          </h3>

          <div className="citation-list">
            {citations.map((citation, index) => (
              <div
                key={`${citation.document}-${citation.section}-${citation.page}-${index}`}
                className="citation"
              >
                <span className="citation-number">
                  {index + 1}
                </span>

                <div className="min-w-0">
                  <p className="citation-document">
                    {citation.document}
                  </p>

                  <p className="citation-section">
                    {citation.section || "Section unavailable"}
                  </p>

                  {citation.page !== "" && (
                    <p className="citation-page">
                      Page {citation.page}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default AnswerPanel;