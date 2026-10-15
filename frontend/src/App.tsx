import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import Home from './pages/Home'
import Parcels from './pages/Parcels'
import ParcelDetail from './pages/ParcelDetail'
import Placeholder from './pages/Placeholder'

const MapPage = lazy(() => import('./pages/MapPage'))
const Analysis = lazy(() => import('./pages/Analysis'))
const Models = lazy(() => import('./pages/Models'))
const Prediction = lazy(() => import('./pages/Prediction'))
const Methodology = lazy(() => import('./pages/Methodology'))
const About = lazy(() => import('./pages/About'))
const Glossary = lazy(() => import('./pages/Glossary'))

function Lazy({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<p className="mono">Cargando módulo…</p>}>{children}</Suspense>
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="predios" element={<Parcels />} />
        <Route path="predios/:public_id" element={<ParcelDetail />} />
        <Route path="mapa" element={<Lazy><MapPage /></Lazy>} />
        <Route path="exploracion" element={<Lazy><Analysis /></Lazy>} />
        <Route path="modelos" element={<Lazy><Models /></Lazy>} />
        <Route path="prediccion" element={<Lazy><Prediction /></Lazy>} />
        <Route path="metodologia" element={<Lazy><Methodology /></Lazy>} />
        <Route path="acerca-de" element={<Lazy><About /></Lazy>} />
        <Route path="glosario" element={<Lazy><Glossary /></Lazy>} />
        <Route
          path="*"
          element={
            <Placeholder
              title="Ruta no encontrada"
              description="La página solicitada no existe en el observatorio."
              eta="Usa la navegación superior para continuar."
            />
          }
        />
      </Route>
    </Routes>
  )
}
