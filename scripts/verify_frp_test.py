"""Independently reproduce the frozen US count/FRP test from existing clean caches.

No analysis functions are imported. Original outcome was known before this portable
packaging step; generated timestamps here are reproduction times, not prediction times.
Usage: python scripts/verify_frp_test.py --data-root /path/to/clean_cache_v2
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import numpy as np
import pandas as pd

CODE_ROOT=Path(__file__).resolve().parents[1]
YEARS=list(range(2013,2025))
STREAMS=['Terra','Aqua','VIIRS']
METRICS=['n','valid_n','valid_frp']
RANGES=[('2020-08-16','2020-09-02'),('2022-03-31','2022-04-16'),('2022-07-26','2022-08-10'),('2024-07-09','2024-07-16'),('2024-07-24','2024-08-01'),('2024-05-31','2024-06-02'),('2024-11-04','2024-11-05')]
EXPECTED_PROTOCOL='1B88C8B3C7A1225FB2AA10E3B19DD9311CB7F4B022A9795C51552557BB434171'
checks=[]

def hashfile(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def audit_inputs():
    manifest = json.loads((REPO/'work/phase3/nepal-us/source_manifest.json').read_text())
    records = {(r['sensor'],r['year']):r for r in manifest['files'] if r['country']=='United_States'}
    all_clean, all_agg, receipts, failures = [], [], [], []
    key = ['stream','local_date','daynight','type']
    columns = ['country','stream','utc','local','local_date','year','weekday','frp','daynight','type','confidence','timezone','file_year','source_file']
    for sensor in ['modis','viirs-snpp']:
        for year in range(2012,2026):
            p = CACHE/f'{sensor}_{year}_United_States.parquet'
            archive = REPO/f'work/phase3/nepal-us/archives/United_States/{sensor}/{year}'
            df = pd.read_parquet(p, columns=columns)
            done = json.loads((archive/'done.json').read_text())
            raw = REPO/f'data/raw/{sensor}/{year}/{sensor}_{year}_United_States.csv'
            raw_hash = hashfile(raw)
            bads = {}
            bads['raw_hash_mismatch'] = raw_hash != records[sensor,year]['sha256'] or raw_hash != done['signature']['source_sha256']
            bads['cache_row_count_mismatch'] = len(df) != done['cleaned_rows']
            bads['file_year'] = int((df.file_year!=year).sum())
            bads['country'] = int((df.country!='United_States').sum())
            bads['local_date'] = int((pd.to_datetime(df.local).dt.normalize()!=pd.to_datetime(df.local_date)).sum())
            bads['year'] = int((pd.to_datetime(df.local_date).dt.year!=df.year).sum())
            bads['weekday'] = int((pd.to_datetime(df.local_date).dt.dayofweek!=df.weekday).sum())
            conf = df.confidence.astype(str).str.lower().str.strip()
            accepted = (df.stream.eq('VIIRS') & conf.isin(['n','h','nominal','high'])) | (df.stream.isin(['Terra','Aqua']) & pd.to_numeric(conf,errors='coerce').ge(30))
            bads['confidence'] = int((~accepted).sum())
            bads['unexpected_stream'] = int((~df.stream.isin(['Terra','Aqua'] if sensor=='modis' else ['VIIRS'])).sum())
            sources = df.source_file.unique().tolist()
            source_bad = []
            for s in sources:
                expected = f'data/raw/{sensor}/{year}/{sensor}_{year}_United_States.csv'
                source_text = str(s).replace('\\','/')
                if source_text != expected and not source_text.endswith('/'+expected):
                    source_bad.append(s)
            bads['source_identity'] = len(source_bad)
            for k,v in bads.items():
                if v:
                    failures.append({'file':p.name,'check':k,'value':v})
            # Verify every local conversion directly using the stored IANA zone.
            local_bad = 0
            for tz, part in df.groupby('timezone',observed=True):
                recovered = pd.to_datetime(part.utc,utc=True).dt.tz_convert(tz).dt.tz_localize(None)
                local_bad += int((recovered!=pd.to_datetime(part.local)).sum())
            if local_bad:
                failures.append({'file':p.name,'check':'IANA_local_timestamp','value':local_bad})
            frp = pd.to_numeric(df.frp, errors='coerce')
            df['n'] = 1
            df['numeric_known'] = frp.notna().astype('int64')
            df['numeric_frp'] = frp.fillna(0.)
            valid = np.isfinite(frp.to_numpy()) & frp.ge(0).to_numpy()
            df['valid_n'] = valid.astype('int64')
            df['valid_frp'] = frp.where(valid,0.)
            df['invalid_n'] = (~valid).astype('int64')
            sums = ['n','numeric_known','numeric_frp','valid_n','valid_frp','invalid_n']
            all_clean.append(df.groupby(key,observed=True,dropna=False)[sums].sum().reset_index())
            aggregate_frames=[]
            metadata_bad = 0
            for ap in sorted(archive.glob('counts-*.parquet')):
                ad = pd.read_parquet(ap)
                metadata_bad += int(ad.attrs.get('source_sha256')!=raw_hash)
                aggregate_frames.append(ad[key+['n','frp_known','frp_sum']])
            agg = pd.concat(aggregate_frames).groupby(key,observed=True,dropna=False)[['n','frp_known','frp_sum']].sum().reset_index()
            all_agg.append(agg)
            if metadata_bad:
                failures.append({'file':p.name,'check':'aggregate_source_hash','value':metadata_bad})
            receipts.append({'file':p.name,'sha256':hashfile(p),'raw_file':raw.relative_to(REPO).as_posix(),'raw_sha256':raw_hash,'rows':len(df),'local_timestamp_mismatches':local_bad,'invalid_frp':int((~valid).sum()),'negative_frp':int(frp.lt(0).sum()),'nonfinite_frp':int((~np.isfinite(frp)).sum()),'checks':bads})
            print(f'input verified {sensor} {year}',flush=True)
    c = pd.concat(all_clean).groupby(key,observed=True,dropna=False)[sums].sum().reset_index()
    a = pd.concat(all_agg).groupby(key,observed=True,dropna=False)[['n','frp_known','frp_sum']].sum().reset_index()
    merged=c.merge(a,on=key,how='outer',suffixes=('_cache','_archive'),indicator=True)
    reconciliation = {'keys':len(merged),'one_sided_keys':int(merged['_merge'].ne('both').sum()),'count_mismatches':int(merged.n_cache.ne(merged.n_archive).sum()),'known_mismatches':int(merged.numeric_known.ne(merged.frp_known).sum()),'max_frp_abs_error':float((merged.numeric_frp-merged.frp_sum).abs().max()),'frp_close':bool(np.allclose(merged.numeric_frp,merged.frp_sum,rtol=1e-12,atol=1e-6))}
    c['local_date']=pd.to_datetime(c.local_date)
    study=c.loc[c.local_date.between('2013-01-01','2024-12-31') & c.daynight.eq('D') & c.type.eq(0)].copy()
    study=study.groupby(['stream','local_date'],observed=True)[sums].sum().reset_index()
    payload={'generated_utc':datetime.now(timezone.utc).isoformat(),'purpose':'Input quality/provenance only; no weekday FRP contrasts calculated','files':receipts,'failures':failures,'reconciliation':reconciliation,'study_rows':len(study),'study_totals':{k:float(study[k].sum()) for k in ['n','valid_n','invalid_n']}}
    (OUT/'input_audit.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    assert not failures, 'Independent input consistency checks failed'
    assert reconciliation['one_sided_keys']==0 and reconciliation['count_mismatches']==0 and reconciliation['known_mismatches']==0 and reconciliation['frp_close'], 'Input aggregate reconciliation failed'
    official=pd.read_csv(CODE_ROOT/'reports/official/kill_test_results.csv')
    official=official.loc[official.country.eq('United_States') & official.subset.eq('day')].set_index('stream')
    totals=study.groupby('stream').n.sum()
    official_rows=[{'stream':s,'official_detections':int(official.loc[s,'detections']),'reconstructed_detections':int(totals[s]),'matches':int(official.loc[s,'detections'])==int(totals[s])} for s in STREAMS]
    payload['official_unmasked_daytime_reconciliation']=official_rows
    (OUT/'input_audit.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    assert all(r['matches'] for r in official_rows), 'Official daytime totals differ'
    return study

def indices(frame):
    """Zero rows already inserted; each index date contributes one eligible day."""
    day = frame.index.dayofweek
    exposure = np.bincount(day,minlength=7)
    assert np.all(exposure>0)
    sums = np.vstack([frame.loc[day==w,METRICS].sum().to_numpy(dtype=float) for w in range(7)])
    rates = sums / exposure[:,None]
    means = rates.mean(axis=0)
    assert np.all(means>0)
    result = rates/means
    assert np.allclose(result.sum(axis=0),7,rtol=0,atol=1e-12)
    return result,exposure

def self_checks():
    # Rate adjustment must make a constant daily observation flat even in leap years.
    dates=pd.date_range('2020-01-01','2020-12-31')
    constant=pd.DataFrame({'n':1,'valid_n':1,'valid_frp':3.},index=dates)
    ix,_=indices(constant)
    assert np.allclose(ix,1)
    # Equal weights imply identical paired normalized profiles.
    weighted=constant.copy()
    weighted.loc[weighted.index.dayofweek==6,['n','valid_n','valid_frp']]*=2
    ix,_=indices(weighted)
    assert np.allclose(ix[:,0],ix[:,2])
    # No observations on a valid date remain exposure (not silently dropped).
    weighted.iloc[0]=0
    _,e=indices(weighted)
    assert e.sum()==366
    removed=weighted.drop(weighted.index[0])
    _,e2=indices(removed)
    assert e2.sum()==365
    return ['constant_daily_rates_flat_with_52_53_occurrences','constant_per_detection_FRP_equal_indices','zero_observation_dates_retained','excluded_dates_removed_from_denominator']

def independent_quality_gate(raw):
    """Check both fixed masks before any FRP weekday contrasts are recalculated."""
    rows=[]
    for mask,padding in [('primary',0),('padded',1)]:
        excluded=set()
        for a,b in RANGES:
            excluded.update(pd.date_range(pd.Timestamp(a)-pd.Timedelta(days=padding),pd.Timestamp(b)+pd.Timedelta(days=padding)))
        included=raw.loc[~raw.local_date.isin(excluded)].copy()
        included['year']=included.local_date.dt.year
        included['weekday']=included.local_date.dt.dayofweek
        for stream in STREAMS:
            for year in YEARS:
                group=included.loc[included.stream.eq(stream)&included.year.eq(year)]
                totals=group.groupby('weekday')[['n','valid_n']].sum().reindex(range(7),fill_value=0)
                assert totals.n.gt(0).all(), 'Missing ordinary weekday denominator'
                fractions=1-totals.valid_n/totals.n
                valid_fraction=float(totals.valid_n.sum()/totals.n.sum())
                spread=float(fractions.max()-fractions.min())
                rows.append({'mask':mask,'stream':stream,'year':year,'valid_fraction':valid_fraction,'weekday_invalid_fraction_spread':spread,'pass':valid_fraction>=.95 and spread<=.01})
    passed=all(row['pass'] for row in rows)
    (OUT/'independent_data_gate.json').write_text(json.dumps({'gate_pass':passed,'checks':rows},indent=2),encoding='utf-8')
    assert passed, 'Independent FRP quality gate failed'

def analyze(raw):
    protocol_hash=hashlib.sha256((CODE_ROOT/'reports/review/frp/original_recorded_protocol.md').read_bytes()).hexdigest().upper()
    assert protocol_hash==EXPECTED_PROTOCOL
    gate=json.loads((RUN/'data_gate.json').read_text())
    assert gate.get('gate_pass') is True, 'Runner input gate is not passed'
    audit=json.loads((OUT/'input_audit.json').read_text())
    assert not audit['failures'] and audit['reconciliation']['count_mismatches']==0
    checks=self_checks()
    raw['local_date']=pd.to_datetime(raw.local_date)
    independent_quality_gate(raw)
    full_calendar=pd.date_range('2013-01-01','2024-12-31')
    rng=np.random.Generator(np.random.PCG64(20261115))
    draws=rng.integers(0,12,size=(50_000,12))
    draw_hash=hashlib.sha256(draws.tobytes()).hexdigest()
    annual_rows=[]; summary=[]; loyo_rows=[]; removed_rows=[]; exposure_rows=[]; quality_rows=[]; exclusion_rows=[]
    for mask,padding in [('primary',0),('padded',1)]:
        excluded=set()
        for a,b in RANGES:
            excluded.update(pd.date_range(pd.Timestamp(a)-pd.Timedelta(days=padding),pd.Timestamp(b)+pd.Timedelta(days=padding)))
        calendar=full_calendar[~full_calendar.isin(excluded)]
        exclusion_rows.extend({'mask':mask,'date':d.date().isoformat()} for d in sorted(excluded))
        for stream in STREAMS:
            frame=raw.loc[raw.stream.eq(stream)].set_index('local_date')[METRICS].reindex(calendar,fill_value=0)
            annual=np.empty((12,7,3)); removed_delta=[]
            for yi,year in enumerate(YEARS):
                yframe=frame.loc[frame.index.year==year]
                ix,exposure=indices(yframe)
                annual[yi]=ix
                for w in range(7):
                    weekday=yframe.loc[yframe.index.dayofweek==w]
                    total=float(weekday.n.sum()); valid=float(weekday.valid_n.sum())
                    assert total>0
                    quality_rows.append({'mask':mask,'stream':stream,'year':year,'weekday':w,'ordinary':int(total),'valid':int(valid),'invalid_fraction':1-valid/total})
                    exposure_rows.append({'mask':mask,'stream':stream,'year':year,'weekday':w,'days':int(exposure[w])})
                    annual_rows.append({'mask':mask,'stream':stream,'year':year,'weekday':w,'ordinary_count_index':float(ix[w,0]),'valid_count_index':float(ix[w,1]),'frp_index':float(ix[w,2]),'delta':float(ix[w,2]-ix[w,1])})
                # idxmax returns first (earliest) tied date because index is sorted.
                max_day=yframe.valid_frp.idxmax()
                reduced=yframe.drop(max_day)
                reduced_ix,_=indices(reduced)
                removed_delta.append(float(reduced_ix[6,2]-reduced_ix[6,1]))
                removed_rows.append({'mask':mask,'stream':stream,'year':year,'removed_date':max_day.date().isoformat(),'maximum_frp':float(yframe.loc[max_day,'valid_frp']),'total_frp':float(yframe.valid_frp.sum()),'maximum_share':float(yframe.loc[max_day,'valid_frp']/yframe.valid_frp.sum()),'delta_after_removal':removed_delta[-1]})
            differences=annual[:,6,2]-annual[:,6,1]
            reps=differences[draws].mean(axis=1)
            lower,upper=np.quantile(reps,[.05/6,1-.05/6],method='linear')
            loyo=np.asarray([np.delete(differences,i).mean() for i in range(12)])
            loyo_rows.extend({'mask':mask,'stream':stream,'omitted_year':year,'delta':float(loyo[i])} for i,year in enumerate(YEARS))
            mean=float(differences.mean())
            removed_mean=float(np.mean(removed_delta))
            summary.append({'mask':mask,'stream':stream,'ordinary_count_index':float(annual[:,6,0].mean()),'valid_count_index':float(annual[:,6,1].mean()),'frp_index':float(annual[:,6,2].mean()),'delta':mean,'ci_lower':float(lower),'ci_upper':float(upper),'loyo_min':float(loyo.min()),'loyo_max':float(loyo.max()),'largest_day_removed_delta':removed_mean,'pass':bool(mean>=.05 and lower>0 and loyo.min()>0 and removed_mean>0),'eligible_days':len(calendar),'retained_detections':int(frame.n.sum())})
    tables={'independent_annual_indices':annual_rows,'independent_summary':summary,'independent_loyo':loyo_rows,'independent_maxday':removed_rows,'independent_exposure':exposure_rows,'independent_quality':quality_rows,'independent_exclusions':exclusion_rows}
    for name,rows in tables.items():pd.DataFrame(rows).to_csv(OUT/f'{name}.csv',index=False)
    same_streams=[s for s in STREAMS if all(r['pass'] for r in summary if r['stream']==s)]
    quality=pd.DataFrame(quality_rows)
    peryear=quality.groupby(['mask','stream','year']).agg(ordinary=('ordinary','sum'),valid=('valid','sum'),invalid_min=('invalid_fraction','min'),invalid_max=('invalid_fraction','max'))
    quality_pass=bool(((peryear.valid/peryear.ordinary>=.95)&(peryear.invalid_max-peryear.invalid_min<=.01)).all())
    result={'generated_utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':protocol_hash,'bootstrap_draws_raw_sha256':draw_hash,'bootstrap_dtype':str(draws.dtype),'checks':checks,'quality_pass':quality_pass,'same_passing_streams':same_streams,'scientific_pass':quality_pass and len(same_streams)>=2,'summary':summary,'independent_input_reconstruction':'verification/input_audit.json','runner_agreement':'pending'}
    (OUT/'independent_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

def compare(label,left,right,keys,columns,atol=1e-12,rtol=1e-12):
    assert not left.duplicated(keys).any(),label+' left duplicate keys'
    assert not right.duplicated(keys).any(),label+' right duplicate keys'
    m=left[keys+columns].merge(right[keys+columns],on=keys,how='outer',suffixes=('_independent','_runner'),indicator=True)
    check={'name':label,'rows':len(m),'keys_match':bool(m['_merge'].eq('both').all()),'fields':{}}
    for col in columns:
        a,b=m[col+'_independent'],m[col+'_runner']
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b) and a.dtype!=bool:
            check['fields'][col]={'pass':bool(np.allclose(a,b,atol=atol,rtol=rtol,equal_nan=False)),'max_absolute_difference':float((a-b).abs().max())}
        else:
            check['fields'][col]={'pass':bool(a.eq(b).all())}
    check['pass']=check['keys_match'] and all(c['pass'] for c in check['fields'].values())
    checks.append(check)

def compare_results(raw):
    independent=raw.rename(columns={'local_date':'date','n':'C','valid_n':'V','valid_frp':'F'})
    all_days=pd.MultiIndex.from_product([['Terra','Aqua','VIIRS'],pd.date_range('2013-01-01','2024-12-31')],names=['stream','date'])
    independent=independent.set_index(['stream','date']).reindex(all_days,fill_value=0).reset_index()
    runner=pd.read_csv(RUN/'daily_counts_and_frp.csv',parse_dates=['date'])
    compare('complete_daily_arrays',independent,runner,['stream','date'],['C','V','F'],atol=1e-7,rtol=1e-12)
    ia=pd.read_csv(OUT/'independent_annual_indices.csv').rename(columns={'ordinary_count_index':'C_index','valid_count_index':'V_index','frp_index':'F_index'})
    ra=pd.read_csv(RUN/'annual_weekday_profiles.csv')
    compare('all_annual_weekday_indices',ia,ra,['mask','stream','year','weekday'],['C_index','V_index','F_index'])
    s=pd.read_csv(OUT/'independent_summary.csv').rename(columns={'ordinary_count_index':'count_sunday','valid_count_index':'valid_count_sunday','frp_index':'frp_sunday','delta':'mean_delta','largest_day_removed_delta':'max_day_removal_mean_delta'})
    compare('complete_sunday_summary',s,pd.read_csv(RUN/'summary.csv'),['mask','stream'],['count_sunday','valid_count_sunday','frp_sunday','mean_delta','ci_lower','ci_upper','loyo_min','loyo_max','max_day_removal_mean_delta','pass'])
    lo=pd.read_csv(OUT/'independent_loyo.csv').rename(columns={'delta':'mean_delta'})
    compare('all_leave_one_year_out',lo,pd.read_csv(RUN/'leave_one_year_out.csv'),['mask','stream','omitted_year'],['mean_delta'])
    maxima=pd.read_csv(OUT/'independent_maxday.csv').rename(columns={'maximum_frp':'removed_F','maximum_share':'max_day_frp_share','delta_after_removal':'trimmed_delta'})
    compare('all_maximum_day_removals',maxima,pd.read_csv(RUN/'maximum_day_sensitivity.csv'),['mask','stream','year'],['removed_date','removed_F','max_day_frp_share','trimmed_delta'],atol=1e-7,rtol=1e-12)
    e=pd.read_csv(OUT/'independent_exposure.csv').drop(columns='stream').drop_duplicates()
    compare('all_exposure_counts',e,pd.read_csv(RUN/'exposure_days.csv'),['mask','year','weekday'],['days'],atol=0,rtol=0)
    a=pd.read_csv(OUT/'independent_exclusions.csv');b=pd.read_csv(RUN/'excluded_dates.csv')
    same_exclusions=a.sort_values(['mask','date']).reset_index(drop=True).equals(b.sort_values(['mask','date']).reset_index(drop=True))
    checks.append({'name':'all_excluded_dates','rows':len(a),'pass':same_exclusions})
    ida=np.random.Generator(np.random.PCG64(20261115)).integers(0,12,size=(50000,12));rda=np.load(RUN/'bootstrap_year_draws.npy')
    checks.append({'name':'joint_bootstrap_draws','draws':len(ida),'indices':int(ida.size),'pass':bool(np.array_equal(ida,rda)),'sha256_raw':hashlib.sha256(ida.tobytes()).hexdigest()})
    ir=json.loads((OUT/'independent_results.json').read_text());rr=json.loads((RUN/'results.json').read_text())
    checks.append({'name':'final_gates','pass':ir['scientific_pass']==(rr['status']=='PASS') and ir['same_passing_streams']==rr['passing_streams_both_masks']})
    payload={'generated_utc':datetime.now(timezone.utc).isoformat(),'pass':all(c['pass'] for c in checks),'checks':checks,'independent_script':'scripts/verify_frp_test.py','runner_script':'pipeline/review/frp_test.py','review':'Runner implementation read and reviewed; same-data paired numerator, full-calendar denominator, frozen shared year draws, multiplicity-adjusted quantiles, both masks, all LOYO and largest-day removal follow protocol. No runner functions imported.'}
    (OUT/'agreement.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    ir['runner_agreement']='passed' if payload['pass'] else 'failed'
    (OUT/'independent_results.json').write_text(json.dumps(ir,indent=2),encoding='utf-8')
    assert payload['pass'], 'Independent numerical agreement failed'
    return payload


def main():
    global CACHE,REPO,RUN,OUT
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-root',type=Path,default=CODE_ROOT/'data/processed/clean_cache_v2',help='Existing clean_cache_v2 directory or repository containing it; no downloads')
    ap.add_argument('--report-dir',type=Path,default=CODE_ROOT/'reports/review/frp')
    args=ap.parse_args()
    CACHE=args.data_root.resolve()
    if (CACHE/'data/processed/clean_cache_v2').is_dir():CACHE=CACHE/'data/processed/clean_cache_v2'
    if not CACHE.is_dir():raise SystemExit('Existing clean-cache directory not found')
    REPO=CACHE.parents[2]
    RUN=args.report_dir.resolve()
    OUT=RUN/'verification'
    OUT.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat()
    raw=audit_inputs()
    result=analyze(raw)
    agreement=compare_results(raw)
    audit=json.loads((OUT/'input_audit.json').read_text())
    receipt={'status':'PASS' if agreement['pass'] and result['quality_pass'] else 'FAIL','scientific_test_status':'PASS' if result['scientific_pass'] else 'FAIL','verification_started_utc':started,'verification_finished_utc':datetime.now(timezone.utc).isoformat(),'chronology':'Portable independent reproduction of an already-known outcome. Original local protocol was frozen 2026-11-14T18:57:23.284Z before original effects; Git receipt 92626ed2f76fc6ab1bcefa6254d49609b7c6b982 was committed after the outcome.','protocol_sha256':EXPECTED_PROTOCOL,'script':'scripts/verify_frp_test.py','script_sha256':hashfile(Path(__file__)),'passing_streams_both_masks':result['same_passing_streams'],'official_unmasked_daytime_reconciliation':audit['official_unmasked_daytime_reconciliation'],'checks':agreement['checks'],'detailed_receipt':'verification/agreement.json','data_limitations':['Independent clean-cache reaggregation, source hashes and stored IANA-zone timestamp conversion; not independent coordinate-to-timezone mapping or NASA retrieval.','Twelve annual resampling blocks; related satellite streams are not independent experiments; no cloud/weather correction.']}
    receipt['analysis_script_sha256']=hashfile(CODE_ROOT/'pipeline/review/frp_test.py')
    receipt['verified_artifacts_sha256']={name:hashfile(RUN/name) for name in ['data_gate.json','input_manifest.json','daily_counts_and_frp.csv','summary.csv','annual_weekday_profiles.csv','annual_contrasts.csv','maximum_day_sensitivity.csv','leave_one_year_out.csv','exposure_days.csv','excluded_dates.csv','bootstrap_year_draws.npy']}
    (RUN/'independent_verification.json').write_text(json.dumps(receipt,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'verification':receipt['status'],'scientific_test':receipt['scientific_test_status'],'passing_streams':receipt['passing_streams_both_masks'],'official_counts':receipt['official_unmasked_daytime_reconciliation']},indent=2))

if __name__=='__main__':main()
