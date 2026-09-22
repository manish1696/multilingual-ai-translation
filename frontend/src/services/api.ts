import axios from "axios";
import type {
  EvaluationRequest, LanguagesResponse, TranslationRequest, TranslationResponse,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180_000,
  headers: { "Content-Type": "application/json" },
});

export async function fetchLanguages(): Promise<LanguagesResponse> {
  const { data } = await apiClient.get<LanguagesResponse>("/translation/languages");
  return data;
}

export async function translateText(
  payload: TranslationRequest,
): Promise<TranslationResponse> {
  const { data } = await apiClient.post<TranslationResponse>(
    "/translation/translate", payload,
  );
  return data;
}

export async function evaluateTranslation(
  payload: EvaluationRequest,
): Promise<TranslationResponse> {
  const { data } = await apiClient.post<TranslationResponse>(
    "/translation/evaluate", payload,
  );
  return data;
}

export async function checkHealth(): Promise<{ status: string }> {
  const { data } = await apiClient.get<{ status: string }>("/health");
  return data;
}
