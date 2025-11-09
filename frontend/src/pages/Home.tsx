import { useKindeAuth } from "@kinde-oss/kinde-auth-react";
import { Song } from "../types";
import { Input } from "../components/ui/input";
import { fetchAllTracks } from "../api/songs";
import { useState, useEffect } from "react";
import FileUpload from "../components/FileUpload";
import { useNavigate } from "react-router-dom";

const Home = () => {
  const { login, register, user, isAuthenticated, isLoading, logout } =
    useKindeAuth();
  const [allTracks, setAllTracks] = useState<{ id: string; name: string }[]>(
    []
  );
  const navigate = useNavigate();

  useEffect(() => {
    fetchAllTracks().then((data: { id: string; name: string }[]) => {
      console.log(data);
      setAllTracks(data);
    });
  }, []);

  return (
    <>
      {isAuthenticated ? (
        <>
          <h1 className="text-4xl font-bold">Hello {user?.givenName}</h1>
          <FileUpload />
        </>
      ) : (
        <h1 className="text-4xl font-bold">Hello World</h1>
      )}
      <Input type="text" placeholder="Search" />
      {allTracks.map((track: { id: string; name: string }) => (
        <div key={track.id}>
          <div>{track.name}</div>
          <button onClick={() => navigate(`/track/${track.id}`)}>
            {track.name}
          </button>
        </div>
      ))}
    </>
  );
};

export default Home;
