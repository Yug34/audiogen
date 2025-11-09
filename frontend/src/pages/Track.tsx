import { useParams } from "react-router-dom";

const Track = () => {
  const { id } = useParams();

  return (
    <div>
      <h1>Track {id}</h1>
    </div>
  );
};

export default Track;
