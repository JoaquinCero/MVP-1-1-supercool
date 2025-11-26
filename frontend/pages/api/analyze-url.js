// frontend/pages/api/analyze-url.js

// ¡ESTA ES LA URL OBTENIDA DE RENDER!
const RENDER_API_URL = "https://aeo-api-backend.onrender.com"; 

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ message: 'Method Not Allowed' });
    }

    const { url } = req.body;

    try {
        // Llama a Render
        const apiResponse = await fetch(`${RENDER_API_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_url: url }),
        });

        const data = await apiResponse.json();
        res.status(apiResponse.status).json(data);

    } catch (error) {
        console.error("Error calling Render API:", error);
        res.status(500).json({ error: 'Fallo interno al analizar la URL.' });
    }
}