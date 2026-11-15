"""Render all seven weekday profiles after independent count/FRP verification.

Usage: python scripts/plot_frp_test.py --report-dir reports/review/frp
"""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
STREAMS=['Terra','Aqua','VIIRS']
DISPLAY={'Terra':'Terra MODIS','Aqua':'Aqua MODIS','VIIRS':'S-NPP VIIRS'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir',type=Path,default=ROOT/'reports/review/frp')
    args=parser.parse_args()
    out=args.report_dir.resolve()
    verification=json.loads((out/'independent_verification.json').read_text())
    assert verification['status']=='PASS','Independent numerical verification must pass first'
    data=pd.read_csv(out/'annual_weekday_profiles.csv')
    data=data.loc[data['mask'].eq('primary')]
    assert data.groupby(['stream','weekday']).size().eq(12).all()
    means=data.groupby(['stream','weekday'])[['V_index','F_index']].mean()
    summary=pd.read_csv(out/'summary.csv').query("mask == 'primary'").set_index('stream')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#B6C4CB','text.color':'#152F40','axes.labelcolor':'#152F40','xtick.color':'#425B6C','ytick.color':'#425B6C'})
    fig,axes=plt.subplots(3,1,figsize=(11,11.5),sharex=True,sharey=True,facecolor='#FAFCFD')
    fig.subplots_adjust(left=.105,right=.86,top=.81,bottom=.17,hspace=.34)
    maximum=float(means.max().max());minimum=float(means.min().min())
    lower=min(.5,np.floor(minimum*10)/10-.05);upper=max(1.3,np.ceil(maximum*10)/10+.05)
    x=np.arange(7)
    for axis,stream in zip(axes,STREAMS):
        axis.set_facecolor('#FAFCFD')
        row=means.loc[stream]
        axis.axhline(1,color='#9AABB6',ls='--',lw=1,zorder=0)
        axis.axvspan(5.7,6.3,color='#EAF0F3',zorder=0)
        axis.plot(x,row.V_index.to_numpy(),'-o',color='#315E89',lw=2.3,markersize=5,label='Detection count (valid FRP)')
        axis.plot(x,row.F_index.to_numpy(),'-s',color='#C36828',lw=2.3,markersize=4.5,label='Summed observed FRP')
        passed=bool(summary.loc[stream,'pass'])
        detail='Sunday contrast passes the fixed test' if passed else 'Sunday contrast interval includes zero'
        axis.set_title(f'{DISPLAY[stream]}  ·  {detail}',loc='left',fontsize=12,fontweight='bold',pad=9)
        axis.set_ylabel('Weekday index',labelpad=12)
        axis.grid(axis='y',color='#E3E9ED',lw=.7)
        axis.set_ylim(lower,upper);axis.set_xlim(-.12,6.3)
        axis.tick_params(axis='both',length=0)
        axis.set_xticks(x,['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
        axis.tick_params(axis='x',labelbottom=True,pad=6)
        for metric,color in [('V_index','#315E89'),('F_index','#C36828')]:
            v=float(row.loc[6,metric])
            axis.annotate(f'{v:.3f}',xy=(6,v),xytext=(19,0),textcoords='offset points',ha='left',va='center',color=color,fontsize=11,fontweight='bold',annotation_clip=False)
    fig.text(.065,.953,'The weekday pattern depends on the measure',fontsize=21,fontweight='bold')
    fig.text(.065,.913,'REAL FIRMS DATA, US daytime 2013-2024',fontsize=13,fontweight='bold')
    fig.text(.065,.876,'Vegetation detections · primary common-date outage mask · average weekday = 1.0',fontsize=11,color='#425B6C')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower left',bbox_to_anchor=(.065,.095),ncol=2,frameon=False,fontsize=11)
    fig.text(.065,.045,'Profiles are equal-weight means of 12 annual weekday indices; the prespecified test concerns Sunday only.\nAll included detections have valid FRP. FRP is sampled radiative power, not energy, emissions or fire counts.\nThe related satellite streams corroborate one another; they are not independent experiments.',fontsize=9.5,color='#425B6C',va='bottom',linespacing=1.5)
    for ext in ['png','svg']:
        kwargs={'dpi':160} if ext=='png' else {'metadata':{'Creator':'FIRETRACE scripts/plot_frp_test.py','Description':'Independently verified primary weekday count and observed FRP indices; original outcome known before portable packaging.'}}
        fig.savefig(out/f'count_vs_frp_weekdays.{ext}',facecolor=fig.get_facecolor(),**kwargs)
    plt.close(fig)
    print('Wrote count_vs_frp_weekdays.png and count_vs_frp_weekdays.svg')

if __name__=='__main__':main()
