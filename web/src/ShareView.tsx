import {useEffect,useId,useRef,useState} from 'react';
import {Check,Link2,X} from 'lucide-react';
import './ShareView.css';

export default function ShareView({url,disabledReason}:{url:string|null;disabledReason?:string}) {
  const [open,setOpen]=useState(false),[status,setStatus]=useState(''),[copied,setCopied]=useState(false);
  const root=useRef<HTMLDivElement>(null),field=useRef<HTMLInputElement>(null),trigger=useRef<HTMLButtonElement>(null),id=useId(),attempt=useRef(0);
  useEffect(()=>{attempt.current++;setOpen(false);setCopied(false);setStatus('');},[url]);
  useEffect(()=>()=>{attempt.current++;},[]);
  useEffect(()=>{if(open&&status.startsWith('Copy was unavailable')){field.current?.focus();field.current?.select();}},[open,status]);
  useEffect(()=>{
    if(!open)return;
    const dismissOutside=(event:Event)=>{
      if(root.current?.contains(event.target as Node))return;
      attempt.current++;setOpen(false);
    };
    document.addEventListener('pointerdown',dismissOutside);
    document.addEventListener('focusin',dismissOutside);
    return()=>{document.removeEventListener('pointerdown',dismissOutside);document.removeEventListener('focusin',dismissOutside);};
  },[open]);
  function close(){attempt.current++;setOpen(false);trigger.current?.focus();}
  async function copy() {
    if(!url)return;
    const current=++attempt.current;
    setOpen(true);setCopied(false);setStatus('Copying link…');
    try {
      if(!navigator.clipboard?.writeText)throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(url);
      if(current===attempt.current){setCopied(true);setStatus('Link copied.');}
    } catch {
      if(current===attempt.current){setStatus('Copy was unavailable. Select and copy the link below.');field.current?.focus();field.current?.select();}
    }
  }
  return <div ref={root} className="share-view" onKeyDown={event=>{if(event.key==='Escape'&&open){event.preventDefault();event.stopPropagation();close();}}}>
    <button ref={trigger} className="button subtle" onClick={copy} disabled={!url} title={url?'Copy a link to these filters and evidence':disabledReason||'Wait for the selected observations to load.'} aria-expanded={open} aria-controls={id}>
      {copied?<Check size={16}/>:<Link2 size={16}/>} Share this view
    </button>
    {open&&url&&<div className="share-panel" id={id} role="region" aria-label="Share details">
      <div className="share-panel-heading"><strong>Link to this exploration</strong><button className="icon-button" onClick={close} aria-label="Close share details"><X size={16}/></button></div>
      <p role="status" aria-live="polite">{status}</p>
      <label htmlFor={`${id}-link`}>Shareable link</label>
      <input ref={field} id={`${id}-link`} type="text" readOnly value={url} onFocus={e=>e.currentTarget.select()}/>
      <p className="share-note">Restores filters, page, scale and open week evidence using current published data. Globe camera, annual-cell selection and Earth/table view reset.</p>
    </div>}
  </div>;
}
