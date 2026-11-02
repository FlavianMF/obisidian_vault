from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

import projects
import projects_state


@dataclass
class Command:
    action: str
    slug: Optional[str] = None
    id: Optional[str] = None
    decision: Optional[str] = None
    priority: Optional[str] = None


@dataclass
class ParseError:
    message: str


@dataclass
class Result:
    ok: bool
    message: str


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def parse(
    texto: str,
    valid_slugs: Optional[Iterable[str]] = None,
    vault: Optional[Path] = None,
) -> Command | ParseError:
    if not texto or not texto.strip():
        return ParseError("Comando vazio.")

    if valid_slugs is None and vault is not None:
        try:
            reg = projects.load_registry(vault)
            valid_slugs = [p.slug for p in reg]
        except Exception:
            valid_slugs = None

    valid_slugs_set = set(valid_slugs) if valid_slugs is not None else None

    def _check_slug(s: str) -> Optional[ParseError]:
        if valid_slugs_set is not None and s not in valid_slugs_set:
            sl = ", ".join(sorted(valid_slugs_set))
            return ParseError(f"Slug desconhecido: '{s}'. Slugs válidos: {sl}")
        return None

    norm = _normalize(texto)
    tokens = norm.split()
    if not tokens:
        return ParseError("Comando vazio.")

    verb = tokens[0]

    if verb == "status":
        if len(tokens) == 1:
            return Command(action="status")
        if len(tokens) == 2:
            slug = tokens[1]
            err = _check_slug(slug)
            if err:
                return err
            return Command(action="status_project", slug=slug)
        return ParseError("Uso do comando status: 'status' ou 'status <slug>'")

    if verb in ("aprovar", "rejeitar"):
        if len(tokens) != 2:
            return ParseError(f"Uso: '{verb} <id>'")
        s_id = tokens[1]
        decision = "approve" if verb == "aprovar" else "reject"
        return Command(action="suggest_decide", id=s_id, decision=decision)

    if verb in ("pausar", "retomar"):
        if len(tokens) != 2:
            return ParseError(f"Uso: '{verb} <slug>'")
        slug = tokens[1]
        err = _check_slug(slug)
        if err:
            return err
        action = "pause" if verb == "pausar" else "resume"
        return Command(action=action, slug=slug)

    if verb == "priorizar":
        if len(tokens) != 3:
            return ParseError("Uso: 'priorizar <slug> P1|P2|P3'")
        slug = tokens[1]
        err = _check_slug(slug)
        if err:
            return err
        pri = tokens[2].upper()
        if pri not in ("P1", "P2", "P3"):
            return ParseError(f"Prioridade inválida: '{tokens[2]}'. Use P1, P2 ou P3.")
        return Command(action="prioritize", slug=slug, priority=pri)

    return ParseError(
        f"Comando não reconhecido: '{texto}'. "
        "Comandos válidos: status, status <slug>, pausar <slug>, retomar <slug>, priorizar <slug> P1|P2|P3, aprovar <id>, rejeitar <id>."
    )


def _cap(msg: str, limit: int = 300) -> str:
    if len(msg) <= limit:
        return msg
    return msg[: limit - 3] + "..."


def execute(cmd: Command, vault: Path, state_dir: Path) -> Result:
    try:
        reg = projects.load_registry(vault)
    except Exception as exc:
        return Result(ok=False, message=_cap(f"Erro ao carregar registro: {exc}"))

    slug_map = {p.slug: p for p in reg}

    if cmd.slug and cmd.slug not in slug_map and cmd.action not in ("status"):
        sl = ", ".join(sorted(slug_map.keys()))
        return Result(ok=False, message=_cap(f"Slug desconhecido: '{cmd.slug}'. Slugs válidos: {sl}"))

    if cmd.action == "status":
        if not reg:
            return Result(ok=True, message="Nenhum projeto registrado.")
        items = []
        for p in reg:
            paused = " (pausado)" if projects_state.is_paused(state_dir, p.slug) else ""
            items.append(f"{p.slug} [{p.prioridade}{paused}]: {p.fase or p.status}")
        msg = f"Projetos ({len(reg)}): " + "; ".join(items)
        return Result(ok=True, message=_cap(msg))

    if cmd.action == "status_project":
        p = slug_map.get(cmd.slug) # type: ignore
        if not p:
            sl = ", ".join(sorted(slug_map.keys()))
            return Result(ok=False, message=_cap(f"Slug desconhecido: '{cmd.slug}'. Slugs válidos: {sl}"))
        is_p = projects_state.is_paused(state_dir, p.slug)
        sit = "pausado" if is_p else p.status
        msg = (
            f"{p.slug} [{p.prioridade}] {sit}: fase '{p.fase}', "
            f"próximo '{p.proximo_passo}', bloqueio '{p.bloqueio or 'nenhum'}'"
        )
        return Result(ok=True, message=_cap(msg))

    if cmd.action == "suggest_decide":
        rc = projects_state.suggest_decide(state_dir, cmd.id, cmd.decision) # type: ignore
        if rc != 0:
            return Result(ok=False, message=_cap(f"Sugestão {cmd.id} não encontrada."))
        action_pt = "aprovada" if cmd.decision == "approve" else "rejeitada"
        return Result(ok=True, message=_cap(f"Sugestão {cmd.id} {action_pt} com sucesso."))

    if cmd.action == "pause":
        projects_state.pause(state_dir, cmd.slug) # type: ignore
        return Result(ok=True, message=_cap(f"Projeto {cmd.slug} pausado com sucesso."))

    if cmd.action == "resume":
        projects_state.resume(state_dir, cmd.slug) # type: ignore
        return Result(ok=True, message=_cap(f"Projeto {cmd.slug} retomado com sucesso."))

    if cmd.action == "prioritize":
        rc = projects.cli_update(vault, cmd.slug, prioridade=cmd.priority) # type: ignore
        if rc != 0:
            return Result(ok=False, message=_cap(f"Falha ao atualizar prioridade de {cmd.slug}."))
        return Result(ok=True, message=_cap(f"Prioridade de {cmd.slug} atualizada para {cmd.priority}."))

    return Result(ok=False, message=_cap(f"Ação desconhecida: {cmd.action}"))
