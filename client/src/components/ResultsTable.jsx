import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import * as XLSX from "xlsx";
import { Link } from "react-router-dom";

function downloadExcel(data) {
  const ws = XLSX.utils.json_to_sheet(data); // Convierte los datos JSON a una hoja
  const wb = XLSX.utils.book_new(); // Crea un libro de trabajo
  XLSX.utils.book_append_sheet(wb, ws, "Optimized Data"); // Añade la hoja al libro
  XLSX.writeFile(wb, "optimized_data.xlsx"); // Descarga el archivo Excel
}

export function ResultsTable() {
  const location = useLocation();
  const { optimizedData } = location.state || {}; // Recibimos los datos optimizados

  // Verificar que optimizedData es un objeto y tiene la clave "optimized_excel_file"
  if (!optimizedData || !optimizedData.optimized_excel_file) {
    return <p>No optimized data available.</p>;
  }

  // Extraer las columnas del objeto
  const columns = Object.keys(optimizedData.optimized_excel_file);
  const rowsLength = optimizedData.optimized_excel_file[columns[0]].length;

  // Convertir los datos en un formato adecuado para la tabla
  const transformedData = Array.from({ length: rowsLength }, (_, index) => {
    const row = {};
    columns.forEach((col) => {
      row[col] = optimizedData.optimized_excel_file[col][index];
    });
    return row;
  });

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-2 text-center">Optimized Results</h2>
      <div className="flex justify-center items-center max-w-xl mx-auto pb-3">
        <button
          onClick={() => downloadExcel(transformedData)}
          className="bg-green-600 px-3 py-2 rounded-l-lg mr-0.5 w-52"
        >
          Download Excel
        </button>
        <Link to="/user-welcome">
          <button className="bg-white text-black px-3 py-2 rounded-r-lg ml-0.5 w-52">
            Enter a new dataset
          </button>
        </Link>
      </div>
      {/*
      
      <div className="overflow-x-auto">
        <table className="table-auto w-1/2 border mx-auto">
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
            {transformedData.map((row, index) => (
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
      */}
    </div>
  );
}
