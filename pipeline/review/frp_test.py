"""Reproduce the fixed US daytime count-versus-FRP test from existing local FIRMS caches.

Run: python -m pipeline.review.frp_test --data-root /path/to/firetrace
Or pass /path/to/firetrace/data/processed/clean_cache_v2 to --data-root.
Raw archives and their count partitions must remain in the same original data tree.
No downloads, refits, source-cache writes or official-result modifications occur.
The protocol was recorded locally before the original analysis; its Git receipt
was committed afterwards. Re-running this script is a reproduction, not a fresh test.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE_REPORT = ROOT / 'reports/review/frp'
OUT = SOURCE_REPORT
REPO = ROOT
CACHE = ROOT / 'data/processed/clean_cache_v2'
YEARS = list(range(2013, 2025))
STREAMS = ['Terra', 'Aqua', 'VIIRS']
METRICS = ['C', 'V', 'F']
ALPHA = .05 / 3
PROTOCOL_COMMIT = '92626ed2f76fc6ab1bcefa6254d49609b7c6b982'
LABEL = 'REAL FIRMS DATA, US daytime 2013-2024'

def portable(value):
    """Never put machine-specific source paths into generated public/repo artifacts."""
    if isinstance(value, dict):
        return {k: portable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [portable(v) for v in value]
    if isinstance(value, str):
        text = value.replace('\\', '/')
        for prefix in (REPO.as_posix(), ROOT.as_posix()):
            if text.startswith(prefix + '/'):
                return text[len(prefix) + 1:]
    return value

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(name,x):
    (OUT/name).write_text(json.dumps(portable(x),indent=2,allow_nan=False),encoding='utf-8')

def check_protocol():
    receipt = json.loads((SOURCE_REPORT/'original_protocol_receipt.json').read_text())
    if sha(SOURCE_REPORT/'original_recorded_protocol.md').upper() != receipt['sha256'].upper():
        raise ValueError('The preserved original protocol bytes no longer match their frozen hash')
    return receipt
def validate_inputs():
    started=datetime.now(timezone.utc).isoformat()
    manifest=[]; errors=[]; summaries=[]; missing=[]
    key=['local_date','stream','daynight','type']
    # Exact historical source remains on disk; promoted copy changes a report phase label.
    codes=[REPO/'work/phase3/aggregate_archives.py',REPO/'pipeline/clean.py',REPO/'pipeline/harmonize.py']
    code_hash=hashlib.sha256(''.join(sha(x) for x in codes).encode()).hexdigest()
    cleanroot=CACHE
    snapshot=json.loads((SOURCE_REPORT/'source_snapshot.json').read_text())
    expected_files={Path(x['clean_path']).name:x for x in snapshot['inputs']}
    for sensor in ['modis','viirs-snpp']:
        for fileyear in range(2012,2026):
            p=cleanroot/f'{sensor}_{fileyear}_United_States.parquet'
            archive=REPO/f'work/phase3/nepal-us/archives/United_States/{sensor}/{fileyear}'
            donepath=archive/'done.json'
            if not p.exists() or not donepath.exists():
                errors.append(f'missing input {p} or {donepath}');continue
            done=json.loads(donepath.read_text())
            if sha(p)!=expected_files[p.name]['clean_sha256']:errors.append(f'Frozen cache hash mismatch {p.name}')
            if sha(donepath)!=expected_files[p.name]['done_sha256']:errors.append(f'Frozen completion metadata mismatch {p.name}')
            cols=['country','stream','local_date','year','weekday','daynight','type','frp','source_file','file_year','confidence']
            d=pd.read_parquet(p,columns=cols)
            diagnostic=d.attrs.get('diagnostics',{})
            sources=d.source_file.unique().tolist()
            raw=REPO/f'data/raw/{sensor}/{fileyear}/{sensor}_{fileyear}_United_States.csv'
            if len(sources)!=1 or Path(sources[0].replace('\\', '/')).name!=raw.name:
                errors.append(f'source identity mismatch {p.name}: {sources}')
            rawhash=sha(raw) if raw.exists() else None
            if rawhash!=expected_files[p.name]['source_sha256']:errors.append(f'Frozen raw source hash mismatch {raw.name}')
            if rawhash!=done['signature']['source_sha256']:errors.append(f'raw hash mismatch {raw}')
            if len(d)!=done['cleaned_rows']:errors.append(f'cleaned row mismatch {p.name}')
            if done['signature']['code_sha256']!=code_hash:errors.append(f'code hash mismatch {p.name}')
            if diagnostic!=done['diagnostics']:errors.append(f'cleaning diagnostics mismatch {p.name}')
            if not d.country.eq('United_States').all():errors.append(f'country mismatch {p.name}')
            if not d.file_year.eq(fileyear).all():errors.append(f'file year mismatch {p.name}')
            if not (d.year.eq(d.local_date.dt.year)&d.weekday.eq(d.local_date.dt.dayofweek)).all():errors.append(f'date field mismatch {p.name}')
            expected=['Aqua','Terra'] if sensor=='modis' else ['VIIRS']
            if not d.stream.isin(expected).all():errors.append(f'stream mismatch {p.name}')
            q=pd.to_numeric(d.confidence,errors='coerce').ge(30) if sensor=='modis' else d.confidence.astype(str).str.lower().isin(['n','h','nominal','high'])
            if not q.all():errors.append(f'confidence mismatch {p.name}')
            d['n']=1;d['frp_known']=d.frp.notna().astype('int64');d['frp_sum']=d.frp.fillna(0.)
            a=d.groupby(key,observed=True,dropna=False)[['n','frp_known','frp_sum']].sum().sort_index()
            parts=sorted(archive.glob('counts-*.parquet'))
            frozen_parts={Path(item['path']).name:item['sha256'] for item in expected_files[p.name]['partitions']}
            if {part.name for part in parts} != set(frozen_parts):errors.append(f'Frozen partition inventory mismatch {p.name}')
            frames=[];partmeta=[]
            for part in parts:
                if sha(part)!=frozen_parts.get(part.name):errors.append(f'Frozen partition hash mismatch {sensor}/{fileyear}/{part.name}')
                t=pd.read_parquet(part,columns=key+['n','frp_known','frp_sum'])
                if t.attrs.get('source_sha256')!=rawhash:errors.append(f'partition source mismatch {part}')
                frames.append(t);partmeta.append({'path':str(part),'sha256':sha(part),'bytes':part.stat().st_size})
            b=pd.concat(frames).groupby(key,observed=True,dropna=False)[['n','frp_known','frp_sum']].sum().sort_index()
            equal_index=a.index.equals(b.index)
            n_equal=bool(equal_index and np.array_equal(a[['n','frp_known']].values,b[['n','frp_known']].values))
            frp_equal=bool(equal_index and np.allclose(a.frp_sum,b.frp_sum,rtol=1e-10,atol=1e-6,equal_nan=True))
            maxdiff=float(np.nanmax(np.abs(a.frp_sum-b.frp_sum))) if equal_index else None
            if not n_equal or not frp_equal:errors.append(f'aggregate reconciliation failed {p.name}, counts={n_equal} FRP={frp_equal}')
            selected=d[d.year.between(2013,2024)&d.daynight.eq('D')&d.type.eq(0)].copy()
            selected['valid']=np.isfinite(selected.frp)&selected.frp.ge(0)
            selected['negative']=selected.frp.lt(0)
            selected['nonfinite_nonmissing']=(~np.isfinite(selected.frp))&selected.frp.notna()
            selected['missing']=selected.frp.isna()
            selected['zero']=selected.frp.eq(0)
            v=selected.groupby(['stream','year','weekday','local_date'],observed=True)[['n','valid','negative','nonfinite_nonmissing','missing','zero']].sum().reset_index()
            missing.append(v)
            summaries.append({'file':p.name,'rows':len(d),'selected_rows':len(selected),'daily_keys':len(a),'count_reconciliation':n_equal,'frp_reconciliation':frp_equal,'max_abs_daily_frp_roundoff':maxdiff})
            manifest.append({'clean_path':str(p),'clean_sha256':sha(p),'bytes':p.stat().st_size,'source_path':str(raw),'source_sha256':rawhash,'done_path':str(donepath),'done_sha256':sha(donepath),'partitions':partmeta})
            print(f'{p.name}: rows={len(d)} selected={len(selected)} count_match={n_equal} FRP_match={frp_equal}',flush=True)
    days=pd.concat(missing).groupby(['stream','year','weekday','local_date'])[['n','valid','negative','nonfinite_nonmissing','missing','zero']].sum().reset_index()
    outage=json.loads((ROOT/'reports/review/no_observation_summary.json').read_text())
    ranges=[(a,b) for _,a,b,_ in outage['documented_outages']]+[(d,d) for d in outage['no_data_days']['VIIRS']]
    masks={}
    for name,pad in [('primary',0),('padded',1)]:
        mask=set()
        for a,b in ranges:mask.update(pd.date_range(pd.Timestamp(a)-pd.Timedelta(days=pad),pd.Timestamp(b)+pd.Timedelta(days=pad)))
        masks[name]=mask
    quality=[];week=[]
    for name,mask in [('unmasked',set()),*masks.items()]:
        mm=days[~days.local_date.isin(mask)]
        m=mm.groupby(['stream','year','weekday'])[['n','valid','negative','nonfinite_nonmissing','missing','zero']].sum().reset_index()
        m['valid_fraction']=m.valid/m.n
        if len(m)!=252 or not m.n.gt(0).all():errors.append(f'missing stream/year/weekday ordinarycount denominator under {name}')
        y=m.groupby(['stream','year'])[['n','valid','negative','nonfinite_nonmissing','missing','zero']].sum().reset_index()
        y['valid_fraction']=y.valid/y.n
        spread=m.groupby(['stream','year']).valid_fraction.agg(lambda x:float(x.max()-x.min())).rename('weekday_valid_fraction_spread').reset_index()
        y=y.merge(spread,on=['stream','year'])
        y['mask']=name;m['mask']=name;quality.append(y);week.append(m)
        if len(y)!=36:errors.append(f'Expected36streamyears under{name},got{len(y)}')
        if not y.valid_fraction.ge(.95).all():errors.append(f'FRP valid coverage below95% under{name}')
        if not y.weekday_valid_fraction_spread.le(.01).all():errors.append(f'FRP weekday missingness spread exceeds1percentagepoint under{name}')
    y=pd.concat(quality,ignore_index=True)
    official=pd.read_csv(ROOT/'reports/official/kill_test_results.csv')
    official=official[(official.country=='United_States')&(official.subset=='day')].set_index('stream')
    observed=y[y['mask']=='unmasked'].groupby('stream').n.sum()
    reconciliation=[]
    for stream in STREAMS:
        actual=int(observed[stream]); original=int(official.loc[stream,'detections'])
        reconciliation.append({'stream':stream,'official_detections':original,'clean_unmasked_detections':actual,'difference':actual-original,'matches':actual==original})
        if actual!=original:errors.append(f'Official unmasked daytime count mismatch {stream}')
    pd.DataFrame(reconciliation).to_csv(OUT/'official_count_reconciliation.csv',index=False)
    pd.concat(week,ignore_index=True).to_csv(OUT/'quality_by_weekday.csv',index=False)
    y.to_csv(OUT/'quality_by_year.csv',index=False)
    save('input_manifest.json',{'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'code_hash':code_hash,'historical_code_files':[{'path':str(p),'sha256':sha(p)} for p in codes],'current_promoted_aggregate_sha256':sha(REPO/'pipeline/streaming/aggregate_archives.py'),'inputs':manifest})
    save('data_gate.json',{'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'gate_pass':not errors,'errors':errors,'file_checks':summaries,'quality_rows':y.to_dict(orient='records'),'excluded_dates':{k:sorted(x.strftime('%Y-%m-%d') for x in v) for k,v in masks.items()},'scope':'Full-source daily aggregate reconciliation and unmasked plus both masked local2013-24 daytime vegetation FRP quality only; no weekday effect contrasts calculated. Original historical work/phase3 aggregator bytehash matches saved code provenance exactly.'})
    u=y[y['mask']=='unmasked']
    print(json.dumps({'pass':not errors,'errors':errors,'selected_rows':int(u.n.sum()),'invalid_frp':int((u.n-u.valid).sum())}),flush=True)


    return not errors

def indices(frame):
    w=frame.date.dt.dayofweek
    exposure=frame.groupby(w).size().reindex(range(7),fill_value=0).to_numpy()
    sums=frame.groupby(w)[METRICS].sum().reindex(range(7),fill_value=0).to_numpy()
    assert np.all(exposure>0)
    rates=sums/exposure[:,None]
    mean=rates.mean(axis=0)
    assert np.isfinite(rates).all() and np.all(mean>0)
    out=rates/mean
    assert np.allclose(out.sum(axis=0),7,rtol=0,atol=1e-12)
    return out,exposure,sums

def synthetic_checks():
    dates=pd.date_range('2013-01-01','2013-12-31')
    c=np.arange(len(dates))%20+1
    t=pd.DataFrame({'date':dates,'C':c,'V':c,'F':7.*c})
    i,_,_=indices(t)
    assert np.allclose(i[:,1],i[:,2],atol=1e-14)
    t['C']=3;t['V']=3;t['F']=11
    j,_,_=indices(t)
    assert np.allclose(j,np.ones((7,3)),atol=1e-14)
    return {'constant_FRP_has_zero_contrast':True,'calendar_occurrence_adjusted_constant_rates_equal_one':True,'weekday_indices_sum_seven':True}

def analyze():
    start=datetime.now(timezone.utc).isoformat()
    freeze=check_protocol()
    gate=json.loads((OUT/'data_gate.json').read_text())
    assert gate['gate_pass'] and not gate['errors']
    manifest=json.loads((OUT/'input_manifest.json').read_text())
    tests=synthetic_checks()
    input_hashes=[];chunks=[]
    for entry in manifest['inputs']:
        p=REPO/entry['clean_path']
        actual=sha(p);assert actual==entry['clean_sha256']
        input_hashes.append({'path':str(p),'sha256':actual})
        d=pd.read_parquet(p,columns=['stream','local_date','daynight','type','frp'])
        d=d[d.local_date.between('2013-01-01','2024-12-31')&d.daynight.eq('D')&d.type.eq(0)].copy()
        d['C']=1;d['V']=(np.isfinite(d.frp)&d.frp.ge(0)).astype('int64')
        d['F']=d.frp.where(d.V.eq(1),0.)
        d=d.groupby(['stream','local_date'],observed=True)[METRICS].sum().reset_index()
        chunks.append(d)
    observed=pd.concat(chunks).groupby(['stream','local_date'])[METRICS].sum()
    dates=pd.date_range('2013-01-01','2024-12-31')
    complete=pd.MultiIndex.from_product([STREAMS,dates],names=['stream','local_date'])
    daily=observed.reindex(complete,fill_value=0).reset_index().rename(columns={'local_date':'date'})
    daily['year']=daily.date.dt.year;daily['weekday']=daily.date.dt.dayofweek
    for n in ['C','V']:daily[n]=daily[n].astype('int64')
    daily.to_csv(OUT/'daily_counts_and_frp.csv',index=False)
    draws=np.random.Generator(np.random.PCG64(20261115)).integers(0,12,size=(50000,12))
    assert draws.dtype==np.int64
    np.save(OUT/'bootstrap_year_draws.npy',draws)
    profiles=[];annual=[];exposure_rows=[];max_rows=[];loyo_rows=[];summaries=[];exclusion_rows=[]
    for mask_name,excluded in gate['excluded_dates'].items():
        excl=pd.to_datetime(excluded)
        for date in excluded:exclusion_rows.append({'mask':mask_name,'date':date})
        use=daily[~daily.date.isin(excl)]
        common_dates=pd.Series(dates[~dates.isin(excl)])
        for year in YEARS:
            local=common_dates[common_dates.dt.year==year]
            for weekday,n in local.groupby(local.dt.dayofweek).size().items():exposure_rows.append({'mask':mask_name,'year':year,'weekday':int(weekday),'days':int(n)})
        for stream in STREAMS:
            all_indices=[];deltas=[];max_deltas=[]
            for year in YEARS:
                frame=use[use.stream.eq(stream)&use.year.eq(year)].sort_values('date')
                ix,exposure,sums=indices(frame)
                all_indices.append(ix);delta=float(ix[6,2]-ix[6,1]);deltas.append(delta)
                annual.append({'mask':mask_name,'stream':stream,'year':year,'count_sunday':float(ix[6,0]),'valid_count_sunday':float(ix[6,1]),'frp_sunday':float(ix[6,2]),'delta':delta,'ordinary_detections':int(sums[:,0].sum()),'valid_detections':int(sums[:,1].sum()),'sampled_frp_sum_mw':float(sums[:,2].sum())})
                for weekday in range(7):profiles.append({'mask':mask_name,'stream':stream,'year':year,'weekday':weekday,'exposure_days':int(exposure[weekday]),**{m+'_index':float(ix[weekday,j]) for j,m in enumerate(METRICS)},**{m+'_sum':float(sums[weekday,j]) for j,m in enumerate(METRICS)}})
                largest=frame.loc[frame.F.idxmax()]
                trimmed=frame[frame.date.ne(largest.date)]
                trimmed_ix,_,_=indices(trimmed)
                md=float(trimmed_ix[6,2]-trimmed_ix[6,1]);max_deltas.append(md)
                max_rows.append({'mask':mask_name,'stream':stream,'year':year,'removed_date':largest.date.strftime('%Y-%m-%d'),'removed_weekday':int(largest.weekday),'removed_C':int(largest.C),'removed_V':int(largest.V),'removed_F':float(largest.F),'max_day_frp_share':float(largest.F/frame.F.sum()),'trimmed_delta':md,'trimmed_count_sunday':float(trimmed_ix[6,1]),'trimmed_frp_sunday':float(trimmed_ix[6,2])})
            arr=np.asarray(deltas);means=arr[draws].mean(axis=1)
            low,high=np.quantile(means,[ALPHA/2,1-ALPHA/2],method='linear')
            loyo=[]
            for i,year in enumerate(YEARS):
                value=float(np.delete(arr,i).mean());loyo.append(value)
                loyo_rows.append({'mask':mask_name,'stream':stream,'omitted_year':year,'mean_delta':value})
            mean_profile=np.asarray(all_indices).mean(axis=0)
            flags={'effect_at_least_0_05':bool(arr.mean()>=.05),'adjusted_CI_above_zero':bool(low>0),'all_LOYO_positive':bool(min(loyo)>0),'maximum_day_removal_positive':bool(np.mean(max_deltas)>0)}
            summaries.append({'mask':mask_name,'stream':stream,'count_sunday':float(mean_profile[6,0]),'valid_count_sunday':float(mean_profile[6,1]),'frp_sunday':float(mean_profile[6,2]),'mean_delta':float(arr.mean()),'ci_lower':float(low),'ci_upper':float(high),'ci_coverage':1-ALPHA,'loyo_min':min(loyo),'loyo_max':max(loyo),'max_day_removal_mean_delta':float(np.mean(max_deltas)),'count_sunday_below_one':bool(mean_profile[6,1]<1),'pass':all(flags.values()),'criteria':flags,'mean_weekday_profiles':{m:[float(x) for x in mean_profile[:,j]] for j,m in enumerate(METRICS)}})
    for name,rows in [('annual_contrasts.csv',annual),('annual_weekday_profiles.csv',profiles),('exposure_days.csv',exposure_rows),('maximum_day_sensitivity.csv',max_rows),('leave_one_year_out.csv',loyo_rows),('excluded_dates.csv',exclusion_rows)]:pd.DataFrame(rows).to_csv(OUT/name,index=False)
    flattened=[{k:v for k,v in row.items() if k not in ['criteria','mean_weekday_profiles']} for row in summaries]
    pd.DataFrame(flattened).to_csv(OUT/'summary.csv',index=False)
    passing=[s for s in STREAMS if all(r['pass'] for r in summaries if r['stream']==s)]
    verdict={'status':'PASS' if len(passing)>=2 else 'FAIL','passing_streams_both_masks':passing,'independently_verified':False,'scientific_interpretation_pending':True,'summaries':summaries,'protocol_sha256':freeze['sha256'],'protocol_frozen_utc':freeze['frozen_utc'],'analysis_started_utc':start,'analysis_finished_utc':datetime.now(timezone.utc).isoformat(),'gate_sha256':sha(OUT/'data_gate.json'),'input_manifest_sha256':sha(OUT/'input_manifest.json'),'script_sha256':sha(Path(__file__)),'bootstrap_draws_npy_sha256':sha(OUT/'bootstrap_year_draws.npy'),'bootstrap_draws_array_sha256':hashlib.sha256(draws.tobytes()).hexdigest(),'runtime_versions':{'numpy':np.__version__,'pandas':pd.__version__},'synthetic_checks':tests,'input_hashes_reverified':input_hashes,'limitations':['12 year blocks; no clear-sky coverage or weather controls','Corroborating, correlated satellite streams; not independent experiments','Summed snapshot radiative power is not energy, emissions, severity, burned area or causal evidence','Prospectively specified new analysis of already inspected historical data; no new holdout']}
    save('results.json',verdict)
    print(json.dumps({'status':verdict['status'],'passing_streams':passing},indent=2))
    return verdict


def public_stream(row):
    names = {'Terra': 'MODIS Terra', 'Aqua': 'MODIS Aqua', 'VIIRS': 'VIIRS S-NPP'}
    return {
        'stream': row['stream'], 'name': names[row['stream']],
        'count_weekdays': row['mean_weekday_profiles']['V'],
        'frp_weekdays': row['mean_weekday_profiles']['F'],
        'count_sunday': row['valid_count_sunday'], 'frp_sunday': row['frp_sunday'],
        'delta': row['mean_delta'], 'ci_low': row['ci_lower'], 'ci_high': row['ci_upper'],
        'passed': row['pass'], 'loyo_min': row['loyo_min'],
        'max_day_removed_delta': row['max_day_removal_mean_delta'],
    }


def public_payload(results, gate):
    masks = []
    for name in ('primary', 'padded'):
        rows = [row for row in results['summaries'] if row['mask'] == name]
        masks.append({'name': name, 'excluded_days': len(gate['excluded_dates'][name]),
                      'passing_streams': [row['stream'] for row in rows if row['pass']],
                      'streams': [public_stream(row) for row in rows]})
    names = {'Terra': 'MODIS Terra', 'Aqua': 'MODIS Aqua', 'VIIRS': 'VIIRS S-NPP'}
    passing = [names[s] for s in results['passing_streams_both_masks']]
    sentence = ('In US daytime observations from 2013-2024, the Sunday deficit was stronger in detection counts '
                'than in summed fire radiative power in ' + ' and '.join(passing) + ', under a pre-specified test.')
    if results['status'] != 'PASS':
        sentence = ('This test did not establish a stable difference between count and FRP weekday patterns; '
                    'we keep the original count finding with its limits.')
    quality = pd.DataFrame(gate['quality_rows'])
    primary = quality[quality['mask'] == 'primary']
    padded = quality[quality['mask'] == 'padded']
    return {
        'version': 1, 'label': LABEL,
        'scope': {'country': 'United States', 'years': [2013, 2024], 'source_type': 0,
                  'subset': 'daytime', 'year_blocks': len(YEARS)},
        'protocol': {'sha256': results['protocol_sha256'], 'frozen_utc': results['protocol_frozen_utc'],
                     'git_receipt_commit': PROTOCOL_COMMIT, 'git_receipt_after_original_results': True,
                     'chronology_note': 'The local protocol was recorded before the original analysis. This Git receipt '
                                        'was committed after its results were known; this is not external preregistration or a new holdout.'},
        'verdict': results['status'].lower(), 'pass_sentence': sentence,
        'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'inference': {'baseline': 1, 'ci_percent': 100 * (1 - ALPHA), 'bootstrap_draws': 50000,
                      'point_threshold': .05},
        'streams': masks[0]['streams'], 'masks': masks,
        'data_gate': {'passed': gate['gate_pass'], 'valid_frp_fraction': float(primary.valid.sum() / primary.n.sum()),
                      'records_primary': int(primary.n.sum()), 'records_padded': int(padded.n.sum())},
        'limitations': ['Summed FRP is sampled radiative power, not energy, emissions, burned area or fire counts.',
                        'The same detections form both measures; a difference does not establish ignition cause.',
                        'Twelve year blocks, correlated sensors and unmeasured cloud/overpass exposure limit inference.',
                        'Terra does not meet the corrected uncertainty criterion; its interval includes zero.',
                        'The effect threshold is a project feasibility choice, not a NASA standard.'],
        'evidence': {'chart': '/evidence/frp/weekday_profiles.svg', 'report': '/evidence/frp/FRP_TEST.md',
                     'protocol': '/evidence/frp/original_recorded_protocol.md', 'summary': '/evidence/frp/summary.csv',
                     'annual': '/evidence/frp/annual_contrasts.csv', 'verification': '/evidence/frp/independent_verification.json'},
    }


def verify_export_sources(receipt, results):
    """Bind public numbers to the independently checked artifacts, rejecting stale receipts."""
    if receipt.get('status') != 'PASS':
        raise ValueError('Independent verification did not pass; public export blocked')
    if receipt.get('analysis_script_sha256') != sha(Path(__file__)):
        raise ValueError('The independent receipt predates the current runner; repeat verification')
    required = {'data_gate.json', 'input_manifest.json', 'daily_counts_and_frp.csv', 'summary.csv',
                'annual_weekday_profiles.csv', 'annual_contrasts.csv', 'maximum_day_sensitivity.csv',
                'leave_one_year_out.csv', 'exposure_days.csv', 'excluded_dates.csv', 'bootstrap_year_draws.npy'}
    pinned = receipt.get('verified_artifacts_sha256', {})
    if not required.issubset(pinned):
        raise ValueError('The independent receipt does not pin all required scientific artifacts')
    for name, digest in pinned.items():
        if sha(OUT/name) != digest:
            raise ValueError(f'Independent receipt is stale for {name}; public export blocked')
    table = pd.read_csv(OUT/'summary.csv').set_index(['mask', 'stream'])
    profiles = pd.read_csv(OUT/'annual_weekday_profiles.csv')
    means = profiles.groupby(['mask', 'stream', 'weekday'])[['V_index', 'F_index']].mean()
    if len(results['summaries']) != len(table):
        raise ValueError('Result JSON and verified summary contain different stream/mask rows')
    for row in results['summaries']:
        key = (row['mask'], row['stream'])
        verified = table.loc[key]
        for name in ('count_sunday', 'valid_count_sunday', 'frp_sunday', 'mean_delta', 'ci_lower', 'ci_upper',
                     'loyo_min', 'loyo_max', 'max_day_removal_mean_delta'):
            if not np.isclose(row[name], verified[name], rtol=0, atol=1e-12):
                raise ValueError(f'Public JSON differs from verified {key}/{name}')
        if row['pass'] != bool(verified['pass']):
            raise ValueError(f'Public JSON differs from verified gate for {key}')
        for metric in ('V', 'F'):
            if not np.allclose(row['mean_weekday_profiles'][metric], means.loc[key][metric+'_index'], rtol=0, atol=1e-12):
                raise ValueError(f'Public weekday profile differs from verified annual indices for {key}/{metric}')


def write_report(results, gate, verification=None):
    payload = public_payload(results, gate)
    lines = ['# Count versus FRP: fixed US daytime comparison', '', '**' + LABEL + '**', '',
             '**Numerical verdict: ' + results['status'] + '.** ' + payload['pass_sentence'], '',
             '## Chronology and scope', '', payload['protocol']['chronology_note'], '',
             f"Original local protocol: {results['protocol_frozen_utc']}; SHA-256 `{results['protocol_sha256']}`. "
             f"The later Git receipt is `{PROTOCOL_COMMIT}`. This run reproduces that completed analysis; "
             'it does not manufacture a new prediction. The original immutable receipt contains a historical local path; '
             'all new source manifests use relative paths, and that receipt JSON is not published to the website.', '',
             'United States, local civil years 2013–2024, vegetation type 0, daytime. Terra, Aqua and S-NPP are separate. '
             'Only finite, nonnegative FRP enters both paired measures; a recorded zero is valid. '
             'Each yearly weekday total is divided by eligible weekday occurrences and normalized by the unweighted '
             'mean of seven weekday rates. Twelve annual Sunday differences are averaged equally.', '',
             '## Results', '', '| Mask | Stream | Count Sunday index | FRP Sunday index | Delta | Adjusted interval | Pass |',
             '|---|---|---:|---:|---:|---|---|']
    for row in results['summaries']:
        lines.append(f"| {row['mask']} | {row['stream']} | {row['valid_count_sunday']:.6f} | {row['frp_sunday']:.6f} | "
                     f"{row['mean_delta']:.6f} | {row['ci_lower']:.6f} to {row['ci_upper']:.6f} | {row['pass']} |")
    lines += ['', 'Indices have baseline one; deltas are index units, not percentages of fires or emissions. '
              'Streams meeting every condition under both masks: ' + ', '.join(results['passing_streams_both_masks']) + '. '
              'The table and accompanying sensitivity files show every stream, including failed criteria.', '',
              'The same 50,000 joint year draws (PCG64 seed 20261115; int64) are used for every stream and mask. '
              'Two-sided Bonferroni percentile intervals use exact coverage 1 − 0.05/3 = 98.333…%. '
              'The point estimate must be at least 0.05 and the interval lower bound above zero, with positive '
              'leave-one-year-out and maximum-day-removal means. This is a specified annual-block model, not '
              'guaranteed uncertainty coverage from twelve real years.', '',
              '## Input and official-count reconciliation', '',
              'All 28 cache hashes, raw source hashes, completion records and archived daily counts/FRP sums '
              'are verified against the original snapshot. The historical aggregation-code signature is exact; '
              'its later promoted copy differs only in a descriptive report label. '
              'The unmasked clean counts agree exactly with the official daytime totals:', '',
              '| Stream | Official count | Clean unmasked count | Difference |', '|---|---:|---:|---:|']
    for row in pd.read_csv(OUT/'official_count_reconciliation.csv').itertuples():
        lines.append(f'| {row.stream} | {row.official_detections} | {row.clean_unmasked_detections} | {row.difference} |')
    lines += ['', f"The common primary mask excludes {len(gate['excluded_dates']['primary'])} dates; padding every "
              f"frozen range by one day excludes {len(gate['excluded_dates']['padded'])}. Primary support contains "
              f"{payload['data_gate']['records_primary']:,} detections and padded support {payload['data_gate']['records_padded']:,}. "
              'Every eligible FRP value is finite and nonnegative. All stream-years pass the ≥95% valid and '
              '≤1-percentage-point weekday missingness-spread gates. Zeros and exclusions are listed separately. '
              'Eligible calendar dates are not measured clear-sky observation exposure.', '', '## Independent checks', '']
    if verification is not None:
        lines += ['The separate checker recomputes observations, daily sums, indices, contrasts, inference and sensitivity '
                  'from the clean caches without importing the runner. See [independent_verification.json](independent_verification.json) '
                  'and its linked evidence; the receipt is required before the public payload is written.']
    else:
        lines += ['Portable independent verification is pending. The public export is blocked until its receipt passes.']
    lines += ['', '## Limitations', '', *['- ' + s for s in payload['limitations']], '',
              'This is a defensible additional measurement comparison, not proof of a new causal mechanism or a world-first result. '
              'It does not alter the official weekly-rhythm gate or the harmonization model.', '', '## Reproduce', '',
              '```sh', 'python -m pipeline.review.frp_test --data-root /path/to/original/firetrace',
              'python scripts/verify_frp_test.py --data-root /path/to/original/firetrace --report-dir reports/review/frp',
              'python scripts/plot_frp_test.py --report-dir reports/review/frp',
              'python -m pipeline.review.frp_test --publish-only', '```', '',
              'The data root may also name its `data/processed/clean_cache_v2` directory. Raw archives and the saved '
              'aggregation tree are needed for provenance reconciliation. No download is performed. '
              'Use `--output` for a separate reproduction directory. `--publish-only` copies verified small artifacts '
              'into `web/public/evidence/frp` and creates `web/public/data/frp.json`; it does not deploy.', '',
              'Source definition: [NASA FIRMS VIIRS attributes](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html). '
              'Full inputs, annual contrasts, all sensitivities and the unchanged original protocol accompany this report.', '']
    (OUT/'FRP_TEST.md').write_text('\n'.join(lines), encoding='utf-8')


def publish(results, gate):
    receipt_path = OUT/'independent_verification.json'
    if not receipt_path.exists():
        raise ValueError('Independent verification receipt is required before public export')
    receipt = json.loads(receipt_path.read_text())
    verify_export_sources(receipt, results)
    if not (OUT/'count_vs_frp_weekdays.svg').exists():
        raise ValueError('Verified weekday profile chart is required before public export')
    write_report(results, gate, receipt)
    public = ROOT/'web/public/evidence/frp'
    public.mkdir(parents=True, exist_ok=True)
    for name in ('FRP_TEST.md', 'summary.csv', 'annual_contrasts.csv', 'independent_verification.json'):
        shutil.copyfile(OUT/name, public/name)
    shutil.copyfile(SOURCE_REPORT/'original_recorded_protocol.md', public/'original_recorded_protocol.md')
    shutil.copyfile(OUT/'count_vs_frp_weekdays.svg', public/'weekday_profiles.svg')
    payload = public_payload(results, gate)
    (ROOT/'web/public/data/frp.json').write_text(json.dumps(payload, indent=2, allow_nan=False), encoding='utf-8')
    print('Published verified static FRP artifacts locally; no deployment performed.')


def main():
    global OUT, REPO, CACHE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, default=ROOT,
                        help='Original data repository root, or its data/processed/clean_cache_v2 directory')
    parser.add_argument('--output', type=Path, default=SOURCE_REPORT)
    parser.add_argument('--publish-only', action='store_true', help='Export existing independently verified outputs to web/public')
    args = parser.parse_args()
    OUT = args.output.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.publish_only:
        publish(json.loads((OUT/'results.json').read_text()), json.loads((OUT/'data_gate.json').read_text()))
        return
    given = args.data_root.resolve()
    if given.name == 'clean_cache_v2':
        CACHE, REPO = given, given.parents[2]
    else:
        REPO, CACHE = given, given/'data/processed/clean_cache_v2'
    check_protocol()
    if not validate_inputs():
        raise SystemExit('Data/provenance gate failed; no FRP effect calculated. See data_gate.json.')
    result = analyze()
    write_report(result, json.loads((OUT/'data_gate.json').read_text()))


if __name__ == '__main__':
    main()

