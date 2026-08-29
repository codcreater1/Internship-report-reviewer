// Base URL for the reviewer API. Baked at build time by Vite, so the deployed
// bundle points wherever the image was built for.
export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
