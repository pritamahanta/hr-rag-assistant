const NETWORK_ERROR_PATTERN = /failed to fetch|network error|load failed|fetch failed|network request failed/i;
const TECHNICAL_ERROR_PATTERN = /internal server error|service unavailable|bad gateway|gateway timeout|http\s*\d{3}|status code|typeerror|syntaxerror|referenceerror|err_/i;

export function createApiError(message, status) {
  const error = new Error(message);
  error.status = status;
  return error;
}

export function getUserFacingError(error, context) {
  console.error(`[HR Policy Assistant] ${context} failed`, error);

  const status = error?.status;
  const technicalMessage = error instanceof Error ? error.message : String(error);

  if (NETWORK_ERROR_PATTERN.test(technicalMessage)) {
    if (context === "upload") {
      return "We couldn't upload that policy document. Please try again.";
    }

    if (context === "delete") {
      return "We couldn't remove that policy document. Please try again.";
    }

    return "We couldn't reach the HR policy service right now. Please try again in a moment.";
  }

  if (status === 502 || status === 503 || status === 504) {
    if (context === "upload") {
      return "We couldn't upload that policy document. Please try again.";
    }

    if (context === "delete") {
      return "We couldn't remove that policy document. Please try again.";
    }

    return "The HR policy service is temporarily unavailable. Please try again shortly.";
  }

  if (context === "upload") {
    if (status >= 500 || TECHNICAL_ERROR_PATTERN.test(technicalMessage)) {
      return "We couldn't upload that policy document. Please try again.";
    }
  }

  if (context === "delete") {
    if (status >= 500 || TECHNICAL_ERROR_PATTERN.test(technicalMessage)) {
      return "We couldn't remove that policy document. Please try again.";
    }
  }

  if (status === 400 || status === 404) {
    if (!TECHNICAL_ERROR_PATTERN.test(technicalMessage)) {
      return technicalMessage;
    }
  }

  if (status >= 500 || TECHNICAL_ERROR_PATTERN.test(technicalMessage)) {
    return "Something went wrong while processing your request. Please try again.";
  }

  if (context === "upload") {
    return "We couldn't upload that policy document. Please try again.";
  }

  if (context === "delete") {
    return "We couldn't remove that policy document. Please try again.";
  }

  return "Something went wrong while processing your request. Please try again.";
}
