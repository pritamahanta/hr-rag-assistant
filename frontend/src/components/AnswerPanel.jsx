function AnswerPanel({ answer, citations }) {
  return (
    <section className="mt-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
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

          <div className="mt-3 space-y-2">
            {citations.map((citation, index) => (
              <div
                key={`${citation.document}-${citation.section}-${citation.page}-${index}`}
                className="flex gap-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-200 text-xs font-semibold text-gray-700">
                  {index + 1}
                </span>

                <div className="min-w-0">
                  <p className="font-medium text-gray-900">
                    {citation.document}
                  </p>

                  <p className="mt-1 text-sm leading-5 text-gray-600">
                    {citation.section || "Section unavailable"}
                  </p>

                  {citation.page !== "" && (
                    <p className="mt-1 text-xs text-gray-500">
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