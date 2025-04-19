import axios from "axios";

const optimizeApi = axios.create({
  baseURL: "http://127.0.0.1:8000/optimization/api/v1/",
});

export const optimize = async (data) => {
  try {
    const response = await optimizeApi.post("optimize/", data);
    return response.data;
  } catch (error) {
    console.error("Error getting optimal data:", error.response || error);
    throw error;
  }
};