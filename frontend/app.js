const fileInput = document.getElementById("fileInput");
const uploadButton = document.getElementById("uploadButton");
const uploadStatus = document.getElementById("uploadStatus");

const questionInput = document.getElementById("questionInput");
const askButton = document.getElementById("askButton");

const answerElement = document.getElementById("answer");
const citationsElement = document.getElementById("citations");


loadDocuments();

uploadButton.addEventListener("click", async () => {
    const file = fileInput.files[0];

    if (!file) {
        uploadStatus.textContent = "Please choose a file.";
        return;
    }

    uploadButton.disabled = true;
    uploadStatus.textContent = "Uploading...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/documents/upload", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Upload failed.");
        }

        uploadStatus.textContent = `${data.filename} uploaded successfully.`;
        await loadDocuments();

    } catch (error) {
        uploadStatus.textContent = error.message;
    } finally {
        uploadButton.disabled = false;
    }
});


askButton.addEventListener("click", async () => {
    const question = questionInput.value.trim();

    if (!question) {
        answerElement.textContent = "Please enter a question.";
        citationsElement.innerHTML = "";
        return;
    }

    askButton.disabled = true;
    answerElement.textContent = "Thinking...";
    citationsElement.innerHTML = "";

    try {
        const response = await fetch("/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                question: question,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Query failed.");
        }

        answerElement.textContent = data.answer;

        if (data.citations.length === 0) {
            citationsElement.innerHTML = "";
            return;
        }

        data.citations.forEach((citation) => {
            const citationElement = document.createElement("div");
            citationElement.className = "citation";

            const section = citation.section
                ? `Section: ${citation.section}`
                : "Section: N/A";

            const page = citation.page !== ""
                ? `Page: ${citation.page}`
                : "";

            citationElement.innerHTML = `
                <strong>${citation.document}</strong>
                <span>${section}</span>
                ${page ? `<span>${page}</span>` : ""}
            `;

            citationsElement.appendChild(citationElement);
        });
    } catch (error) {
        answerElement.textContent = error.message;
        citationsElement.innerHTML = "";
    } finally {
        askButton.disabled = false;
    }
});

const documentsList = document.getElementById("documentsList");


async function loadDocuments() {
    try {
        const response = await fetch("/documents/");

        if (!response.ok) {
            throw new Error("Failed to load documents.");
        }

        const data = await response.json();

        documentsList.innerHTML = "";

        if (data.documents.length === 0) {
            documentsList.innerHTML = "<p>No documents uploaded.</p>";
            return;
        }

        data.documents.forEach((filename) => {
            const row = document.createElement("div");
            row.className = "document-row";

            row.innerHTML = `
                <span>${filename}</span>
                <button class="delete-button">Delete</button>
            `;

            row.querySelector(".delete-button").addEventListener(
                "click",
                () => deleteDocument(filename)
            );

            documentsList.appendChild(row);
        });
    } catch (error) {
        documentsList.innerHTML = `<p>${error.message}</p>`;
    }
}


async function deleteDocument(filename) {
    const confirmed = window.confirm(
        `Delete "${filename}"?`
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(
            `/documents/${encodeURIComponent(filename)}`,
            {
                method: "DELETE",
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Failed to delete document.");
        }

        await loadDocuments();
    } catch (error) {
        window.alert(error.message);
    }
}