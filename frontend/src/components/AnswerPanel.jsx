function AnswerPanel({ answer, citations }) {
  return (
    <section className="mt-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900">Answer</h2>

      {answer ? (
        <p className="mt-4 whitespace-pre-wrap leading-7 text-gray-700">
          {answer}
        </p>
      ) : (
        <p className="mt-4 text-gray-500">
          Ask a question to see an answer.
        </p>
      )}

      {citations.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
            Sources
          </h3>

          <div className="mt-3 space-y-3">
            {citations.map((citation, index) => (
              <div
                key={`${citation.document}-${citation.section}-${citation.page}-${index}`}
                className="rounded-lg bg-gray-50 p-4"
              >
                <p className="font-medium text-gray-900">
                  {citation.document}
                </p>

                <p className="mt-1 text-sm text-gray-600">
                  Section: {citation.section || "N/A"}
                </p>

                {citation.page !== "" && (
                  <p className="mt-1 text-sm text-gray-600">
                    Page: {citation.page}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default AnswerPanel;