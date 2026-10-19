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
    if args.posicoes:
        pontos = []
        for item in args.posicoes.split(";"):
            valores = [float(v) for v in item.replace(",", " ").split()]
            if len(valores) != 3:
                print(f"erro: posição inválida {item!r} (esperado x,y,z)", file=sys.stderr)
                return 2
            pontos.append(tuple(valores))
        kwargs["posicoes"] = pontos
    if args.antes is not None:
        kwargs["antes"] = args.antes
    if args.depois is not None:
        kwargs["depois"] = args.depois
    if args.amostras:
        kwargs["amostras"] = args.amostras
    if args.intervalo:
        kwargs["intervalo"] = args.intervalo
    if args.modulo:
        kwargs["modulo"] = args.modulo
    if args.minimo:
        kwargs["minimo"] = args.minimo
    adaptador = None
    if args.pid:
        try:
            adaptador = _abrir_adaptador(args.pid)
        except Exception as exc:  # adaptador indisponível: check devolve INDETERMINADO com o motivo
            print(
                f"aviso: adaptador indisponível ({exc}); o check vai devolver INDETERMINADO",
                file=sys.stderr,
            )
    try:
        if adaptador is not None:
            kwargs["adaptador"] = adaptador
            if args.endereco:
                kwargs["endereco"] = int(args.endereco, 0)
            kwargs["tipo"] = args.tipo
        resultado = checks.executar(args.check, **kwargs)
    except (ValueError, FileNotFoundError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    finally:
        if adaptador is not None and hasattr(adaptador, "fechar"):
            adaptador.fechar()
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
        print(
            "erro: o comando `map` requer o extra dnfile. Instale com:\n"
            "  pipx inject prumo dnfile\n"
            "  pip install 'prumo[map] @ git+https://github.com/overlord111111/prumo'",
            file=sys.stderr,
        )
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



def _abrir_adaptador(pid: int, escrita: bool = False):
    from .adapters import abrir

    adaptador = abrir(pid)
    if escrita:
        if not hasattr(adaptador, "habilitar_escrita"):
            raise TypeError("este adaptador não permite escrita")
        adaptador.habilitar_escrita()
    return adaptador


def _cmd_processo(args: argparse.Namespace) -> int:
    from .adapters import AdaptadorIndisponivel, FalhaDeLeitura

    try:
        with _abrir_adaptador(args.pid) as adaptador:
            info = adaptador.processo()
            modulos = adaptador.modulos()
            resultado = checks.check_processo(adaptador, args.modulo)
    except (AdaptadorIndisponivel, FalhaDeLeitura) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    if args.formato == "json":
        print(
            json.dumps(
                {"processo": info, "modulos": [m.__dict__ for m in modulos], "check": resultado.como_dict()},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    print(f"processo  {info['pid']}  {info['arquitetura']}  {info['executavel']}")
    print(f"modulos   {len(modulos)}")
    for modulo in modulos[: args.limite]:
        print(f"  0x{modulo.base:012X}  {modulo.tamanho:>10}  {modulo.nome_modulo}")
    print()
    print(resultado)
    return 0 if resultado.status != checks.FAIL else 1


def _cmd_ler(args: argparse.Namespace) -> int:
    from .adapters import AdaptadorIndisponivel, FalhaDeLeitura

    try:
        with _abrir_adaptador(args.pid) as adaptador:
            valor = checks.ler_valor(adaptador, int(args.endereco, 0), args.tipo)
    except (AdaptadorIndisponivel, FalhaDeLeitura, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    if args.formato == "json":
        print(json.dumps({"endereco": int(args.endereco, 0), "tipo": args.tipo, "valor": valor}))
    else:
        print(f"{args.tipo} @ {args.endereco} = {valor}")
    return 0


def _cmd_escrever(args: argparse.Namespace) -> int:
    from .adapters import AdaptadorIndisponivel, FalhaDeLeitura

    if not args.confirmar:
        print(
            "erro: escrita exige --confirmar. É a única operação do prumo que altera o alvo.",
            file=sys.stderr,
        )
        return 2
    try:
        with _abrir_adaptador(args.pid, escrita=True) as adaptador:
            escritos = checks.escrever_valor(adaptador, int(args.endereco, 0), args.tipo, args.valor)
    except (AdaptadorIndisponivel, FalhaDeLeitura, PermissionError, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    print(f"{escritos} byte(s) escritos em {args.endereco}")
    return 0


def _cmd_varrer(args: argparse.Namespace) -> int:
    from .adapters import AdaptadorIndisponivel, FalhaDeLeitura

    try:
        padrao = checks.parse_padrao(args.padrao)
        with _abrir_adaptador(args.pid) as adaptador:
            achados = adaptador.varrer(padrao, args.limite_mb * 1024 * 1024)
    except (AdaptadorIndisponivel, FalhaDeLeitura, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    cabecalho = f"{len(achados)} hit(s) para {args.padrao!r}"
    if args.formato == "json":
        print(
            json.dumps(
                {"padrao": args.padrao, "hits": [hex(a) for a in achados[: args.max]], "total": len(achados)}
            )
        )
        return 0
    print(cabecalho)
    for endereco in achados[: args.max]:
        print(f"  0x{endereco:012X}")
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
    ver.add_argument("--pid", type=int, help="abre o adaptador local no processo indicado")
    ver.add_argument("--modulo", help="módulo que precisa estar carregado (check processo)")
    ver.add_argument("--endereco", help="endereço em hexadecimal ou decimal (check campo)")
    ver.add_argument("--tipo", default="int32", choices=sorted(checks.TIPOS))
    ver.add_argument("--amostras", type=int, default=5)
    ver.add_argument("--intervalo", type=float, default=0.15)
    ver.add_argument("--antes", type=float)
    ver.add_argument("--depois", type=float)
    ver.add_argument("--posicoes", help="x,y,z;x,y,z;... (check entidades)")
    ver.add_argument("--minimo", type=int, default=2)
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

    proc = sub.add_parser("processo", help="abre o adaptador, lista módulos e roda o check de processo")
    proc.add_argument("--pid", type=int, required=True)
    proc.add_argument("--modulo", help="exige que este módulo esteja carregado")
    proc.add_argument("--limite", type=int, default=10)
    proc.add_argument("--formato", choices=["md", "json"], default="md")
    proc.set_defaults(func=_cmd_processo)

    ler = sub.add_parser("ler", help="lê um valor tipado do processo")
    ler.add_argument("--pid", type=int, required=True)
    ler.add_argument("--endereco", required=True)
    ler.add_argument("--tipo", default="int32", choices=sorted(checks.TIPOS))
    ler.add_argument("--formato", choices=["md", "json"], default="md")
    ler.set_defaults(func=_cmd_ler)

    esc = sub.add_parser("escrever", help="escreve um valor (exige --confirmar)")
    esc.add_argument("--pid", type=int, required=True)
    esc.add_argument("--endereco", required=True)
    esc.add_argument("--tipo", default="int32", choices=sorted(checks.TIPOS))
    esc.add_argument("--valor", type=float, required=True)
    esc.add_argument("--confirmar", action="store_true")
    esc.set_defaults(func=_cmd_escrever)

    var = sub.add_parser("varrer", help="varre a memória do processo atrás de uma assinatura")
    var.add_argument("--pid", type=int, required=True)
    var.add_argument("--padrao", required=True)
    var.add_argument("--max", type=int, default=20)
    var.add_argument("--limite-mb", dest="limite_mb", type=int, default=64)
    var.add_argument("--formato", choices=["md", "json"], default="md")
    var.set_defaults(func=_cmd_varrer)

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
