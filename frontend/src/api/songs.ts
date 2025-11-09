import { Song } from "../types";

const fetchAllTracks = async (): Promise<{ id: string; name: string }[]> => {
  const response = await fetch(
    `${import.meta.env.VITE_API_URL}/api/v1/allTracks`
  );
  const data = await response.json();
  return data as { id: string; name: string }[];
};

const fetchTrackById = async (id: string): Promise<Song> => {
  const response = await fetch(
    `${import.meta.env.VITE_API_URL}/api/v1/tracks/${id}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch track with id ${id}`);
  }

  const data = await response.json();
  return data as Song;
};

export { fetchAllTracks, fetchTrackById };
