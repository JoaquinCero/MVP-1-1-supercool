// Reemplaza el contenido del archivo principal (index.tsx o page.tsx)

import React, { useState } from 'react';

// Esta es la ruta al proxy de Vercel que configuraste previamente
const API_PROXY_URL = '/api/analyze-url'; 

// Definición de las estructuras de datos del JSON final
interface Rival {
  posicion: number;
  empresa: string;
  url: string;
  score: number;
  detalles: string;
  es_usuario: boolean;
  descripcion_mercado: string;
  pais: string;
  oportunidades?: string[];
}

interface AnalysisResult {
  puntuacion: number;
  diagnostico: string; // Mensaje comparativo completo
  industria: string;
  ranking_completo: Rival[];
  error?: boolean;
}

const AEOAnalyzer: React.FC = () => {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 1. Lógica de Envío
  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError('');

    if (!url || !url.startsWith('http')) {
      setError('Por favor, ingresa una URL válida (ej. https://ejemplo.com)');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(API_PROXY_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      const data: AnalysisResult = await response.json();
      
      if (response.status !== 200 || data.error) {
        setError(`Análisis fallido: ${data.diagnostico || 'Error desconocido. Revisa tu consola para más detalles.'}`);
      } else {
        setResult(data);
      }
      
    } catch (err) {
      setError('Error de conexión con el servicio de análisis. Verifica la URL de Render en el proxy.');
    } finally {
      setLoading(false);
    }
  };

  // 2. Componente de Ranking de Rivales
  const renderRankingTable = () => {
    if (!result || !result.ranking_completo || result.ranking_completo.length === 0) return null;

    return (
      <div className="mt-8">
        <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
            Ranking de Competitividad ({result.industria})
        </h3>
        <div className="overflow-x-auto shadow-md rounded-lg">
          <table className="min-w-full bg-white text-left text-sm">
            <thead className="bg-gray-200">
              <tr>
                <th scope="col" className="px-4 py-3">#</th>
                <th scope="col" className="px-4 py-3">Empresa / Descripción</th>
                <th scope="col" className="px-4 py-3">PAA Score</th>
                <th scope="col" className="px-4 py-3">Razón PAA</th>
                <th scope="col" className="px-4 py-3">País</th>
              </tr>
            </thead>
            <tbody>
              {result.ranking_completo.map((rival) => (
                <tr 
                  key={rival.url} 
                  className={`border-b ${rival.es_usuario ? 'bg-purple-100 font-bold' : 'hover:bg-gray-50'}`}
                >
                  <td className="px-4 py-3 text-lg">{rival.posicion}</td>
                  <td className="px-4 py-3">
                    {rival.empresa} 
                    {rival.es_usuario && <span className="ml-2 text-purple-600">(Tú)</span>}
                    <div className='text-xs text-gray-500 font-normal'>{rival.descripcion_mercado}</div>
                  </td>
                  <td className="px-4 py-3 text-2xl">{rival.score}</td>
                  <td className="px-4 py-3 text-xs">{rival.detalles}</td>
                  <td className="px-4 py-3 text-xs">{rival.pais}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };
  
  // 3. Componente de Oportunidades
  const renderOpportunities = () => {
    const user = result?.ranking_completo?.find(r => r.es_usuario);
    if (!user || !user.oportunidades || user.oportunidades.length === 0) return null;

    return (
      <div className="mt-8 p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded-lg">
        <h3 className="text-xl font-bold text-yellow-800 flex items-center">
            Oportunidades de Mejora Clave
        </h3>
        <ul className="list-disc list-inside mt-3 text-sm text-gray-700 space-y-2">
          {user.oportunidades.map((op, index) => (
            <li key={index}>{op}</li>
          ))}
        </ul>
      </div>
    );
  };


  // 4. ESTRUCTURA VISUAL DE LA PÁGINA
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center p-8">
      <div className="w-full max-w-5xl bg-white p-8 rounded-xl shadow-2xl mt-10">
        <h1 className="text-4xl font-extrabold text-gray-900 text-center mb-4">
          📈 Analizador AEO (AI Engine Optimization)
        </h1>
        <p className="text-xl text-gray-600 text-center mb-8">
          Descubre tu verdadera posición frente a la IA y tus rivales.
        </p>

        <form onSubmit={handleAnalyze} className="flex flex-col sm:flex-row gap-4 mb-8">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Ej: https://tudominio.com"
            className="p-3 border border-gray-400 rounded-lg text-lg flex-grow"
            required
          />
          <button
            type="submit"
            className="p-3 bg-blue-600 text-white font-bold rounded-lg text-lg hover:bg-blue-700 disabled:opacity-50 transition duration-300"
            disabled={loading}
          >
            {loading ? 'Analizando 6 sitios...' : '¡Generar Diagnóstico de Mercado!'}
          </button>
        </form>

        {error && <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">{error}</div>}

        {/* --- RESULTADOS --- */}
        {result && (
          <>
            <div className="mt-6 p-6 bg-purple-50 shadow-md rounded-lg">
              <h2 className="text-2xl font-bold text-gray-800 mb-3">Diagnóstico Ejecutivo:</h2>
              {/* Aquí se usa dangerouslySetInnerHTML para renderizar el mensaje con negritas y saltos de línea */}
              <div className="text-lg leading-relaxed whitespace-pre-line" dangerouslySetInnerHTML={{ __html: result.diagnostico.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
            </div>

            {renderOpportunities()}
            {renderRankingTable()}

            {/* Formulario de Waiting List (Tu Lead Magnet) */}
            <div className="mt-8 p-6 bg-green-50 border-l-4 border-green-500 rounded-lg">
              <h3 className="text-xl font-bold text-green-800">
                ¡Tu Análisis de Mercado está listo!
              </h3>
              <p className="mt-2 text-gray-700">
                El informe completo (AIO/GEO) incluye análisis de Embeddings y sugerencias de RAG. Únete a la lista para recibir las estrategias para superar a tus rivales.
              </p>
              <form className="mt-4 flex gap-3">
                <input 
                  type="email" 
                  placeholder="Email" 
                  className="p-2 border border-gray-300 rounded-lg flex-grow" 
                  required
                />
                <button 
                  type="submit" 
                  className="p-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition"
                >
                  Unirme a la Waitlist
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AEOAnalyzer;