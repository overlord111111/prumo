"""CLI do prumo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, checks, dados, diagnostico, docs


def _ler_buffer(caminho: str) -> bytes:
    return Path(caminho).read_bytes()


def _cmd_diagnostico(args: argparse.Namespace) -> int:
    try:
        plano = diagnostico.gerar_plano(args.motor, args.ac, args.modo)
    except (ValueError, dados.DadosInvalidos) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    if args.formato == "json":
        print(json.dumps(plano.como_dict(), ensure_ascii=False, indent=2))
    else:
        print(diagnostico.render_markdown(plano))
    return 0


def _cmd_verificar(args: argparse.Namespace) -> int:
    if args.lista:
        for item in checks.registro():
            print(f"{item['id']:<12} {item['implementacao']:<14} {item['pergunta']}")
        return 0
    kwargs: dict = {}
    if args.padrao:
        kwargs["padrao"] = args.padrao
    if args.buffer_arquivo:
        kwargs["buffer"] = _ler_buffer(args.buffer_arquivo)
    if args.min_fixos:
        kwargs["min_fixos"] = args.min_fixos
    if args.matriz:
        kwargs["matriz"] = [float(v) for v in args.matriz.replace(",", " ").split()]
    if args.ponto:
        kwargs["ponto"] = tuple(float(v) for v in args.ponto.replace(",", " ").split())
    if args.tela:
        largura, altura = args.tela.lower().split("x")
        kwargs["tela"] = (int(largura), int(altura))
    if args.esperado:
        kwargs["esperado"] = tuple(float(v) for v in args.esperado.replace(",", " ").split())
    if args.tolerancia is not None:
        kwargs["tolerancia"] = args.tolerancia
    if args.mapa_arquivo:
        kwargs["mapa"] = json.loads(Path(args.mapa_arquivo).read_text(encoding="utf-8"))
    if args.classe:
        kwargs["classe"] = args.classe
    if args.alvo:
        kwargs["alvo"] = args.alvo
    try:
        resultado = checks.executar(args.check, **kwargs)
    except (ValueError, FileNotFoundError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    if args.formato == "json":
        print(json.dumps(resultado.como_dict(), ensure_ascii=False, indent=2))
    else:
        print(resultado)
    return 0 if resultado.status != checks.FAIL else 1


def _cmd_map(args: argparse.Namespace) -> int:
    try:
        from . import dotnet
    except ImportError:  # pragma: no cover
        print("erro: comando indisponível", file=sys.stderr)
        return 2
    if not dotnet.disponivel():
        print("erro: o comando `map` requer o extra: pip install 'prumo[map]'", file=sys.stderr)
        return 2
    try:
        mapa = dotnet.ler(args.assembly)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    if args.saida_json:
        Path(args.saida_json).write_text(json.dumps(mapa, ensure_ascii=False), encoding="utf-8")
    if args.formato == "json":
        resumo = {
            "assembly": mapa["assembly"],
            "sha256": mapa["sha256"],
            "tamanho_bytes": mapa["tamanho_bytes"],
            "classes_total": mapa["classes_total"],
            "campos_total": mapa["campos_total"],
            "classes": mapa["classes"][: args.limite],
        }
        print(json.dumps(resumo, ensure_ascii=False, indent=2))
        return 0
    texto, total, tokens = dotnet.dossie(mapa, args.alvo, args.orcamento)
    print(texto)
    print(
        f"\n_({total} classes ranqueadas; dossiê cortado em ~{tokens} tokens "
        f"de um orçamento de {args.orcamento})_",
        file=sys.stderr,
    )
    return 0


def _cmd_docs(args: argparse.Namespace) -> int:
    destino = Path(args.destino)
    if args.check:
        problemas = docs.verificar(destino)
        if problemas:
            for problema in problemas:
                print(f"✘ {problema}", file=sys.stderr)
            return 1
        print(f"✔ {len(docs.DOCUMENTOS)} documentos sincronizados com os dados")
        return 0
    escritos = docs.gerar(destino)
    for caminho in escritos:
        print(f"✔ {caminho}")
    return 0


def _cmd_dados(args: argparse.Namespace) -> int:
    resultados = dados.validar_tudo()
    falhas = [r for r in resultados if not r.ok]
    for resultado in resultados:
        marca = "✔" if resultado.ok else "✘"
        print(f"{marca} {resultado.arquivo}")
        for problema in resultado.problemas:
            print(f"   {problema}")
    if falhas:
        return 1
    print(f"\n{len(resultados)} arquivos válidos")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prumo",
        description="Diagnóstico, playbooks e verificação para engenharia reversa de jogos com agentes.",
    )
    parser.add_argument("--version", action="version", version=f"prumo {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)

    diag = sub.add_parser("diagnostico", help="cruza motor + anti-cheat + modo e devolve o plano")
    diag.add_argument("--motor", required=True, choices=list(dados.ids_motores()))
    diag.add_argument("--ac", required=True, choices=list(dados.ids_acs()))
    diag.add_argument("--modo", required=True, choices=list(diagnostico.MODOS))
    diag.add_argument("--formato", choices=["md", "json"], default="md")
    diag.set_defaults(func=_cmd_diagnostico)

    ver = sub.add_parser("verificar", help="executa um dos 7 checks")
    ver.add_argument("--check", choices=[c["id"] for c in dados.checks()])
    ver.add_argument("--lista", action="store_true", help="lista os checks disponíveis")
    ver.add_argument("--padrao", help="assinatura AOB, ex: '48 8B 05 ?? ?? 66'")
    ver.add_argument("--buffer-arquivo", dest="buffer_arquivo", help="arquivo para varrer")
    ver.add_argument("--min-fixos", dest="min_fixos", type=int, default=8)
    ver.add_argument("--matriz", help="16 floats da matriz view-projection")
    ver.add_argument("--ponto", help="x,y,z do ponto de mundo")
    ver.add_argument("--tela", help="largura x altura, ex: 1920x1080")
    ver.add_argument("--esperado", help="pixel esperado x,y")
    ver.add_argument("--tolerancia", type=float)
    ver.add_argument("--mapa-arquivo", dest="mapa_arquivo", help="JSON gerado por `prumo map --saida-json`")
    ver.add_argument("--classe")
    ver.add_argument("--alvo")
    ver.add_argument("--formato", choices=["md", "json"], default="md")
    ver.set_defaults(func=_cmd_verificar)

    mapa = sub.add_parser("map", help="gera o dossiê de tipos de um assembly .NET")
    mapa.add_argument("assembly")
    mapa.add_argument("--alvo", default="health", help="termo procurado (ex: health, position, ammo)")
    mapa.add_argument("--orcamento", type=int, default=3000, help="orçamento estimado em tokens")
    mapa.add_argument("--formato", choices=["md", "json"], default="md")
    mapa.add_argument("--saida-json", dest="saida_json", help="salva o mapa completo em JSON")
    mapa.add_argument("--limite", type=int, default=20, help="classes no JSON resumido")
    mapa.set_defaults(func=_cmd_map)

    doc = sub.add_parser("docs", help="gera (ou confere) a documentação derivada dos dados")
    doc.add_argument("--destino", default="docs")
    doc.add_argument("--check", action="store_true")
    doc.set_defaults(func=_cmd_docs)

    dad = sub.add_parser("dados", help="valida os dados versionados")
    dad.set_defaults(func=_cmd_dados)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.comando == "verificar" and not args.check and not args.lista:
        parser.error("use --check <id> ou --lista")
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
