import unittest
from unittest.mock import patch, mock_open
from tempfile import TemporaryDirectory
from pathlib import Path
from projects import load_manifest, load_registry, validate, MissingDependency, Issue, ERROR, WARN


def make_vault(tmp_dir):
    vault = Path(tmp_dir)
    m_dir = vault / "00_META/projects"
    m_dir.mkdir(parents=True, exist_ok=True)
    (m_dir / "manifest.yaml").write_text("""
version: 1
limits:
  quota_min_free_pct: 30
  max_implementers: 2
secretario:
  traycer_task: ""
web:
  port: 8765
projects:
  - slug: outlet_promo
    note: 40_Projects/outlet_promo.md
    repo: git@github.com:FlavianMF/outlet_promo.git
    checkout: ~/projetos_apps/outlet_promo
    branch: master
    setup: ["flutter pub get"]
    test: "make test"
    harness: claude
    model: sonnet
    effort: high
    env: [SUPABASE_URL]
""", encoding="utf-8")
    p_dir = vault / "40_Projects"
    p_dir.mkdir(parents=True, exist_ok=True)
    (p_dir / "outlet_promo.md").write_text("""---
title: Outlet Promo
type: project
tags: [app]
created: 2026-10-01
status: active
prioridade: P1
fase: spec
proximo_passo: Proximo passo
bloqueio: Nenhum
---

Descricao do projeto.
""", encoding="utf-8")
    d_dir = vault / "00_META"
    d_dir.mkdir(parents=True, exist_ok=True)
    (d_dir / "jev-denylist.md").write_text("""---
title: Denylist
---
- term: secreto_termo
- repo: bloqueado_repo
""", encoding="utf-8")
    return vault


class TestProjects(unittest.TestCase):
    def test_load_manifest_success(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            manifest = load_manifest(Path(vault))
            self.assertEqual(manifest.version, 1)
            self.assertEqual(manifest.limits["quota_min_free_pct"], 30)
            self.assertEqual(len(manifest.projects), 1)
            self.assertEqual(manifest.projects[0]["slug"], "outlet_promo")

    def test_load_manifest_missing_dependency(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            with patch('sys.modules', {'yaml': None}):
                with self.assertRaises(MissingDependency):
                    load_manifest(Path(vault))

    def test_load_registry(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            projects = load_registry(Path(vault))
            p = projects[0]
            self.assertEqual(p.slug, "outlet_promo")
            self.assertEqual(p.prioridade, "P1")
            self.assertEqual(p.status, "active")

    def test_validate_clean_vault(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            issues = validate(Path(vault))
            self.assertEqual(len(issues), 0)

    def test_validate_secret_in_manifest(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "00_META/projects/manifest.yaml").write_text("""
version: 1
limits:
  quota_min_free_pct: 30
  max_implementers: 2
secretario:
  traycer_task: ""
web:
  port: 8765
projects:
  - slug: outlet_promo
    note: 40_Projects/outlet_promo.md
    repo: git@github.com:FlavianMF/outlet_promo.git
    checkout: ~/projetos_apps/outlet_promo
    branch: master
    setup: ["flutter pub get"]
    test: "make test"
    harness: claude
    model: sonnet
    effort: high
    env: [SUPABASE_URL]
    secret: ghp_1234567890abcdef1234567890abcdef
""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "secret" and i.severity == "error" for i in issues))
            self.assertNotIn("ghp_1234567890abcdef1234567890abcdef", str(issues))

    def test_validate_secret_in_note(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "40_Projects/outlet_promo.md").write_text("""---
title: Outlet Promo
type: project
tags: [app]
created: 2026-10-01
status: active
prioridade: P1
fase: spec
proximo_passo: Proximo passo
bloqueio: Nenhum
---

Descricao do projeto.
secret: ghp_1234567890abcdef1234567890abcdef
""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "secret" for i in issues))
            self.assertNotIn("ghp_1234567890abcdef1234567890abcdef", str(issues))

    def test_validate_invalid_manifest_key(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "00_META/projects/manifest.yaml").write_text("""
version: 1
limits:
  quota_min_free_pct: 30
  max_implementers: 2
secretario:
  traycer_task: ""
web:
  port: 8765
projects:
  - slug: outlet_promo
    note: 40_Projects/outlet_promo.md
    repo: git@github.com:FlavianMF/outlet_promo.git
    checkout: ~/projetos_apps/outlet_promo
    branch: master
    setup: ["flutter pub get"]
    test: "make test"
    harness: claude
    model: sonnet
    effort: high
    env: [SUPABASE_URL]
    unknown_prop: 123
""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "manifest" and i.severity == "error" for i in issues))

    def test_validate_invalid_env_name(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "00_META/projects/manifest.yaml").write_text("""
version: 1
limits:
  quota_min_free_pct: 30
  max_implementers: 2
secretario:
  traycer_task: ""
web:
  port: 8765
projects:
  - slug: outlet_promo
    note: 40_Projects/outlet_promo.md
    repo: git@github.com:FlavianMF/outlet_promo.git
    checkout: ~/projetos_apps/outlet_promo
    branch: master
    setup: ["flutter pub get"]
    test: "make test"
    harness: claude
    model: sonnet
    effort: high
    env: [invalid-env-123]
""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "env" and i.severity == "error" for i in issues))

    def test_validate_pii_email(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "40_Projects/outlet_promo.md").write_text("""---
title: Outlet Promo
type: project
tags: [app]
created: 2026-10-01
status: active
prioridade: P1
fase: spec
proximo_passo: user@test.com
bloqueio: Nenhum
---

Descricao do projeto.
""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "pii" and i.severity == "error" for i in issues))
            self.assertNotIn("user@test.com", str(issues))

    def test_validate_pii_phone_cpf_cnpj(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "40_Projects/outlet_promo.md").write_text("""---
title: Outlet Promo
type: project
tags: [app]
created: 2026-10-01
status: active
prioridade: P1
fase: spec
proximo_passo: +55 11 98765-4321
bloqueio: Nenhum
---

Descricao do projeto.
""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "pii" for i in issues))
            self.assertNotIn("+55 11 98765-4321", str(issues))

    def test_validate_denylist_term(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "00_META/projects/manifest.yaml").write_text("""
version: 1
limits:
  quota_min_free_pct: 30
  max_implementers: 2
secretario:
  traycer_task: ""
web:
  port: 8765
projects:
  - slug: outlet_promo
    note: 40_Projects/outlet_promo.md
    repo: git@github.com:FlavianMF/outlet_promo.git
    checkout: ~/projetos_apps/outlet_promo
    branch: master
    setup: ["flutter pub get"]
    test: "make test"
    harness: claude
    model: sonnet
    effort: high
    env: [SUPABASE_URL]
""", encoding="utf-8")
            (Path(vault) / "40_Projects/outlet_promo.md").write_text("""---
title: Outlet Promo
type: project
tags: [app]
created: 2026-10-01
status: active
prioridade: P1
fase: spec
proximo_passo: secreto_termo
bloqueio: Nenhum
---

Descricao do projeto.
""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "denylist" and i.severity == "error" for i in issues))

    def test_validate_denylist_missing_is_warn(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "00_META/jev-denylist.md").unlink()
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "denylist" and i.severity == "warn" for i in issues))

    def test_validate_inactive_status_is_warn(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "40_Projects/outlet_promo.md").write_text("""---
title: Outlet Promo
type: project
tags: [app]
created: 2026-10-01
status: superseded
prioridade: P1
fase: spec
proximo_passo: Proximo passo
bloqueio: Nenhum
---

Descricao do projeto.
""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "status" and i.severity == "warn" for i in issues))

    def test_validate_text_length_and_newline(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "40_Projects/outlet_promo.md").write_text("""---
title: Outlet Promo
type: project
tags: [app]
created: 2026-10-01
status: active
prioridade: P1
fase: spec
proximo_passo: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
bloqueio: Nenhum
---

Descricao do projeto.
""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "frontmatter" and i.severity == "error" for i in issues))

    def test_validate_invalid_priority(self):
        with TemporaryDirectory() as tmp_dir:
            vault = make_vault(tmp_dir)
            (Path(vault) / "00_META/projects/manifest.yaml").write_text("""
version: 1
limits:
  quota_min_free_pct: 30
  max_implementers: 2
secretario:
  traycer_task: ""
web:
  port: 8765
projects:
  - slug: outlet_promo
    note: 40_Projects/outlet_promo.md
    repo: git@github.com:FlavianMF/outlet_promo.git
    checkout: ~/projetos_apps/outlet_promo
    branch: master
    setup: ["flutter pub get"]
    test: "make test"
    harness: claude
    model: sonnet
    effort: high
    env: [SUPABASE_URL]
""", encoding="utf-8")
            (Path(vault) / "40_Projects/outlet_promo.md").write_text("""---\ntitle: Outlet Promo\ntype: project\ntags: [app]\ncreated: 2026-10-01\nstatus: active\nprioridade: P9\nfase: spec\nproximo_passo: Proximo passo\nbloqueio: Nenhum\n---\n\nDescricao do projeto.\n""", encoding="utf-8")
            issues = validate(Path(vault))
            self.assertTrue(any(i.check == "frontmatter" and i.severity == "error" for i in issues))

if __name__ == '__main__':
    unittest.main()
