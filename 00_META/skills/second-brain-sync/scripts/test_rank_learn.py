"""Testes do ranking que aprende (vault_rank.sh lê <sid>.injected e <sid>.opened):
python3 -m unittest discover -s 00_META/skills/second-brain-sync/scripts -v

Todo teste usa estado temporário e `SECOND_BRAIN_RANK_NOW` fixo; nenhum lê o estado real da máquina.
"""

import hashlib
import json
import os
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
import unicodedata
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
RANK = SCRIPTS / "vault_rank.sh"
HINT = SCRIPTS / "prompt_hint.sh"

NOW = 1_800_000_000
DAY = 86400
QUERY = "importar issues jira rest"
HEADER = "| Path | Title | Tags | Created | Provenance | Confidence | Seen in | Summary |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n"
ROWS = [
    ("20/a.md", "Importar issues no Jira por REST", "jira, rest", "medium", "Importar tarefas em lote."),
    ("20/d.md", "Importador CSV do Jira", "jira, csv", "medium", "Parent aponta o issue id."),
    ("20/e.md", "Importar issues variante", "jira", "low", "Nota gêmea sobre rest."),
    ("20/f.md", "Importar issues variante", "jira", "low", "Nota gêmea sobre rest."),
]


def awk_variants():
    """Diretórios de PATH que forçam gawk, mawk ou o awk padrão (o script chama `awk` pelo nome)."""
    found = {name: shutil.which(name) for name in ("gawk", "mawk")}
    return {name: path for name, path in found.items() if path} or {"awk": shutil.which("awk")}


class RankLearnBase(unittest.TestCase):
    ROWS = ROWS

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.manifests = root / "by_type"
        self.manifests.mkdir()
        self.write_manifest(self.ROWS)
        self.state = root / "state"
        self.state.mkdir()
        self.bin = root / "bin"
        self.bin.mkdir()
        self.env = {
            **os.environ,
            "SECOND_BRAIN_MANIFEST_DIR": str(self.manifests),
            "SECOND_BRAIN_STATE_DIR": str(self.state),
            "SECOND_BRAIN_RANK_NOW": str(NOW),
            "HOME": str(root / "home"),
        }
        for var in ("SECOND_BRAIN_RANK_LEARN", "SECOND_BRAIN_RANK_MIN_INJECTIONS"):
            self.env.pop(var, None)
        self.sid = 0

    def write_manifest(self, rows):
        lines = [f"| {p} | {t} | {g} | 2026-01-01 | x | {c} | | {s} |" for p, t, g, c, s in rows]
        (self.manifests / "pattern.md").write_text(HEADER + "\n".join(lines) + "\n", encoding="utf-8")

    def session(self, injected, opened=(), age_days=0.0, name=None, opened_age_days=None):
        """Cria <name>.injected e, se `opened`, <name>.opened; a idade vem da mtime."""
        self.sid += 1
        name = name or f"s{self.sid}"
        inj = self.state / f"{name}.injected"
        inj.write_text("".join(f"{n}\n" for n in injected), encoding="utf-8")
        os.utime(inj, (NOW - age_days * DAY, NOW - age_days * DAY))
        if opened:
            op = self.state / f"{name}.opened"
            op.write_text("".join(f"{n}\n" for n in opened), encoding="utf-8")
            old = age_days if opened_age_days is None else opened_age_days
            os.utime(op, (NOW - old * DAY, NOW - old * DAY))
        return name

    def sessions(self, note, count, opened=0, age_days=0.0):
        for i in range(count):
            self.session([note], [note] if i < opened else (), age_days)

    def run_rank(self, *args, env=None, awk=None, query=QUERY, timeout=20):
        full = dict(env or self.env)
        if awk:
            shim = self.bin / f"awk_{Path(awk).name}"
            shim.mkdir(exist_ok=True)
            link = shim / "awk"
            if not link.exists():
                link.symlink_to(awk)
            full["PATH"] = f"{shim}:{full['PATH']}"
        done = subprocess.run(["bash", str(RANK), *args, "--", query], capture_output=True, text=True, env=full,
                              stdin=subprocess.DEVNULL, timeout=timeout, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stderr, "")
        return done.stdout

    def rows(self, *args, **kwargs):
        return [line.split("\t") for line in self.run_rank(*args, **kwargs).splitlines()]

    def scores(self, *args, **kwargs):
        return {r[1]: float(r[0]) for r in self.rows(*args, **kwargs)}

    def base(self, *args, **kwargs):
        env = {**(kwargs.pop("env", None) or self.env), "SECOND_BRAIN_RANK_LEARN": "0"}
        return self.scores(*args, env=env, **kwargs)

    def assertFactor(self, factor, note="20/a.md", *args, **kwargs):
        base = self.base(*args, **kwargs)[note]
        self.assertAlmostEqual(self.scores(*args, **kwargs)[note], base * factor, delta=0.002)

    def for_each_awk(self):
        for name, path in awk_variants().items():
            with self.subTest(awk=name):
                yield path


class FormulaTest(RankLearnBase):
    def test_fixture_base_ranking_is_pinned_to_the_script_without_learning(self):
        # a ordem sem ajuste (a mesma de 683caed) é a referência dos outros testes; e e f empatam no score
        base = self.base()
        self.assertEqual([r[1] for r in self.base_rows()], ["20/a.md", "20/e.md", "20/f.md", "20/d.md"])
        self.assertEqual(base["20/e.md"], base["20/f.md"])
        self.assertGreater(base["20/a.md"], base["20/e.md"])

    def test_nine_injections_leave_the_output_identical_and_ten_apply_the_floor(self):
        for awk in self.for_each_awk():
            self.sessions("20/a.md", 9)
            self.assertEqual(self.run_rank(awk=awk), self.run_rank(awk=awk, env={**self.env, "SECOND_BRAIN_RANK_LEARN": "0"}))
            self.sessions("20/a.md", 1)
            self.assertFactor(0.8, awk=awk)
            shutil.rmtree(self.state)
            self.state.mkdir()

    def test_ratio_zero_half_and_one_map_to_the_band(self):
        for awk in self.for_each_awk():
            for opened, factor in ((0, 0.8), (5, 1.0), (10, 1.2)):
                shutil.rmtree(self.state)
                self.state.mkdir()
                self.sessions("20/a.md", 10, opened=opened)
                self.assertFactor(factor, awk=awk)

    def test_ratio_zero_never_zeroes_a_note_even_with_500_sessions(self):
        self.sessions("20/a.md", 500)
        score = self.scores()["20/a.md"]
        self.assertGreater(score, 0)
        self.assertFactor(0.8)

    def test_factor_stays_in_the_band_for_odd_state(self):
        # nota repetida em 50 linhas, .opened com a nota duplicada, .opened de sessão sem a nota e .opened sem .injected
        for i in range(12):
            self.session(["20/a.md"] * 50, ["20/a.md"] * 50)
        self.session(["20/d.md"], ["20/a.md"] * 5)
        (self.state / "orphan.opened").write_text("20/a.md\n" * 30, encoding="utf-8")
        base = self.base()["20/a.md"]
        self.assertAlmostEqual(self.scores()["20/a.md"], base * 1.2, delta=0.002)
        self.assertLessEqual(self.scores()["20/a.md"], base * 1.2 + 0.002)

    def test_opened_by_another_session_does_not_count(self):
        # A injeta e não abre; B abre e não injeta: n = 10, O vazio, r = 0
        for i in range(10):
            self.session(["20/a.md"], name=f"a{i}")
            (self.state / f"b{i}.opened").write_text("20/a.md\n", encoding="utf-8")
        self.assertFactor(0.8)
        # 9 de A e 20 de B: n = 9, score base
        shutil.rmtree(self.state)
        self.state.mkdir()
        for i in range(9):
            self.session(["20/a.md"], name=f"a{i}")
        for i in range(20):
            (self.state / f"b{i}.opened").write_text("20/a.md\n", encoding="utf-8")
        self.assertEqual(self.run_rank(), self.run_rank(env={**self.env, "SECOND_BRAIN_RANK_LEARN": "0"}))

    def test_a_note_opened_but_never_injected_keeps_its_base_score(self):
        for i in range(10):
            self.session(["20/d.md"], ["20/d.md", "20/a.md"])
        self.assertEqual(self.scores()["20/a.md"], self.base()["20/a.md"])

    def test_notes_outside_the_manifest_never_show_up_and_notes_without_history_keep_the_base(self):
        self.sessions("99/ghost.md", 12)
        self.assertEqual(self.scores(), self.base())
        self.assertNotIn("ghost", self.run_rank())

    def test_ratio_changes_the_order_of_two_tied_notes(self):
        self.sessions("20/e.md", 10, opened=0)
        self.sessions("20/f.md", 10, opened=10)
        self.assertEqual([r[1] for r in self.base_rows()][1:3], ["20/e.md", "20/f.md"])  # empate: path
        got = [r[1] for r in self.rows()]
        self.assertLess(got.index("20/f.md"), got.index("20/e.md"))

    def base_rows(self):
        return self.rows(env={**self.env, "SECOND_BRAIN_RANK_LEARN": "0"})

    def test_rows_with_score_zero_and_coverage_at_the_limit_follow_the_old_cuts(self):
        self.sessions("20/d.md", 12)
        for env in (self.env, {**self.env, "SECOND_BRAIN_RANK_LEARN": "0"}):
            # só a nota "d" tem "importador": as outras têm score 0 e nunca saem (score > MIN, não >=)
            self.assertEqual([r[1] for r in self.rows("-k", "100", env=env, query="importador")], ["20/d.md"])
            # cobertura exatamente no limite (1,000) passa (coverage >= COV, não >)
            self.assertIn("20/a.md", [r[1] for r in self.rows("-c", "1", env=env)])
            self.assertEqual(self.rows("-c", "1.001", env=env), [])

    def test_the_set_of_rows_does_not_change_with_k_m_and_c(self):
        self.sessions("20/a.md", 12)
        self.sessions("20/d.md", 12, opened=12)
        for flags in (("-k", "100"), ("-k", "100", "-m", "1"), ("-k", "100", "-c", "0.3"), ("-k", "100", "-t", "3")):
            on = [r[1] for r in self.rows(*flags)]
            off = [r[1] for r in self.rows(*flags, env={**self.env, "SECOND_BRAIN_RANK_LEARN": "0"})]
            self.assertEqual(sorted(on), sorted(off), flags)
            self.assertTrue(on)

    def test_min_cut_uses_the_base_score_so_a_printed_score_can_fall_below_min(self):
        self.sessions("20/e.md", 10)
        base = self.base()["20/e.md"]
        cut = f"{base * 0.9:.3f}"
        printed = self.scores("-m", cut)["20/e.md"]
        self.assertAlmostEqual(printed, base * 0.8, delta=0.002)
        self.assertLess(printed, float(cut))
        self.assertEqual(self.base("-m", cut)["20/e.md"], base)

    def test_columns_other_than_the_score_do_not_change(self):
        self.sessions("20/a.md", 10, opened=3)
        on = self.rows("-n")
        off = self.rows("-n", env={**self.env, "SECOND_BRAIN_RANK_LEARN": "0"})
        self.assertTrue(all(len(r) == 6 for r in on))
        self.assertEqual({r[1]: r[2:] for r in on}, {r[1]: r[2:] for r in off})


class KnobsTest(RankLearnBase):
    def test_min_injections_env_opens_the_gate_and_invalid_values_mean_ten(self):
        self.sessions("20/a.md", 7)
        on = {**self.env, "SECOND_BRAIN_RANK_MIN_INJECTIONS": "3"}
        base = self.base()["20/a.md"]
        self.assertAlmostEqual(self.scores(env=on)["20/a.md"], base * 0.8, delta=0.002)
        for bad in ("0", "-1", "abc", "2.5", "", "007", "1e3"):  # invalid means 10, and n = 7 stays below it
            self.assertEqual(self.scores(env={**self.env, "SECOND_BRAIN_RANK_MIN_INJECTIONS": bad}), self.base(), bad)
        self.sessions("20/a.md", 3)
        for bad in ("0", "abc", ""):
            self.assertAlmostEqual(self.scores(env={**self.env, "SECOND_BRAIN_RANK_MIN_INJECTIONS": bad})["20/a.md"],
                                   base * 0.8, delta=0.002, msg=bad)

    def test_learn_switch_values(self):
        self.sessions("20/a.md", 12)
        base = self.base()
        for value in ("0", "false", "no", "off", "OFF", "False", "No"):
            self.assertEqual(self.scores(env={**self.env, "SECOND_BRAIN_RANK_LEARN": value}), base, value)
        for value in (None, "", "1", "yes", "TRUE", "on", "2"):
            env = dict(self.env)
            if value is not None:
                env["SECOND_BRAIN_RANK_LEARN"] = value
            self.assertNotEqual(self.scores(env=env), base, value)

    def test_empty_or_missing_state_and_unknown_dirs_give_the_plain_output(self):
        plain = self.base()
        self.assertEqual(self.scores(), plain)
        for state in (str(self.state / "nope"), "relative/missing"):
            self.assertEqual(self.scores(env={**self.env, "SECOND_BRAIN_STATE_DIR": state}), plain)

    def test_empty_state_dir_variable_reads_the_default_under_home(self):
        home = Path(self.tmp.name) / "home"
        default = home / ".local/state/second-brain"
        default.mkdir(parents=True)
        for i in range(10):
            (default / f"s{i}.injected").write_text("20/a.md\n", encoding="utf-8")
            os.utime(default / f"s{i}.injected", (NOW, NOW))
        base = self.base()["20/a.md"]
        for value in ("", None):
            env = {**self.env, "SECOND_BRAIN_STATE_DIR": ""}
            if value is None:
                del env["SECOND_BRAIN_STATE_DIR"]
            self.assertAlmostEqual(self.scores(env=env)["20/a.md"], base * 0.8, delta=0.002)

    def test_relative_and_odd_state_dir_names_still_apply_the_adjustment(self):
        base = self.base()["20/a.md"]
        cwd = Path(self.tmp.name) / "cwd"
        cwd.mkdir()
        for name in ("st=x", "-st", "sp ace'q\""):
            (cwd / name).mkdir()
            for i in range(10):
                (cwd / name / f"s{i}.injected").write_text("20/a.md\n", encoding="utf-8")
                os.utime(cwd / name / f"s{i}.injected", (NOW, NOW))
            done = subprocess.run(["bash", str(RANK), "--", QUERY], capture_output=True, text=True, cwd=cwd, check=False,
                                  env={**self.env, "SECOND_BRAIN_STATE_DIR": name}, stdin=subprocess.DEVNULL, timeout=20)
            self.assertEqual((done.returncode, done.stderr), (0, ""))
            got = {line.split("\t")[1]: float(line.split("\t")[0]) for line in done.stdout.splitlines()}
            self.assertAlmostEqual(got["20/a.md"], base * 0.8, delta=0.002, msg=name)
            self.assertEqual(sorted(p.name for p in cwd.iterdir() if p.is_file()), [])


class DecayTest(RankLearnBase):
    def test_window_boundary_seven_days_in_seven_days_plus_one_second_out(self):
        edge = 7 + 0.0
        for i in range(10):
            self.session(["20/a.md"], age_days=edge, name=f"in{i}")
        self.assertFactor(0.8)
        shutil.rmtree(self.state)
        self.state.mkdir()
        for i in range(10):
            self.session(["20/a.md"], age_days=edge + 1 / DAY, name=f"out{i}")
        self.assertEqual(self.run_rank(), self.run_rank(env={**self.env, "SECOND_BRAIN_RANK_LEARN": "0"}))

    def test_sessions_outside_the_window_do_not_count_toward_n(self):
        self.sessions("20/a.md", 9)
        self.sessions("20/a.md", 5, age_days=8)
        self.assertEqual(self.scores(), self.base())

    def test_weight_decays_linearly_from_one_to_a_quarter(self):
        # 5 novas fechadas + 5 de 3,5 dias abertas: r = 5 * 0,625 / (5 + 5 * 0,625) = 0,3846
        self.sessions("20/a.md", 5, opened=0)
        self.sessions("20/a.md", 5, opened=5, age_days=3.5)
        self.assertFactor(0.8 + 0.4 * 0.38461538)
        shutil.rmtree(self.state)
        self.state.mkdir()
        self.sessions("20/a.md", 5, opened=5)
        self.sessions("20/a.md", 5, opened=0, age_days=3.5)
        self.assertFactor(0.8 + 0.4 * 0.61538461)

    def test_a_session_at_the_edge_weighs_a_quarter(self):
        self.sessions("20/a.md", 9, opened=0)
        self.sessions("20/a.md", 1, opened=1, age_days=7)
        self.assertFactor(0.8 + 0.4 * (0.25 / 9.25))

    def test_a_future_mtime_counts_as_age_zero(self):
        self.sessions("20/a.md", 10, opened=10, age_days=-3)
        self.assertFactor(1.2)
        shutil.rmtree(self.state)
        self.state.mkdir()
        self.sessions("20/a.md", 5, opened=5, age_days=-3)  # weight 1, not 1,375
        self.sessions("20/a.md", 5, opened=0)
        self.assertFactor(0.8 + 0.4 * 0.5)

    def test_age_comes_from_the_injected_file_not_the_opened_file(self):
        for i in range(5):
            self.session(["20/a.md"], ["20/a.md"], age_days=0, opened_age_days=9)
        for i in range(5):
            self.session(["20/a.md"], age_days=0)
        self.assertFactor(1.0)
        shutil.rmtree(self.state)
        self.state.mkdir()
        for i in range(10):
            self.session(["20/a.md"], ["20/a.md"], age_days=6, opened_age_days=0)
        self.assertFactor(1.2)

    def test_rank_now_fixes_the_clock_and_a_bad_value_falls_back_to_the_real_one(self):
        self.sessions("20/a.md", 10, age_days=1)
        far = {**self.env, "SECOND_BRAIN_RANK_NOW": str(NOW + 30 * DAY)}
        self.assertEqual(self.scores(env=far), self.base())
        # valor inválido: vale o relógio real; as mtimes de 2027 estão no futuro (idade 0), então o ajuste vale
        for bad in ("abc", "", "-5"):
            self.assertAlmostEqual(self.scores(env={**self.env, "SECOND_BRAIN_RANK_NOW": bad})["20/a.md"],
                                   self.base()["20/a.md"] * 0.8, delta=0.002, msg=bad)


class RobustnessTest(RankLearnBase):
    def tree(self):
        out = []
        for path in sorted(self.state.rglob("*")):
            st = path.lstat()
            data = hashlib.sha1(path.read_bytes()).hexdigest() if path.is_file() and not path.is_symlink() else ""
            out.append((str(path.relative_to(self.state)), st.st_mode, st.st_mtime_ns, data))
        return out

    def test_the_ranker_never_writes_to_the_state_dir_and_never_creates_it(self):
        self.sessions("20/a.md", 12, opened=4)
        before = self.tree()
        self.rows()
        self.assertEqual(self.tree(), before)
        gone = Path(self.tmp.name) / "no-such-state"
        self.run_rank(env={**self.env, "SECOND_BRAIN_STATE_DIR": str(gone)})
        self.assertFalse(gone.exists())

    def test_unreadable_binary_nul_huge_line_and_link_files_do_not_break_the_ranker(self):
        for i in range(10):
            self.session(["20/a.md"], name=f"ok{i}")
        base = self.scores()
        (self.state / "bin.injected").write_bytes(b"\xff\xfe\x00\x00 20/a.md \x00\n20/a.md")
        (self.state / "nonl.injected").write_bytes(b"20/a.md")
        (self.state / "big.injected").write_text("x" * 1_000_000, encoding="utf-8")
        (self.state / "link.injected").symlink_to("/etc/passwd")
        (self.state / "dead.injected").symlink_to(self.state / "missing")
        for awk in self.for_each_awk():
            got = self.scores(awk=awk)
            self.assertEqual(set(got), set(base))
            self.assertGreater(got["20/a.md"], 0)
        # só os 10 ok + nonl + bin contam como injeção, com r = 0: o fator é 0,8
        self.assertFactor(0.8)

    def test_unreadable_vanished_dir_fifo_and_socket_candidates_are_skipped_in_every_awk(self):
        for i in range(10):
            self.session(["20/a.md"], ["20/a.md"] if i < 5 else (), name=f"ok{i}")
        want = self.scores()
        for kind in ("injected", "opened"):
            path = self.state / f"zero.{kind}"
            path.write_text("20/a.md\n" * 5, encoding="utf-8")
            os.utime(path, (NOW, NOW))
            path.chmod(0)
        self.addCleanup(lambda: [p.chmod(0o600) for p in self.state.glob("zero.*") if not p.is_symlink()])
        (self.state / "d.injected").mkdir()
        os.mkfifo(self.state / "f.injected")
        os.mkfifo(self.state / "g.opened")
        sock = socket.socket(socket.AF_UNIX)
        self.addCleanup(sock.close)
        sock.bind(str(self.state / "k.opened"))
        for special in ("d.injected", "f.injected", "g.opened", "k.opened"):
            os.utime(self.state / special, (NOW, NOW))  # inside the window: only -type f keeps them out
        old = self.state / "old.injected"
        old.write_text("20/a.md\n", encoding="utf-8")
        os.utime(old, (NOW - 20 * DAY, NOW - 20 * DAY))
        old.chmod(0)
        self.addCleanup(lambda: old.chmod(0o600))
        # um nome que some entre o find e a leitura: shim de find que lista um arquivo inexistente
        real_find = shutil.which("find")
        shim = self.bin / "findshim"
        shim.mkdir()
        script = shim / "find"
        script.write_text(f'#!/bin/bash\n{real_find} "$@"\necho "{NOW} vanished.injected"\necho "{NOW} vanished.opened"\n', encoding="utf-8")
        script.chmod(0o755)
        for awk in self.for_each_awk():
            self.assertEqual(self.scores(awk=awk, timeout=2), want)
            shimmed = {**self.env, "PATH": f"{shim}:{os.environ['PATH']}"}
            self.assertEqual(self.scores(awk=awk, env=shimmed, timeout=2), want)

    def test_only_regular_files_of_the_right_names_at_depth_one_are_candidates(self):
        for i in range(10):
            self.session(["20/a.md"], name=f"ok{i}")
        want = self.scores()
        for name in ("a b.injected", "a.injected.bak", ".injected", "x.injected~", "a.b.injected", "é.injected", "s.seen"):
            (self.state / name).write_text("20/a.md\n" * 3, encoding="utf-8")
        self.assertEqual(self.scores(), want)
        for sub in ("observe", "usage", "patches"):
            (self.state / sub).mkdir()
            for i in range(300):
                for ext in ("injected", "opened"):  # opened too: a recursive find would push the ratio toward 1
                    inner = self.state / sub / f"x{i}.{ext}"
                    inner.write_text("20/a.md\n", encoding="utf-8")
                    os.utime(inner, (NOW, NOW))
        for i in range(300):
            (self.state / f"seen{i}.seen").write_text("20/a.md\n", encoding="utf-8")
        self.assertEqual(self.scores(), want)

    def test_a_newline_in_a_file_name_cannot_forge_a_candidate(self):
        for i in range(10):
            self.session(["20/a.md"], name=f"ok{i}")
        self.session(["20/a.md"], ["20/a.md"], age_days=6.5, name="b")  # b real: weight 0,29, the only opened session
        want = self.scores()
        forged = self.state / f"a\n{NOW - 1} b.injected"  # a second line claiming b was touched a second ago
        forged.write_text("20/a.md\n", encoding="utf-8")
        os.utime(forged, (NOW, NOW))
        self.assertEqual(self.scores(), want)
        self.assertNotAlmostEqual(self.scores()["20/a.md"], self.base()["20/a.md"] * 0.8, delta=0.002)
        forged.unlink()
        self.assertEqual(self.scores(), want)

    def test_cr_lines_are_ignored_and_accented_names_match_by_bytes(self):
        nfc = "20/nota café ç.md"
        nfd = unicodedata.normalize("NFD", nfc)
        self.write_manifest(self.ROWS + [(nfc, "Importar issues no Jira por REST", "jira, rest", "low", "Acento.")])
        for i in range(10):
            self.session([f"{nfc}\r"], name=f"cr{i}")
        self.assertEqual(self.scores(), self.base())  # linha com \r não casa
        shutil.rmtree(self.state)
        self.state.mkdir()
        for i in range(10):
            self.session([nfc], [nfc], name=f"n{i}")
        base = self.base()[nfc]
        self.assertAlmostEqual(self.scores()[nfc], base * 1.2, delta=0.002)
        shutil.rmtree(self.state)
        self.state.mkdir()
        for i in range(10):
            self.session([nfd], [nfd], name=f"d{i}")
        self.assertEqual(self.scores(), self.base())  # NFD contra NFC não casa (limite declarado)

    def test_sentinel_in_query_and_state_lines_never_reaches_the_state_dir(self):
        self.sessions("20/a.md", 10)
        (self.state / "q.injected").write_text("SENTINELA-NAO-GRAVAR\n", encoding="utf-8")
        before = self.tree()
        out = self.run_rank(query="importar issues jira SENTINELA-NAO-GRAVAR $(touch pwned) `id` '\"\\")
        self.assertNotIn("SENTINELA", out)
        self.assertEqual(self.tree(), before)
        self.assertFalse(Path("pwned").exists())

    def test_locale_does_not_change_the_score(self):
        self.sessions("20/a.md", 10, opened=3)
        want = self.scores()
        # locales com vírgula decimal só entram se a máquina os tem (senão o bash avisa em stderr)
        have = subprocess.run(["locale", "-a"], capture_output=True, text=True, check=False).stdout.split()
        langs = ["C", "C.UTF-8"] + [name for name in ("pt_BR.UTF-8", "de_DE.UTF-8", "fr_FR.UTF-8") if name in have]
        for lang in langs:
            env = {**self.env, "LANG": lang, "LC_ALL": lang}
            self.assertEqual(self.scores(env=env), want, lang)

    def test_manifest_dir_with_accent_and_space(self):
        moved = Path(self.tmp.name) / "manifestos é espaço"
        shutil.copytree(self.manifests, moved)
        self.sessions("20/a.md", 10)
        env = {**self.env, "SECOND_BRAIN_MANIFEST_DIR": str(moved)}
        base = self.base(env=env)["20/a.md"]
        self.assertAlmostEqual(self.scores(env=env)["20/a.md"], base * 0.8, delta=0.002)

    def test_the_script_uses_only_shell_tools(self):
        code = "\n".join(line for line in RANK.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#"))
        for banned in ("sb.py", "python", "jq "):
            self.assertNotIn(banned, code)


class CapTest(RankLearnBase):
    def fill(self, count, valid=True):
        for i in range(count):
            path = self.state / f"cap{i}.injected"
            path.write_text("20/a.md\n", encoding="utf-8")
            t = NOW if valid else NOW - 9 * DAY
            os.utime(path, (t, t))

    def test_3000_valid_candidates_keep_the_adjustment_and_3001_switch_it_off(self):
        for awk in self.for_each_awk():
            shutil.rmtree(self.state)
            self.state.mkdir()
            self.fill(3000)
            self.assertFactor(0.8, awk=awk)
            self.fill(3001)
            self.assertEqual(self.scores(awk=awk), self.base(awk=awk))

    def test_opened_files_without_a_valid_session_do_not_count_toward_the_cap(self):
        self.fill(2500)
        for i in range(1000):
            path = self.state / f"orphan{i}.opened"
            path.write_text("20/a.md\n", encoding="utf-8")
            os.utime(path, (NOW, NOW))
        self.assertFactor(0.8)  # 2500 + 1000 would pass 3000 if orphans counted

    def test_files_in_subdirs_do_not_count_toward_the_cap(self):
        self.sessions("20/a.md", 10)
        sub = self.state / "observe"
        sub.mkdir()
        for i in range(3500):
            path = sub / f"deep{i}.injected"
            path.write_text("20/a.md\n", encoding="utf-8")
            os.utime(path, (NOW, NOW))
        self.assertFactor(0.8)

    def test_old_files_do_not_count_toward_the_cap(self):
        self.fill(3500, valid=False)
        for i in range(2000):
            path = self.state / f"new{i}.injected"
            path.write_text("20/a.md\n", encoding="utf-8")
            os.utime(path, (NOW, NOW))
        self.assertFactor(0.8)


class CostTest(RankLearnBase):
    def build_real_size(self, sessions):
        rows = [(f"20/n{i}.md", f"Nota {i} sobre importar issues jira rest {i % 7}", f"jira, tag{i % 11}", "medium",
                 f"Resumo da nota {i} sobre issues e importar.") for i in range(390)]
        self.write_manifest(rows)
        for i in range(sessions):
            names = [f"20/n{(i * 7 + j) % 390}.md" for j in range(8)]
            self.session(names, names[:2], age_days=(i % 70) / 10, name=f"c{i}")

    def timed(self, count, awk, learn="1"):
        env = {**self.env, "SECOND_BRAIN_RANK_LEARN": learn}
        runs = []
        for _ in range(5):
            start = time.perf_counter()
            self.run_rank("-k", "5", "-t", "3", env=env, awk=awk, timeout=10)
            runs.append(time.perf_counter() - start)
        return statistics.median(runs)

    def test_500_sessions_stay_far_below_the_hook_ranker_timeout(self):
        self.build_real_size(500)
        for awk in self.for_each_awk():
            on, off = self.timed(500, awk), self.timed(500, awk, "0")
            self.assertLess(on, 0.45)  # the hook ranker timeout is 0.6 s; the contract E1 (0.30 s) is the Evaluator's own measure
            self.assertLess(on - off, 0.25)

    def test_hook_with_500_sessions_never_times_out(self):
        self.build_real_size(500)
        hook_env = {**self.env, "SECOND_BRAIN_HOOKS": "1", "SECOND_BRAIN_PROMPT_HINT": "active",
                    "SECOND_BRAIN_MIN_COVERAGE": "0.1", "SECOND_BRAIN_MIN_TERMS": "3"}
        proj = Path(self.tmp.name) / "proj"
        proj.mkdir()
        for i in range(10):
            payload = json.dumps({"prompt": "como importar issues no jira por rest com tag", "session_id": f"h{i}", "cwd": str(proj)})
            done = subprocess.run(["bash", str(HINT)], input=payload, capture_output=True, text=True, env=hook_env, check=False, timeout=5)
            self.assertEqual(done.returncode, 0, done.stderr)
        log = [json.loads(line) for line in (self.state / "shadow.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(log), 10)
        self.assertTrue(all(entry["timeout"] is False for entry in log))
        self.assertTrue(all(entry["candidates"] for entry in log))


class HookTest(RankLearnBase):
    def hook(self, session, prompt="como importar issues no jira por rest", extra=None):
        env = {**self.env, "SECOND_BRAIN_HOOKS": "1", "SECOND_BRAIN_PROMPT_HINT": "active", "SECOND_BRAIN_MIN_COVERAGE": "0.3",
               "SECOND_BRAIN_MIN_TERMS": "3", **(extra or {})}
        proj = Path(self.tmp.name) / "proj"
        proj.mkdir(exist_ok=True)
        done = subprocess.run(["bash", str(HINT)], input=json.dumps({"prompt": prompt, "session_id": session, "cwd": str(proj)}),
                              capture_output=True, text=True, env=env, check=False, timeout=10)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout.splitlines()

    def test_the_hint_puts_a_never_opened_note_behind_a_tied_note_with_history(self):
        base = self.hook("fresh1", extra={"SECOND_BRAIN_RANK_LEARN": "0"})
        self.assertEqual([line.split(" — ")[1].split(" ")[0] for line in base[1:3]], ["20/a.md", "20/e.md"])
        self.sessions("20/e.md", 10, opened=0)
        self.sessions("20/f.md", 10, opened=10)
        out = self.hook("fresh2")
        paths = [line.split(" — ")[1].split(" ")[0] for line in out[1:]]
        self.assertLess(paths.index("20/f.md"), paths.index("20/e.md"))
        self.assertEqual(out[0], base[0])
        self.assertTrue(all(line.startswith("- ") and line.endswith("]") for line in out[1:]))

    def test_the_hook_still_writes_seen_and_injected_with_mode_600_and_never_opened(self):
        self.sessions("20/a.md", 10)
        self.hook("sx")
        for ext in ("seen", "injected"):
            self.assertEqual(oct((self.state / f"sx.{ext}").stat().st_mode & 0o777), "0o600")
        self.assertFalse((self.state / "sx.opened").exists())


class GoldenSetAdapterTest(RankLearnBase):
    """run_eval.RankAdapter: learning off by default, on only when the caller exports SECOND_BRAIN_RANK_LEARN=1."""

    def adapter(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("run_eval_for_rank", SCRIPTS.parents[2] / "eval/run_eval.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module  # @dataclass resolves the module by name
        self.addCleanup(sys.modules.pop, spec.name, None)
        spec.loader.exec_module(module)
        return module

    def search(self, module, env):
        keys = ("SECOND_BRAIN_MANIFEST_DIR", "SECOND_BRAIN_STATE_DIR", "SECOND_BRAIN_RANK_NOW", "SECOND_BRAIN_RANK_LEARN")
        saved = {k: os.environ.get(k) for k in keys}
        try:
            for k in keys:
                os.environ.pop(k, None)
            os.environ.update({k: v for k, v in env.items() if k in keys})
            module.RANKER = RANK
            return module.RankAdapter().search(QUERY, 10)
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None)
                if v is not None:
                    os.environ[k] = v

    def test_default_ignores_the_state_and_an_exported_one_applies_it(self):
        module = self.adapter()
        self.sessions("20/e.md", 12, opened=0)
        self.sessions("20/f.md", 12, opened=12)
        clean = {**self.env, "SECOND_BRAIN_STATE_DIR": str(Path(self.tmp.name) / "empty")}
        plain = self.search(module, clean)
        self.assertEqual(self.search(module, self.env), plain)  # state with history, same ranking
        self.assertLess(plain.index("20/e.md"), plain.index("20/f.md"))
        learned = self.search(module, {**self.env, "SECOND_BRAIN_RANK_LEARN": "1"})
        self.assertLess(learned.index("20/f.md"), learned.index("20/e.md"))

    def test_the_adapter_hands_the_ranker_learn_off_unless_the_caller_set_it(self):
        module = self.adapter()
        seen = []

        class Done:
            stdout = ""

        def fake(cmd, **kwargs):
            seen.append(kwargs["env"].get("SECOND_BRAIN_RANK_LEARN"))
            return Done()

        saved = os.environ.pop("SECOND_BRAIN_RANK_LEARN", None)
        try:
            with mock.patch.object(subprocess, "run", fake):
                module.RankAdapter().search("jira importar issues", 3)
                os.environ["SECOND_BRAIN_RANK_LEARN"] = "1"
                module.RankAdapter().search("jira importar issues", 3)
        finally:
            os.environ.pop("SECOND_BRAIN_RANK_LEARN", None)
            if saved is not None:
                os.environ["SECOND_BRAIN_RANK_LEARN"] = saved
        self.assertEqual(seen, ["0", "1"])


if __name__ == "__main__":
    unittest.main()
