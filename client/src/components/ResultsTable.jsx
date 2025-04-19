import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import * as XLSX from "xlsx";
import { Link } from "react-router-dom";

function downloadExcel(data, fileName) {
  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, fileName);
  XLSX.writeFile(wb, `${fileName}.xlsx`);
}

export function ResultsTable() {
  const location = useLocation();
  const { optimizedData } = location.state || {};
  const { pareto } = location.state || {};

  if (!location.state || !location.state.optimizedData) {
    return <p>Error: No data was passed to this page.</p>;
  }

  if (!optimizedData) {
    return <p>No optimized data available.</p>;
  }

  if (!pareto) {
    return <p>No pareto available.</p>;
  }

  const columns = Object.keys(optimizedData);
  const rowsLength = optimizedData[columns[0]].length;

  const transformedOptimized = Array.from(
    { length: rowsLength },
    (_, index) => {
      const row = {};
      columns.forEach((col) => {
        row[col] = optimizedData[col][index];
      });
      return row;
    }
  );

  let transformedPareto = [];
  let paretoColumns = [];

  if (pareto && pareto.length > 0) {
    paretoColumns = Object.keys(pareto[0]);
    const paretoRowsLength = pareto.length;

    transformedPareto = Array.from({ length: paretoRowsLength }, (_, index) => {
      const row = {};
      paretoColumns.forEach((col) => {
        row[col] = pareto[index][col];
      });
      return row;
    });
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-2 text-center">
        Optimized Results
      </h2>
      <div className="flex justify-center items-center max-w-2/3 mx-auto pb-3">
        <button
          onClick={() => downloadExcel(transformedOptimized, "optimized_data")}
          className="bg-green-600 px-3 py-2 rounded-l-lg mr-0.5 flex-1"
        >
          Download Optimized Data
        </button>
        <button
          onClick={() => downloadExcel(transformedPareto, "pareto_data")}
          className="bg-green-600 px-3 py-2 rounded-r-lg ml-0.5 flex-1"
        >
          Download Pareto
        </button>
      </div>
      <div className="flex justify-center items-center max-w-2/3 mx-auto pb-3">
        <Link to="/user-welcome" className="flex-1">
          <button className="bg-white text-black px-3 py-2 rounded-lg ml-0.5 w-full">
            Enter a new dataset
          </button>
        </Link>
      </div>
      <div className="flex justify-center space-x-4 overflow-x-auto">
        <table className="table-auto w-1/3 border">
          <thead>
            <tr>
              {columns.map((key) => (
                <th key={key} className="border px-4 py-2 bg-neutral-600">
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {transformedOptimized.map((row, index) => (
              <tr key={index} className="hover:bg-gray-500">
                {Object.values(row).map((val, i) => (
                  <td key={i} className="border px-4 py-2 text-center">
                    {val}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <table className="table-auto w-1/3 border pl-4">
          <thead>
            <tr>
              {paretoColumns.map((key) => (
                <th key={key} className="border px-4 py-2 bg-neutral-600">
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {transformedPareto.map((row, index) => (
              <tr key={index} className="hover:bg-gray-500">
                {Object.values(row).map((val, i) => (
                  <td key={i} className="border px-4 py-2 text-center">
                    {val}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}