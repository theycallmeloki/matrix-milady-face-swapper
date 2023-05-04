export default async function handler(req, res) {
    try {
      // Replace this with the URL of your Python API
      const PYTHON_API_URL = "https://api.nutter.tools/sheet-data";
  
      const response = await fetch(PYTHON_API_URL);
      const data = await response.json();
  
      res.status(200).json(data);
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: "Failed to fetch sheet data" });
    }
  }
  