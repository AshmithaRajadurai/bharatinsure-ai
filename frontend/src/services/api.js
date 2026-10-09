/**
 * BharatInsure AI API Client Service
 */

const API_BASE_URL = "http://127.0.0.1:8000";

export async function sendChatMessage({
  message,
  sessionId = "default-session",
  language = "auto",
  modelPreference = "api",
  inputType = "text"
}) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      language,
      model_preference: modelPreference,
      input_type: inputType
    })
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server responded with status ${response.status}`);
  }

  return response.json();
}

export async function uploadSpeechAudio(audioBlob, hintLanguage = "auto") {
  const formData = new FormData();
  formData.append("audio_file", audioBlob, "recording.wav");
  formData.append("hint_language", hintLanguage);

  const response = await fetch(`${API_BASE_URL}/speech-to-text`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Speech recognition upload failed");
  }

  return response.json();
}

export async function requestTextToSpeech(text, language = "en") {
  const response = await fetch(`${API_BASE_URL}/text-to-speech`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language })
  });

  if (!response.ok) {
    throw new Error("Text-to-speech request failed");
  }

  return response.json();
}

export async function detectLanguage(text) {
  const response = await fetch(`${API_BASE_URL}/detect-language`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  });
  return response.json();
}

export async function retrieveDocuments(query, sessionId = "default-session") {
  const response = await fetch(`${API_BASE_URL}/retrieve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId, top_k: 4 })
  });
  return response.json();
}

export async function uploadInsuranceDocument(file, sessionId = "default-session") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", sessionId);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
  }

  return response.json();
}

export async function getCurrentDocument(sessionId = "default-session") {
  const response = await fetch(`${API_BASE_URL}/documents/current?session_id=${encodeURIComponent(sessionId)}`);
  if (!response.ok) {
    return { active: false };
  }
  return response.json();
}

export async function removeCurrentDocument(sessionId = "default-session") {
  const response = await fetch(`${API_BASE_URL}/documents/current?session_id=${encodeURIComponent(sessionId)}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new Error("Failed to remove document");
  }
  return response.json();
}
