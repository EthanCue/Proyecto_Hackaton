import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import * as XLSX from 'xlsx';

export function ResultsTable({ optimizedExcelBlob }) {
  const [excelData, setExcelData] = useState([]);
  const [downloadUrl, setDownloadUrl] = useState(null);

  useEffect(() => {
    if (optimizedExcelBlob) {
      // Crear URL para descarga
      const url = URL.createObjectURL(optimizedExcelBlob);
      setDownloadUrl(url);

      // Leer el archivo con SheetJS
      const reader = new FileReader();
      reader.onload = (e) => {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const worksheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(worksheet);
        setExcelData(jsonData);
      };
      reader.readAsArrayBuffer(optimizedExcelBlob);
    }
  }, [optimizedExcelBlob]);

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        {downloadUrl && (
          <a
            href={downloadUrl}
            download="optimized_results.xlsx"
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
          >
            Download Excel
          </a>
        )}
      </div>

      <div className="overflow-x-auto shadow rounded">
        <table className="min-w-full border border-gray-300 table-auto">
          <thead className="bg-gray-100">
            <tr>
              <th className="border px-4 py-2">Product</th>
              <th className="border px-4 py-2">Period</th>
              <th className="border px-4 py-2">Production</th>
            </tr>
          </thead>
          <tbody>
            {excelData.map((row, idx) => (
              <tr key={idx}>
                <td className="border px-4 py-2">{row.product}</td>
                <td className="border px-4 py-2">{row.period}</td>
                <td className="border px-4 py-2">{row.production}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

ResultsTable.propTypes = {
  optimizedExcelBlob: PropTypes.instanceOf(Blob).isRequired,
};
