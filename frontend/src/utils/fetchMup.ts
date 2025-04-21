// utils/fetchMup.ts
import axios from "axios";

export async function fetchMupSatScores(institution: string) {
  try {
    const { data } = await axios.post("/mup-sat-scores", {
      institution_name: institution,
    });
    return { data, error: null };
  } catch (err: any) {
    const msg =
      err.response?.data?.error ??
      `Unexpected error (${err.response?.status ?? "network"})`;
    return { data: null, error: msg };
  }
}
