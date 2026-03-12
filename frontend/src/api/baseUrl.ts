const host = process.env.NEXT_PUBLIC_HOST || "localhost";
export const baseUrl = `http://${host}:8000`; // backend

const mockHost = process.env.NEXT_PUBLIC_MOCK_HOST || "localhost";
export const mockBaseUrl = `http://${mockHost}:4010`; // prism
