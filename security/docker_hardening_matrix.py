import json, sqlite3, subprocess, tempfile, shutil
from pathlib import Path

IMG="anonymization-trial"
def policy(*vals):
    return {"version":1,"protected_values":[],"sensitive_values":[{"rule_id":f"r{i}","subject_id":"s","type":"name","value":v} for i,v in enumerate(vals)]}

def run_case(name, build, expect):
    root=Path(tempfile.mkdtemp())
    inp=root/"input"; out=root/"output"; (inp/"corpus").mkdir(parents=True); out.mkdir()
    build(inp)
    p=subprocess.run(["docker","run","--rm","-v",f"{inp}:/trial/input:ro","-v",f"{out}:/trial/output",IMG,"run"],
                     capture_output=True,text=True)
    corpus=out/"corpus"
    got_output = corpus.exists() and any(corpus.rglob("*"))
    # read all output bytes for leak scan
    blob=b""
    if corpus.exists():
        for f in corpus.rglob("*"):
            if f.is_file(): blob+=f.read_bytes()
    verdict = expect(p.returncode, got_output, blob, p.stderr+p.stdout)
    print(f"{'PASS' if verdict[0] else 'FAIL'} | {name}: {verdict[1]}")
    shutil.rmtree(root, ignore_errors=True)
    return verdict[0]

def anon(secret):
    # expect: exit 0, output present, secret bytes absent
    return lambda rc,got,blob,log: (rc==0 and got and secret.encode() not in blob,
        f"exit={rc} output={got} '{secret}'absent={secret.encode() not in blob}")
def failclosed():
    return lambda rc,got,blob,log: (rc!=0 and not got,
        f"exit={rc} output_corpus={got} (want exit!=0,no corpus)")
def survives(tbl):
    # SQL injection: victim table must survive; scan handled specially
    return None

cases=[]
# 1 typed int/float phone
def b1(inp):
    (inp/"policy.json").write_text(json.dumps(policy("5551234567")))
    (inp/"corpus/p.json").write_text(json.dumps({"i":5551234567,"f":5551234567.0,"s":"5551234567"}))
    c=sqlite3.connect(inp/"corpus/a.sqlite"); c.executescript("CREATE TABLE t(id INTEGER PRIMARY KEY, ph INTEGER); INSERT INTO t VALUES(1,5551234567);"); c.commit(); c.close()
cases.append(("1 typed int/float phone", b1, anon("5551234567")))
# 2 BLOB
def b2(inp):
    (inp/"policy.json").write_text(json.dumps(policy("Alice")))
    c=sqlite3.connect(inp/"corpus/a.sqlite"); c.execute("CREATE TABLE t(b BLOB)"); c.execute("INSERT INTO t VALUES(?)",(b"Alice",)); c.commit(); c.close()
cases.append(("2 SQLite BLOB", b2, failclosed()))
# 3 NFC/NFD
def b3(inp):
    import unicodedata
    (inp/"policy.json").write_text(json.dumps(policy(unicodedata.normalize("NFC","José Malké"))))
    (inp/"corpus/c.json").write_text(json.dumps({"who":unicodedata.normalize("NFD","José Malké")}))
import unicodedata
cases.append(("3 NFC/NFD name", b3, anon(unicodedata.normalize("NFD","José Malké"))))
# 4 view reconstruction
def b4(inp):
    (inp/"policy.json").write_text(json.dumps(policy("Alice")))
    c=sqlite3.connect(inp/"corpus/a.sqlite"); c.executescript("CREATE TABLE t(a TEXT,b TEXT); INSERT INTO t VALUES('Al','ice'); CREATE VIEW v AS SELECT a||b AS f FROM t;"); c.commit(); c.close()
cases.append(("4 view reconstruction", b4, failclosed()))
# 5 freelist residue
def b5(inp):
    (inp/"policy.json").write_text(json.dumps(policy("Alice")))
    c=sqlite3.connect(inp/"corpus/a.sqlite"); c.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, name TEXT)")
    for i in range(300): c.execute("INSERT INTO t(name) VALUES(?)",(f"F{i}",))
    c.execute("INSERT INTO t(name) VALUES('Alice')"); c.commit(); c.close()
cases.append(("5 freelist residue", b5, anon("Alice")))
# 6 hostile: corrupt DB -> integrity fail-closed
def b6(inp):
    (inp/"policy.json").write_text(json.dumps(policy("Alice")))
    ap=inp/"corpus/a.sqlite"
    c=sqlite3.connect(ap); c.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, name TEXT)")
    for i in range(500): c.execute("INSERT INTO t(name) VALUES(?)",(f"r{i}Alice",))
    c.commit(); c.close()
    d=ap.read_bytes(); ap.write_bytes(d[:len(d)//2])
cases.append(("6 malformed/truncated SQLite", b6, failclosed()))
# 8 expression index
def b8(inp):
    (inp/"policy.json").write_text(json.dumps(policy("SECRET")))
    c=sqlite3.connect(inp/"corpus/a.sqlite"); c.executescript("CREATE TABLE t(x TEXT); INSERT INTO t VALUES('clean'); CREATE INDEX i ON t(char(83,69,67,82,69,84));"); c.commit(); c.close()
cases.append(("8 expression index", b8, failclosed()))
# 9 non-deterministic view
def b9(inp):
    (inp/"policy.json").write_text(json.dumps(policy("SECRET")))
    c=sqlite3.connect(inp/"corpus/a.sqlite"); c.executescript("CREATE TABLE t(x TEXT); INSERT INTO t VALUES('clean'); CREATE VIEW v AS SELECT CASE WHEN (abs(random())%2)=0 THEN char(83,69,67,82,69,84) ELSE 'clean' END AS x;"); c.commit(); c.close()
cases.append(("9 non-deterministic view", b9, failclosed()))
# 10 computed DEFAULT
def b10(inp):
    (inp/"policy.json").write_text(json.dumps(policy("SECRET")))
    c=sqlite3.connect(inp/"corpus/a.sqlite"); c.executescript("CREATE TABLE t(x TEXT DEFAULT (char(83,69,67,82,69,84)));"); c.commit(); c.close()
cases.append(("10 computed DEFAULT", b10, failclosed()))
# 11 numeric alias 1e20
def b11(inp):
    (inp/"policy.json").write_text(json.dumps(policy("100000000000000000000")))
    (inp/"corpus/c.json").write_text(json.dumps({"x":1e20}))
cases.append(("11 numeric 1e20 alias", b11, anon("100000000000000000000")))

results=[run_case(n,b,e) for n,b,e in cases]

# 7 SQL identifier injection: victim table must survive
def b7(inp):
    (inp/"policy.json").write_text(json.dumps(policy("Alice")))
    c=sqlite3.connect(inp/"corpus/a.sqlite")
    c.execute('CREATE TABLE "w""; DROP TABLE victim; --" (name TEXT)')
    c.execute('CREATE TABLE victim (x TEXT)')
    c.execute('INSERT INTO "w""; DROP TABLE victim; --" VALUES(?)',("Alice",))
    c.commit(); c.close()
root=Path(tempfile.mkdtemp()); inp=root/"input"; out=root/"output"; (inp/"corpus").mkdir(parents=True); out.mkdir()
b7(inp)
subprocess.run(["docker","run","--rm","-v",f"{inp}:/trial/input:ro","-v",f"{out}:/trial/output",IMG,"run"],capture_output=True,text=True)
victim_ok=False
if (out/"corpus/a.sqlite").exists():
    o=sqlite3.connect(out/"corpus/a.sqlite"); tbls={r[0] for r in o.execute("SELECT name FROM sqlite_master WHERE type='table'")}; o.close()
    victim_ok="victim" in tbls
print(f"{'PASS' if victim_ok else 'FAIL'} | 7 SQL identifier injection: victim table survived={victim_ok}")
results.append(victim_ok)
shutil.rmtree(root, ignore_errors=True)

print(f"\nALL {sum(results)}/{len(results)} holes verified through docker run")
import sys; sys.exit(0 if all(results) else 1)
