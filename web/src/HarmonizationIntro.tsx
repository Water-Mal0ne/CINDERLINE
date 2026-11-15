import {ArrowRight} from 'lucide-react';
import type {Index,Week} from './types';
import ComparisonJourney from './ComparisonJourney';
import './introduction.css';

interface Props {
  weeks: Week[];
  context: string;
  loading: boolean;
  unavailable: boolean;
  countries: Index['regions'];
  country: string;
  onCountry: (id: string) => void;
  onExplore: () => void;
  onInspect: (week: Week) => void;
  onCompare: () => void;
  onValidate: () => void;
}

export default function HarmonizationIntro({weeks,context,loading,unavailable,countries,country,onCountry,onExplore,onInspect,onCompare,onValidate}:Props) {
  const countryName=countries.find(item=>item.id===country)?.name||'the selected country';
  return <div className="home-page">
    <header className="home-opening">
      <p className="home-kicker">Harmonizing MODIS &amp; VIIRS</p>
      <h1 id="workspace-title">Fire history, on a common scale.</h1>
      <div className="home-summary">
        <p>MODIS and VIIRS observe fire at different resolutions. Their hotspot counts cannot be compared directly. CINDERLINE converts VIIRS observations to the Aqua MODIS reference scale, creating a calendar for exploring historical burning activity.</p>
        <button className="home-explore" onClick={onExplore}>Explore the calendar <ArrowRight size={18} aria-hidden="true"/></button>
      </div>
    </header>
    <section className="home-example" aria-labelledby="home-example-title">
      <div className="home-example-header">
        <h2 id="home-example-title">Harmonization, in numbers</h2>
        <div className="home-country"><label htmlFor="home-country">Country</label><select id="home-country" value={country} onChange={event=>onCountry(event.target.value)} disabled={loading||!countries.length}>{!countries.length&&<option value="">Loading countries…</option>}{countries.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></div>
      </div>
      <div className="home-example-body" aria-busy={loading}>
        {loading?<div className="home-example-state" role="status">Loading {countryName} observations…</div>:unavailable?<div className="home-example-state"><p>This example is unavailable. Retry loading above or choose another country.</p></div>:<ComparisonJourney weeks={weeks} context={context} introduction onInspect={onInspect} onCompare={onCompare} onValidate={onValidate}/>}
      </div>
    </section>
  </div>;
}
