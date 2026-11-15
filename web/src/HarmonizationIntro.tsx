import {ArrowRight} from 'lucide-react';
import type {Week} from './types';
import ComparisonJourney from './ComparisonJourney';
import './introduction.css';

interface Props {
  weeks: Week[];
  context: string;
  loading: boolean;
  onExplore: () => void;
  onInspect: (week: Week) => void;
  onCompare: () => void;
  onValidate: () => void;
}

export default function HarmonizationIntro({weeks,context,loading,onExplore,onInspect,onCompare,onValidate}:Props) {
  return <div className="harmonization-intro">
    <div className="intro-opening">
      <div className="intro-title">
        <p className="intro-kicker">Harmonizing MODIS &amp; VIIRS</p>
        <h1 id="workspace-title">Different sensors.<br/>One reference scale.</h1>
      </div>
      <div className="intro-copy">
        <p>MODIS and VIIRS observe fire at different resolutions. Their hotspot counts cannot be compared directly.</p>
        <p>CINDERLINE converts VIIRS observations to the Aqua MODIS reference scale, creating a calendar for exploring historical burning activity.</p>
        <button className="intro-explore" onClick={onExplore}>Explore the calendar <ArrowRight size={18} aria-hidden="true"/></button>
      </div>
    </div>
    <div className="intro-example">
      {loading?<div className="intro-loading" role="status"><p>Loading an observed week to show the conversion…</p></div>:<ComparisonJourney weeks={weeks} context={context} introduction onInspect={onInspect} onCompare={onCompare} onValidate={onValidate}/>}
    </div>
  </div>;
}
