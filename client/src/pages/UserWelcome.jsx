import { ExcelForm } from "../components/ExcelForm";

export function UserWelcome() {
  return (
    <div>
      <header className="pt-24 px-12">
        <div className="container mx-auto px-4">
          <h1 className="text-5xl text-center font-semibold">
            <em className="text-pink-500">Optimal Product Planification</em>
          </h1>
          <div className="container mx-auto py-12 px-4">
            <div className="text-lg text-center">
              <p className="text-2xl">
                Upload your excel with the data you want optimized
              </p>
            </div>
          </div>
        </div>
      </header>
      <ExcelForm />
    </div>
  );
}