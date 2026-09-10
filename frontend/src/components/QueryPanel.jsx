function QueryPanel({ question, setQuestion, onAsk, loading }) {
    return (
        <section className="mt-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-gray-900">
                Ask a Question
            </h2>

            <form onSubmit={onAsk} className="mt-5 flex gap-3">
                <input
                    type="text"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="How many casual leave days do employees receive?"
                    className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 outline-none focus:border-gray-500 focus:ring-1 focus:ring-gray-300"
                />

                <button
                    type="submit"
                    disabled={loading}
                    className="rounded-lg bg-gray-900 px-6 py-3 text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    {loading ? "Thinking..." : "Ask"}
                </button>
            </form>
        </section>
    );
}

export default QueryPanel;