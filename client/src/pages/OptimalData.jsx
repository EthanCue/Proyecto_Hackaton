import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { optimize } from "../api/optimize.api";

export function OptimalData() {
  const location = useLocation();
  const initialRecommendations = location.state?.recommendations || [];
  const normalizedDesc = location.state?.normalizedDesc;
  
  const batchSize = 3;
  const [recommendations, setRecommendations] = useState(initialRecommendations);
  const [startIndex, setStartIndex] = useState(location.state?.startIndex || 0);

  // Función para cargar el siguiente lote de recomendaciones
  const loadNextBatch = async () => {
    try {
      const newRecommendations = await optimize(normalizedDesc, startIndex + batchSize, batchSize);
      setRecommendations(newRecommendations);
      setStartIndex(startIndex + batchSize);
    } catch (error) {
      console.error("Error al cargar más recomendaciones:", error);
    }
  };

  return (
    <div>
      <header className="pt-24 px-12">
        <div className="container mx-auto px-4">
          <h1 className="text-5xl text-center font-semibold">
            We recommend these movies
          </h1>
          <div className="container mx-auto pt-4 pb-5 px-4 text-lg text-center">
            <p>
              We hope you enjoy them, if you are not satisfied with the
              recommendations, try other similar movies or try again.
            </p>
          </div>
        </div>
      </header>
      <MoviesList recommendations={recommendations} />
      <div className="flex justify-center items-center max-w-xl mx-auto pt-5">
        <button
          onClick={loadNextBatch}
          className="bg-ffpink px-3 py-2 rounded-l-lg mr-0.5 w-52"
        >
          Give me new options
        </button>
        <Link to="/user-welcome">
          <button className="bg-white text-black px-3 py-2 rounded-r-lg w-52">
            Enter a new description
          </button>
        </Link>
      </div>
    </div>
  );
}
