function QueryPanel({ question, setQuestion, onAsk, loading }) {
    return (
        <section className="query-panel">
            <form onSubmit={onAsk} className="query-form">
                <input
                    type="text"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Ask about HR policies..."
                    className="query-input"
                />

                <button
                    type="submit"
                    disabled={loading}
                    className="send-button"
                    aria-label={loading ? "Thinking" : "Send question"}
                >
                    {loading ? "..." : <span aria-hidden="true">&#8593;</span>}
                </button>
            </form>
        </section>
    );
}

export default QueryPanel;