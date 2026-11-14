import type {monthly} from './utils';

interface ComparisonScope {regionId: string; regionName: string; cellId: string; label: string}

/** Keep geography with exported values, including when files are renamed. */
export function buildMonthlyExport(points: ReturnType<typeof monthly>, scope: ComparisonScope) {
  const fields=['region','region_name','cell_id','month','raw_sensor_switch_detections','aqua_equivalent_detections','observed_aqua_detections','raw_days','harmonized_days','aqua_days','data_label'];
  const quote=(value: unknown)=>`"${String(value??'').replaceAll('"','""')}"`;
  const lines=points.map(p=>[scope.regionId,scope.regionName,scope.cellId,p.date,p.raw,p.harmonized,p.aqua,p.rawDays,p.harmonizedDays,p.aquaDays,scope.label].map(quote).join(','));
  const safe=(value: string)=>value.replace(/[^A-Za-z0-9._-]/g,'_');
  const location=scope.cellId==='ALL'?'whole-region':`cell_${safe(scope.cellId)}`;
  const range=points.length?`_${points[0].date}_${points[points.length-1].date}`:'';
  return {filename:`FIRETRACE_${safe(scope.regionId)}_${location}${range}_monthly.csv`,content:'\uFEFF'+[fields.join(','),...lines].join('\r\n')};
}
