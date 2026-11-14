from pathlib import Path
from types import SimpleNamespace
import json
import pytest
from pipeline.streaming import reproduce as module


def options(output, manifest=None):
    return SimpleNamespace(output=str(output),countries=["Nepal"],source_manifest=str(manifest) if manifest else None,
                           workers=3,chunk_size=200000,baseline_reports=None,locked_evaluation="saved-lock",
                           model_revision="fixture-v1",baseline_commit="old",)


@pytest.mark.parametrize("reuse_manifest",[False,True])
def test_one_command_sequences_steps_and_preserves_locked_reuse(tmp_path,reuse_manifest):
    events = []
    source = tmp_path/"existing.json"
    source.write_text("{}")
    def download(countries,years,destination,**kwargs):
        assert not reuse_manifest
        assert countries==["Nepal"] and list(years)==list(range(2001,2026))
        assert kwargs=={"workers":3,"reserve_gib":10}
        destination.mkdir()
        (destination/"manifest.json").write_text("{}")
        events.append("download")
    def prepare(manifest,countries,destination,chunk_size,write_clean):
        assert Path(manifest).exists() and chunk_size==200000 and not write_clean
        destination.mkdir()
        events.append("prepare")
        return {"cleaned_rows":17}
    def build(args):
        assert args.locked_evaluation=="saved-lock" and args.model_revision=="fixture-v1"
        assert args.expected_countries==["Nepal"] and not args.no_encode
        assert args.science_checks
        (Path(args.output)/"public/data").mkdir(parents=True)
        events.append("build")
        return 0
    def site(data,destination):
        assert data.is_dir()
        events.append("site")
        return {"within_50MiB":True,"within_25MiB_per_file":True,"bytes":100}
    output = tmp_path/"new"
    result = module.reproduce(options(output,source if reuse_manifest else None),download_fn=download,prepare_fn=prepare,build_fn=build,site_fn=site)
    assert result==0
    assert events==(["prepare","build","site"] if reuse_manifest else ["download","prepare","build","site"])
    report = json.loads((output/"REPRODUCTION.json").read_text())
    assert report["locked_evaluation_reused"] and report["cleaned_detections"]==17


def test_fresh_output_guard_runs_before_network(tmp_path):
    def forbidden(*args,**kwargs):
        raise AssertionError("No step may run for an existing output")
    with pytest.raises(ValueError,match="fresh reproduction"):
        module.reproduce(options(tmp_path),download_fn=forbidden)


def test_isolated_frontend_control_flow_uses_install_map_and_build(tmp_path,monkeypatch):
    root = tmp_path/"repo"
    source = root/"web"
    (source/"src").mkdir(parents=True)
    (source/"src/main.ts").write_text("export {}")
    (source/"package.json").write_text("{}")
    (source/"package-lock.json").write_text("{}")
    (source/"index.html").write_text("<html></html>")
    (source/"public/data").mkdir(parents=True)
    (source/"public/data/stale.json").write_text("old")
    (root/"scripts").mkdir()
    (root/"scripts/prepare-map.mjs").write_text("//fixture")
    data = tmp_path/"newdata"
    data.mkdir()
    (data/"index.json").write_text("new")
    monkeypatch.setattr(module,"ROOT",root)
    monkeypatch.setattr(module.shutil,"which",lambda name:name)
    calls = []
    def run(command,**kwargs):
        assert kwargs["check"]
        calls.append(command)
        if command[-2:]==["run","build"]:
            dist = Path(kwargs["cwd"])/"dist"
            dist.mkdir()
            (dist/"index.html").write_text("ready")
    monkeypatch.setattr(module.subprocess,"run",run)
    target = tmp_path/"site"
    result = module.build_site(data,target)
    assert calls[0][-1]=="ci" and Path(calls[1][1]).is_absolute() and calls[2][-2:]==["run","build"]
    assert (target/"web/public/data/index.json").read_text()=="new"
    assert not (target/"web/public/data/stale.json").exists()
    assert (source/"public/data/stale.json").read_text()=="old"
    assert result["within_50MiB"] and result["within_25MiB_per_file"]


def test_supplemental_reports_preserve_locked_model_and_separate_output(tmp_path,monkeypatch):
    from pipeline.streaming import __main__ as entry
    from pipeline import synthetic
    calls = []
    monkeypatch.setattr(synthetic,"save_switch_check",lambda output:calls.append(("synthetic",output)))
    monkeypatch.setattr(entry.subprocess,"run",lambda command,**kwargs:calls.append((command,kwargs)))
    model = tmp_path/"locked_model.json"
    model.write_text("unchanged")
    entry.additional_reports(["p1","p2"],["a1","a2"],model,tmp_path/"science",tmp_path/"reports")
    assert calls[0]==("synthetic",tmp_path/"reports")
    command,kwargs = calls[1]
    assert command[1:3]==["-m","pipeline.validation.science_checks"]
    assert command[command.index("--preparations")+1:command.index("--analyses")]==["p1","p2"]
    assert command[-1]==str((tmp_path/"science").resolve()) and kwargs["check"]
    assert model.read_text()=="unchanged"
