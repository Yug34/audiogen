import { Song } from "../types";

const fetchAllTracks = async (): Promise<Song[]> => {
  const response = await fetch(
    `${import.meta.env.VITE_API_URL}/api/v1/allTracks`
  );
  const data = await response.json();
  return data as Song[];
};

export { fetchAllTracks };
