import { Link } from "react-router-dom";
import { ResultsTable } from "../components/ResultsTable";

export function OptimalData() {

  return (
    <div>
      <header className="pt-24 px-12">
        <div className="container mx-auto px-4">
          <h1 className="text-5xl text-center font-semibold">
            This are the results
          </h1>
          <div className="container mx-auto pt-4 pb-5 px-4 text-lg text-center">
            <p>
              Try these and see yout production increase and your expenses decrease
            </p>
          </div>
        </div>
      </header>
      <ResultsTable />
      <div className="flex justify-center items-center max-w-xl mx-auto pt-5">
        <Link to="/user-welcome">
          <button className="bg-white text-black px-3 py-2 rounded-lg w-52">
            Enter a new dataset
          </button>
        </Link>
      </div>
    </div>
  );
}
