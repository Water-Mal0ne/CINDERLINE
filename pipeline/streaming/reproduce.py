"""One command from official annual archives to an isolated, built website."""
from pathlib import Path
from types import SimpleNamespace
import json
import os
import shutil
import subprocess

from .aggregate_archives import ROOT, prepare, write_json
from .download_guarded import download


def build_site(public_data, directory):
    directory = Path(directory).resolve()
    public_data = Path(public_data).resolve()
    web = directory/"web"
    web.mkdir(parents=True)
    source = ROOT/"web"
    shutil.copytree(source/"src",web/"src")
    for pattern in ["package*.json","tsconfig*.json","vite.config.*","index.html"]:
        for path in source.glob(pattern):
            if path.is_file():
                shutil.copyfile(path,web/path.name)
    if (source/"public").exists():
        shutil.copytree(source/"public",web/"public",ignore=shutil.ignore_patterns("data"))
    shutil.copytree(public_data,web/"public/data")
    scripts = directory/"scripts"
    scripts.mkdir()
    shutil.copyfile(ROOT/"scripts/prepare-map.mjs",scripts/"prepare-map.mjs")
    npm = shutil.which("npm.cmd" if os.name=="nt" else "npm")
    node = shutil.which("node")
    if not npm or not node:
        raise RuntimeError("Node and npm are required to build the isolated frontend")
    subprocess.run([npm,"ci"],cwd=web,check=True)
    subprocess.run([node,str(scripts/"prepare-map.mjs")],cwd=directory,check=True)
    subprocess.run([npm,"run","build"],cwd=web,check=True)
    dist = web/"dist"
    files = [path for path in dist.rglob("*") if path.is_file()]
    total = sum(path.stat().st_size for path in files)
    largest = max(files,key=lambda path:path.stat().st_size)
    return {"dist":str(dist.resolve()),"files":len(files),"bytes":total,"largest_file":str(largest.relative_to(dist)),
            "largest_file_bytes":largest.stat().st_size,"within_50MiB":total<=50*1024**2,
            "within_25MiB_per_file":largest.stat().st_size<=25*1024**2}


def reproduce(args, *, download_fn=download, prepare_fn=prepare, build_fn=None, site_fn=build_site):
    if build_fn is None:
        from .__main__ import build
        build_fn = build
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError("Use a fresh reproduction directory; existing data and builds are preserved")
    output.mkdir(parents=True)
    if args.source_manifest:
        manifest = Path(args.source_manifest).resolve()
        if not manifest.is_file():
            raise FileNotFoundError(manifest)
    else:
        raw = output/"archives"
        download_fn(args.countries,range(2001,2026),raw,workers=args.workers,reserve_gib=10)
        manifest = raw/"manifest.json"
    prepared = output/"prepared"
    preparation = prepare_fn(manifest,args.countries,prepared,args.chunk_size,False)
    pipeline_output = output/"pipeline"
    options = SimpleNamespace(preparations=[str(prepared)],analyses=None,output=str(pipeline_output),
                              baseline_reports=args.baseline_reports,locked_evaluation=args.locked_evaluation,
                              model_revision=args.model_revision,baseline_commit=args.baseline_commit,
                              expected_countries=args.countries,no_encode=False,science_checks=True)
    code = build_fn(options)
    if code:
        write_json(output/"REPRODUCTION.json",{"status":"payload_budget_failed","pipeline_exit_code":code,
                                              "publication":"No deployment attempted."})
        return code
    site = site_fn(pipeline_output/"public/data",output/"site")
    success = site["within_50MiB"] and site["within_25MiB_per_file"]
    report = {"status":"ready" if success else "final_site_budget_failed","source_manifest":str(manifest),
              "cleaned_detections":preparation["cleaned_rows"],"site":site,
              "locked_evaluation_reused":bool(args.locked_evaluation),
              "publication":"Built in a fresh directory; production files are unchanged and no deployment is attempted."}
    write_json(output/"REPRODUCTION.json",report)
    print(json.dumps(report,indent=2))
    return 0 if success else 2
