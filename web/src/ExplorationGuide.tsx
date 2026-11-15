import {ArrowRight} from 'lucide-react';
import './exploration-guide.css';

export interface ExplorationGuideProps {
  regionName: string;
  onChooseArea: () => void;
  onSeason: () => void;
  onAnomalies: () => void;
  onEvidence: () => void;
}

export default function ExplorationGuide({regionName, onChooseArea, onSeason, onAnomalies, onEvidence}: ExplorationGuideProps) {
  return <details className="exploration-guide">
    <summary><strong>How to read this record</strong><span>From an area to an evidence-backed observation</span></summary>
    <ol>
      <li><button type="button" onClick={onChooseArea}>Choose your area <ArrowRight size={14} aria-hidden="true"/></button><p>Start with {regionName} or choose another area and date range. Check which spatial scope each chart uses.</p></li>
      <li><button type="button" onClick={onSeason}>Read the historical season <ArrowRight size={14} aria-hidden="true"/></button><p>See when recorded activity has usually been higher. The seasonal summary is historical, not a forecast.</p></li>
      <li><button type="button" onClick={onAnomalies}>Inspect unusual weeks <ArrowRight size={14} aria-hidden="true"/></button><p>Open a flagged week to inspect its observations. A flag describes a historical comparison, not hazard severity.</p></li>
      <li><button type="button" onClick={onEvidence}>Check the evaluation <ArrowRight size={14} aria-hidden="true"/></button><p>Compare the conversion with Aqua. For a particular week, open its calendar square to inspect sensor counts and download the evidence.</p></li>
    </ol>
  </details>;
}
