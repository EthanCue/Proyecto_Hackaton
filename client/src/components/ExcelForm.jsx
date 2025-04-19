import { useForm } from "react-hook-form";
import { optimize } from "../api/optimize.api";
import { toast } from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { useState } from 'react';

export function ExcelForm() {

  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm();
  const [loading, setLoading] = useState(false);

  const uploadedFile = watch("excel_file");

  // Determina si el archivo es válido y si el botón debe estar habilitado
  const isFileUploaded = uploadedFile && uploadedFile.length > 0;

  const onSubmit = handleSubmit(async (data) => {

    setLoading(true);

    const formData = new FormData();
    formData.append("excel_file", data.excel_file[0]);

    for (let [key, value] of formData.entries()) {
      console.log(`${key}:`, value);
    }

    try {
      const { optimizedData, pareto } = await optimize(formData); // blob
      console.log("Plan:", optimizedData);
      console.log("Pareto:", pareto);
  
      //const fileUrl = URL.createObjectURL(optimizedData);
    
      // Enviar a vista de resultados con el blob URL
      navigate("/optimal-data", {
        state: {
          //optimizedDataUrl: fileUrl,
          optimizedData,
          pareto
        },
      });
    
      toast.success("Data successfully processed", {
        position: "bottom-right",
        style: { background: "#101010", color: "#fff" },
      });
    } catch (error) {
      console.error(error);
      toast.error("Error processing data");
    } finally {
      setLoading(false);
    }
  });

  return (
    <div className="max-w-xl mx-auto pt-5">
      <form onSubmit={onSubmit}>
          <div className="flex items-center justify-center w-full">
              <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-gray-800 dark:bg-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <svg className="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                          <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
                      </svg>
                      <p className="mb-2 text-sm text-gray-500 dark:text-gray-400"><span className="font-semibold">Click to upload</span> or drag and drop</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">xlsx or xls</p>
                  </div>
                  <input id="dropzone-file" type="file" className="hidden" accept=".xlsx,.xls"{...register("excel_file", { required: true })}/>
              </label>
          </div> 
          {errors.excel_file && (<span>Upload an Excel archive</span>)}
          <div className="flex justify-center py-4">
            <button className="bg-pink-500 p-3 rounded-full w-1/2" type="submit"  disabled={loading || !isFileUploaded} >
            {loading ? "Procesando…" : "Optimize"}
            </button>
          </div>
      </form>
    </div>
  );
}
