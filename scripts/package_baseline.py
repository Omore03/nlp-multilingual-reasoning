"""Package the clean local baseline branch for review; never writes to a remote."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE='01f52473ba2966d68f0b6a561ca348d9006d9484'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def main():
    if git('diff','--name-only') or git('diff','--cached','--name-only'):
        raise ValueError('Commit reviewed tracked changes before packaging')
    files=[x.decode() for x in git('ls-files','-z').split(b'\0') if x]
    for name in files:
        path=Path(name)
        if (path.name=='.env' or (path.name.startswith('.env.') and path.name!='.env.example')
            or any(p in path.parts for p in ('.git','.venv','__pycache__','tmp','output','models','.cache'))
            or path.suffix in ('.gguf','.safetensors','.pyc')):
            raise ValueError(f'Excluded private/runtime artifact is tracked: {name}')
    out=ROOT/'output/review';out.mkdir(parents=True,exist_ok=True)
    release={'date':'2026-11-25','branch':git('branch','--show-current').decode().strip(),
             'base_sha':BASE,'final_sha':git('rev-parse','HEAD').decode().strip(),
             'local_main_sha':git('rev-parse','main').decode().strip(),
             'origin_main_sha':git('rev-parse','origin/main').decode().strip(),
             'remote_writes':'intermediate-stage published; no main merge','submission':'not performed',
             'scope':'18 approved demonstrations, 10 dev questions; seven completed saved runs, 380 scored records',
             'source_files':len(files)}
    release_bytes=(json.dumps(release,indent=2)+'\n').encode()
    (out/'REVIEW_RELEASE.json').write_bytes(release_bytes)
    patch=git('diff','--binary',BASE,'HEAD')
    (out/'baseline_vs_01f5247.patch').write_bytes(patch)
    report=(ROOT/'BASELINE_COMPLETION_REPORT.md').read_text()+f"\n## Packaged branch head\n\nFinal branch SHA: `{release['final_sha']}`. Published on intermediate-stage; no main merge or LMS submission has occurred. This packaging note is appended after the local commit.\n"
    (out/'BASELINE_COMPLETION_REPORT.md').write_text(report)
    contents={name:(ROOT/name).read_bytes() for name in files}
    contents.update({'REVIEW_RELEASE.json':release_bytes,'BASELINE_COMPLETION_REPORT.md':report.encode(),
                     'baseline_vs_01f5247.patch':patch})
    sums=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(contents.items()))
    contents['SHA256SUMS.txt']=sums.encode()
    zip_path=out/'NLP_Baseline_Review_2026-11-25.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(contents.items()):z.writestr(name,data)
    with zipfile.ZipFile(zip_path) as z:
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            digest,name=line.split('  ',1)
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise ValueError('Package hash mismatch')
    (out/'NLP_Baseline_Review_2026-11-25.zip.sha256').write_text(hashlib.sha256(zip_path.read_bytes()).hexdigest()+'  '+zip_path.name+'\n')
    print(json.dumps({**release,'package':str(zip_path),'package_bytes':zip_path.stat().st_size}))


if __name__=='__main__':main()
