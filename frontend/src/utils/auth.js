import { jwtDecode } from "jwt-decode";

export function getUserIdFromToken() {
  const token = localStorage.getItem("token");
  if (!token) return null;

  try {
    const decoded = jwtDecode(token); // ✅ utilisation directe
    return decoded.user_id || null;
  } catch (error) {
    console.error("Token invalide", error);
    return null;
  }
}
